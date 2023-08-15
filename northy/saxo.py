import jwt
import requests
import random, string
import time, uuid, json
from .utils import Utils
from datetime import datetime
from collections import namedtuple
from saxo_openapi import API
from requests.auth import HTTPBasicAuth
from jwt.exceptions import ExpiredSignatureError
import saxo_openapi.endpoints.trading as tr
import logging

utils = Utils()

# create random context that contain letters (a-z) and numbers (0-9) as well as - (dash) and _ (underscore). It is case insensitive. Max length is 50 characters.
ContextId = ''.join(random.choice(string.ascii_letters + string.digits + '-_') for i in range(50))
ReferenceId = ''.join(random.choice(string.ascii_letters + string.digits + '-_') for i in range(50))

"""
TraderConfig = {
    "SAXO_DEMO": {
        # Saxo Demo Account
        'AccountId': '17470793',
        'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==',
        'ContextId': ContextId,
        "ReferenceId": ReferenceId,


        # Set preferred order type
        # Market, will be executed immediately
        # Limit, will be executed when price is reached (you might risk missing the trade)
        'OrderType': 'Market',
    }
}
"""

class SaxoConfig:
    def __init__(self, config_file="saxo_config.json"):
        # Create a logger instance for the class
        self.logger = logging.getLogger(__name__)

        self.load_config(filename=config_file)

    def load_config(self, filename):
        """ Read config from file """
        with open(filename, "r") as file:
            config = json.load(file)
        self.config = config
    
    def get_stoploss(self, symbol):
        """
            Lookup default stoploss points for a symbol.
        """
        symbol = symbol.upper()
        try:
            stoploss_points = self.config["tickers"][symbol]["stoploss_points"]
            return stoploss_points
        except Exception as e:
            # Setting arbitrary SL for unknown symbols
            self.logger.warning(f"Unknown symbol '{symbol}'. Setting SL to 9.")
            return 9

class Saxo:
    def __init__(self, config_file="saxo_config.json", profile_name="default"):
        # Create a logger instance for the class
        self.logger = logging.getLogger(__name__)

        # Set trade account config
        self.config = SaxoConfig().config
        self.set_profile(profile_name)
        self.tickers = self.config["tickers"]

        # Misc vars
        self.session_filename = ".saxo-session"
        self.base_url = self.environment["OpenApiBaseUrl"]
        self.state = str(uuid.uuid4())

        # Setup Saxo API connection
        self.s = requests.session()
        self.token = self.__get_bearer()
        self.client = API(access_token=self.token)

    def load_config(self, filename):
        """ Read config from file """
        with open(filename, "r") as file:
            config = json.load(file)
        self.config = config

    def set_profile(self, profile_name):
        """ Set profile """
        self.profile_name = profile_name
        self.profile = self.config["profiles"][self.profile_name]
        self.environment_name = self.profile["environment"]
        self.environment = self.config["environments"][self.environment_name]
        self.username = self.profile["username"]
        self.password = self.profile["password"]

        self.logger.info(f"Using profile: {self.profile_name} ({self.environment_name})")

    ### Helper functions ###
    def pretty_print_position(self, position):
        """ Pretty print position """
        p = position
        pos_id = p["PositionId"]
        entry_date = p["PositionBase"]["ExecutionTimeOpen"]

        # convert entry_date to datetime object
        entry_date = datetime.strptime(entry_date, "%Y-%m-%dT%H:%M:%S.%fZ")
        # remove seconds from entry_date
        entry_date = entry_date.replace(second=0, microsecond=0)

        uic = p["PositionBase"]["Uic"]
        symbol = self.uic_lookup(uic=uic)
        entry = p["PositionBase"]["OpenPrice"]
        profit = p["PositionView"]["ProfitLossOnTrade"]
        profit_adj = p["PositionView"]["ProfitLossOnTradeAdjusted"]
        amount = p["PositionBase"]["Amount"] * -1
        print("ID\t\tDATE\t\t\tSYMBOL\tAMOUNT\tENTRY\t\tProfit\tprofit_adj")
        print("{pos_id}\t{entry_date}\t{symbol}\t{amount}\t{entry}\t\t{profit}\t{profit_adj}".format(pos_id=pos_id, symbol=symbol, entry=entry, profit=profit, amount=amount, entry_date=entry_date, profit_adj=profit_adj))

    def signal_to_tuple(self, signal):
        """ 
            Convert signal into a namedtuple

            Example signal:
                SPX_TRADE_SHORT_IN_4162_SL_10
                NDX_FLATSTOP
        """
        s = signal.split("_")
        __action = s[1]

        if __action == "TRADE":
            # NDX_TRADE_SHORT_IN_13199_SL_25
            _entry, _sl = float(s[4]), float(s[6])
            return namedtuple("signal", ["symbol", "action", "direction", "entry", "stoploss", "raw"])(s[0], s[1], s[2], _entry, _sl, signal)
        
        if __action == "SCALEOUT":
            # SPX_SCALEOUT_IN_3809_OUT_4153_POINTS_344
            return namedtuple("signal", ["symbol", "action", "entry", "exit", "points", "raw"])(s[0], s[1], s[3], s[5], s[7], signal)

        if __action == "FLAT":
            # SPX_FLAT
            return namedtuple("signal", ["symbol", "action", "raw"])(s[0], s[1], signal)

        if __action == "FLATSTOP":
            # SPX_FLATSTOP
            return namedtuple("signal", ["symbol", "action", "raw"])(s[0], s[1], signal)
                
        if __action == "CLOSED":
            # NDX_CLOSED
            return namedtuple("signal", ["symbol", "action", "raw"])(s[0], s[1], signal)
        
        if __action == "LIMIT":
            # SPX_LIMIT_LONG_IN_3749_OUT_3739_SL_10
            _entry, _exit, _sl = float(s[4]), float(s[6]), float(s[8])
            return namedtuple("signal", ["symbol", "action", "direction", "entry", "exit", "stoploss", "raw"])(s[0], s[1], s[2], _entry, _exit, _sl, signal)

    def uic_lookup(self, symbol=None, uic=None):
            """
                Lookup Uic and AssetType for a given symbol
            """
            TABLE = self.config["tickers"]

            if symbol is not None:
                symbol = symbol.upper()
                try:
                    res = TABLE[symbol]
                    self.logger.info(f"{symbol} --> {res}")
                    return res
                except KeyError:
                    return None
            
            if uic is not None:
                uic = int(uic)
                for symbol, v in TABLE.items():
                    if v["Uic"] == uic:
                        print(f"{uic} --> {symbol}")
                        return symbol
                return None

    ### Auth ###
    def __auth_request(self):
        # Vars
        auth_endpoint = self.environment["AuthorizationEndpoint"]
        client_id = self.environment["AppKey"]
        redirect_uri = self.environment["RedirectUrls"][1]

        url = f"{auth_endpoint}?response_type=code&client_id={client_id}&state={self.state}&redirect_uri={redirect_uri}"
        self.logger.debug(f"GET {url}")
        r = self.s.get(url, allow_redirects=False)
        #logger(r.content)
        redirect_url = r.headers["Location"]
        return redirect_url

    def __manual_auth(self, redirect_url):
        """ Authenticate "manually" using user/pass """
        def __parse_url(url):
            """ Parse URL and return query string as dict """
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(url)
            return parse_qs(parsed_url.query)

        # Login
        data = {"field_userid": self.username, "field_password": self.password}
        self.logger.info(f"POST {redirect_url}")
        r = self.s.post(redirect_url, data=data, allow_redirects=False)
        post_login_url = r.headers["Location"]

        # Post login, fetch auth code
        self.logger.info(f"GET {post_login_url}")
        r = self.s.get(post_login_url, allow_redirects=False)
        auth_code_url = r.headers["Location"]
        auth_code = __parse_url(auth_code_url)["code"][0]
        self.logger.debug(f"Auth Code: {auth_code}")
        return auth_code

    def __access_token(self, auth_code, grant_type):
        # Vars
        redirect_uri = self.environment["RedirectUrls"][1]
        token_endpoint = self.environment["TokenEndpoint"]
        app_key = self.environment["AppKey"]
        app_secret = self.environment["AppSecret"]
        basic = HTTPBasicAuth(app_key, app_secret)

        data = { "redirect_uri": redirect_uri, "grant_type": grant_type}

        if grant_type == "authorization_code":
            data["code"] = auth_code
        elif grant_type == "refresh_token":
            data["refresh_token"] = auth_code
        
        self.logger.info(f"POST {token_endpoint}")

        r = self.s.post(token_endpoint, auth=basic, data=data)
        if r.status_code == 401:
            self.logger.warning("401 Unauthorized")
            return None
        else:
            __jwt = r.json()
            # mask middle of token
            _access_token_masked = __jwt["access_token"][:10] + "..." + __jwt["access_token"][-10:]
            _masked_refresh_token = __jwt["refresh_token"][:5] + "..." + __jwt["refresh_token"][-5:]

            self.logger.debug("Access Token: " + _access_token_masked + " Refresh Token: " + _masked_refresh_token)

            # Write access token to file
            utils.write_json(data=__jwt, filename=self.session_filename)

            # Set token
            self.token = __jwt["access_token"]
            
            return __jwt

    def __get_bearer(self):
        """ Get bearer token from .saxo-session file """
        __jwt = utils.read_json(filename=self.session_filename)
        if __jwt is None:
            self.logger.warning("No .saxo-session file found, authenticating..")
            __jwt = self.__authenticate()

        if "access_token" not in __jwt:
            self.logger.warning("No access_token in .saxo-session file, authenticating..")
            __jwt = self.__authenticate()
        
        access_token = __jwt["access_token"]

        headers = {
            #'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Bearer ' + access_token
        }
        self.s.headers.update(headers)

        return access_token

    def __authenticate(self) -> dict:
        """
            Authenticate using OAuth 2.0 Authorization Code Grant
            Reference: https://www.developer.saxo/openapi/learn/oauth-authorization-code-grant
        """
        self.logger.info("Authenticating to SaxoBank..")

        # Step 1, make auth request
        redirect_url = self.__auth_request()

        # Step 2, bypass manual auth process
        auth_code = self.__manual_auth(redirect_url)

        # Step 3, get access token
        access_obj = self.__access_token(auth_code, grant_type="authorization_code")

        # Append headers to the session object
        self.logger.info("Connected to SaxoBank. Storing valid headers in session..")
        headers = {
            #'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Bearer ' + access_obj["access_token"]
        }
        self.s.headers.update(headers)

        return access_obj

    def __refresh_token(self):
        # Read refresh token from file
        self.access_obj = utils.read_json(filename=self.session_filename)

        # Attempt to refresh token
        _token = self.__access_token(self.access_obj["refresh_token"], grant_type="refresh_token")
        if _token is None:
            self.logger.error("Unable to refresh token. Attempting to re-authenticate.")
            self.__authenticate()
        else:
            self.logger.info("Token refreshed.")
            return self.token

    def __valid_token(self, token):
        """
            Check if token is valid. If not, refresh token.
        """
        try:
            jwt.decode(token, options={"verify_signature": False})
            return True
        except ExpiredSignatureError:
            self.logger.error("Token has expired")
            self.__refresh_token()
            return False
        except Exception as e:
            self.logger.error("Something else went wrong", e)
            self.__refresh_token()
            return False

    def get(self, path) -> tuple:
        """
            Make GET request to SaxoBank API.

            Connection is checked before making request.

            Args:
                path (str): Path to resource

            Returns:
                tuple: (status_code, json)
        """
        # Check if token is valid (passive check)
        self.__valid_token(self.token)

        # Make request
        url = self.base_url + path
        self.logger.debug("GET {}".format(url))
        rsp = self.s.get(url)

        if rsp.status_code == 401:
            self.logger.warning("401 Unauthorized")
            self.__authenticate()
            self.logger.debug("GET {} (retry)".format(url))
            rsp = self.s.get(url)

        # Return response        
        response = namedtuple("Response", ["status_code", "json"])(rsp.status_code, rsp.json())
        self.logger.debug("{} {}".format(response.status_code, response.json))
        return response

    def post(self, path, data) -> tuple:
        """
            Make POST request to SaxoBank API.

            Connection is checked before making request.

            Args:
                path (str): Path to resource

            Returns:
                tuple: (status_code, json)
        """
        # Check if token is valid (passive check)
        self.__valid_token(self.token)

        # Make request
        url = self.base_url + path
        self.logger.debug("POST {}".format(url))

        rsp = self.s.post(url, json=data)

        if rsp.status_code == 401:
            self.logger.warning("401 Unauthorized")
            self.__authenticate()
            self.logger.debug("POST {} (retry)".format(url))
            rsp = self.s.post(url, json=data)

        # Return response        
        response = namedtuple("Response", ["status_code", "json"])(rsp.status_code, rsp.json())
        if response.status_code == 200:
            self.logger.debug("{} {}".format(response.status_code, json.dumps(response.json)))
        else:
            self.logger.error("{} {}".format(response.status_code, json.dumps(response.json)))
        return response

    def trade(self, signal):
        """ Execute Trade based on signal """
        self.logger.debug("Executing trade({signal})")
        s = self.signal_to_tuple(signal)
        self.logger.info(s)

        # Determine order action
        if s.action == "TRADE":
            self.logger.info("Placing trade for {signal}")
            buy = True if s.direction == "LONG" else False
            if self.profile["OrderPreference"].upper() == "MARKET":
                self.logger.info("Profile OrderPreference is set to MARKET")
                self.market(symbol=s.symbol, amount=self.profile["TradeSize"][s.symbol], buy=buy, stoploss_points=s.stoploss)
            elif self.profile["OrderPreference"].upper() == "LIMIT":
                self.logger.info("Profile OrderPreference is set to LIMIT")
                self.limit(symbol=s.symbol, amount=self.profile["TradeSize"][s.symbol], buy=buy, stoploss_points=s.stoploss)
            else:
                self.logger.error("Profile OrderPreference is not set")
        if s.action == "FLAT":
            # Set all profitable positions to flat
            positions = self.positions(cfd_only=True, profit_only=True)
            for i in positions["Data"]: 
                self.set_stoploss(position=i, points=0)
        if s.action == "SCALEOUT":
            # TODO
            self.logger.info("FLATSTOP not implemented yet")
            pass
        if s.action == "CLOSED":
            # Close latest positions that are not flat
            positions = self.positions(cfd_only=True, profit_only=False)
            import pytz
            import dateutil.parser
            TZ = pytz.timezone('America/Chicago')
            def __position_age(position):
                """
                    Return the age of a position in minutes
                """
                p = position
                now = datetime.now().astimezone(TZ)

                ExecutionTimeOpen = p["PositionBase"]["ExecutionTimeOpen"]
                ExecutionTimeOpen = dateutil.parser.parse(ExecutionTimeOpen).astimezone(TZ)
                delta = now - ExecutionTimeOpen
                delta_in_minutes = delta.total_seconds() // 60
                print(f"Position age: {delta_in_minutes} minutes")
                return delta_in_minutes
            
            for p in positions["Data"]:
                self.pretty_print_position(p)

                # Don't close positions without stoploss
                # Northy positions always have a stoploss, so this should be OK to skip
                if len(p["PositionBase"]["RelatedOpenOrders"]) == 0:
                    print("Position does not have a stoploss. Skipping..")
                    continue

                # skip if older than 1 hour
                # TODO: Analyze all northy close signals and see if they are all closed within 1 hour
                if __position_age(p) > 60:
                    print("Position is older than 1 hour. Skipping..")
                    continue

                self.close(position=p)
        if s.action == "FLATSTOP":
            # TODO
            self.logger.info("FLATSTOP nothing to do here..")
            pass
        if s.action == "LIMIT":
            # TODO
            self.logger.info("FLATSTOP not implemented yet")
            pass
  
    def positions(self, cfd_only=True, profit_only=True, symbol=None, status_open=True):
        """
            Get all positions

            Example output:
                See `tests/mock_data/SaxoTrader_Saxo_positions.json`
        """
        pos = self.get(f"/port/v1/positions/me").json

        # Filter positions
        if cfd_only:
            self.logger.info("Filtering positions, showing CFDs only")
            pos["Data"] = [p for p in pos["Data"] if p["PositionBase"]["AssetType"] == "CfdOnIndex"]
        
        if profit_only:
            self.logger.info("Filtering positions, showing positions in profit only")
            pos["Data"] = [p for p in pos["Data"] if p["PositionView"]["ProfitLossOnTrade"] > 0]
        
        if symbol is not None:
            self.logger.info(f"Filtering positions, showing positions for {symbol} only")
            pos["Data"] = [p for p in pos["Data"] if symbol == self.uic_lookup(uic=p["PositionBase"]["Uic"])]

        if status_open:
            status = "Open" if status_open else "Closed"
            self.logger.info(f"Filtering positions, showing positions with status {status} only")
            pos["Data"] = [p for p in pos["Data"] if p["PositionBase"]["Status"] == status]

        # Inject adjusted ProfitLossOnTrade based on real-time price
        # TODO: Asked Saxo Team if this is possible to do server-side
        # TODO: Only do this when needed ()
        for p in pos["Data"]:
            entry = p["PositionBase"]["OpenPrice"]
            uic = p["PositionBase"]["Uic"]
            real_price = self.price(uic)["Quote"]["Mid"]
            amount = p["PositionBase"]["Amount"]
            profit_adj = round((real_price - entry) * amount, 2)
            p["PositionView"]["ProfitLossOnTradeAdjusted"] = profit_adj
        
        return pos

    def orders(self, status_open=True):
        """
            Get all orders

            Example output:
                See `tests/mock_data/SaxoTrader_Saxo_orders.json`
        """
        orders = self.get(f"/port/v1/orders?ClientKey=" + self.profile["AccountKey"]).json

        # Filter orders
        """
        if status_open:
            status = "Open" if status_open else "Closed"
            self.logger.info(f"Filtering orders, showing orders with status {status} only")
            orders["Data"] = [o for o in orders["Data"] if o["Status"] == status]
        """
        return orders

    def get_stoploss_price(self, entry, stoploss, BuySell):
        """ Calculate stop loss price """
        if BuySell == "Buy":
            exit_price = entry - stoploss
        else:
            exit_price = entry + stoploss
        return exit_price

    def __action_trade(self, signal, order):
        """
            Handle Trade Orders 

            Example signal:
                SPX_TRADE_SHORT_IN_4162_SL_10
        """
        s = signal
        accountKey = self.TraderConfig["SAXO_DEMO"]["AccountKey"]

        # Market order
        order["BuySell"] = "Buy" if s.direction == "LONG" else "Sell"  # Set BuySell value
        order["Amount"] = self.config["TradeSize"][s.symbol]  # Set order quantity
        order["AccountKey"] = accountKey
        order["OrderDuration"] = { "DurationType": "DayOrder" }

        # Stop Loss order
        _SL_price = self.get_stoploss_price(s.entry, s.stoploss, order["BuySell"]) # Get stop loss price
        _SL_BuySell_Direction = "Sell" if order["BuySell"] == "Buy" else "Buy"
        stoploss_order = {
            "Uic": order["Uic"],
            "AccountKey": accountKey,
            "AssetType": order["AssetType"],
            "OrderType": "StopIfTraded",
            "ManualOrder": False,
            "BuySell": _SL_BuySell_Direction,
            "Amount": order["Amount"],
            "OrderDuration": { "DurationType": "GoodTillCancel" },
            "OrderPrice": _SL_price,
        }
        order["Orders"] = [stoploss_order]
        #order = {"AccountKey":"wlgQxI5-JzdhnV4s6BsDiA==","ManualOrder": False,"Uic":4913,"AssetType":"CfdOnIndex","OrderType":"Market","BuySell":"Buy","Amount":70,"OrderDuration":{"DurationType":"DayOrder"},"OrderRelation":"StandAlone","OrderContext":{"QuoteId":"638178880555876049","LastSeenClientBidPrice":4128.33,"LastSeenClientAskPrice":4129.23},"AppHint":17105153,"Orders":[{"AccountKey":"wlgQxI5-JzdhnV4s6BsDiA==","Uic":4913,"ManualOrder": False,"AssetType":"CfdOnIndex","Amount":70,"BuySell":"Sell","OrderDuration":{"DurationType":"GoodTillCancel"},"OrderPrice":4046.64,"OrderType":"StopIfTraded","AppHint":17105153}]}

        self.logger.info("{} was converted to market order at ~{} with stop loss at {}".format(s.raw, s.entry, _SL_price))

        # Execute order
        rsp = self.__post(path="/trade/v2/orders", data=order)
        time.sleep(2)

    def __action_flat(self, signal, order):
        """ Execute FLATSTOP signal """
        s = signal

        __positions = self.positions()
        for _p in __positions["Data"]:
            
            #self.logger.debug("Position: {}".format(_p))
            __pos_base = _p["PositionBase"]
            __pos_view = _p["PositionView"]
            __pos_id = _p["PositionId"]
            
            # Only touch CFDs
            __AssetType = __pos_base["AssetType"]
            if __AssetType != "CfdOnIndex":
                self.logger.debug("Skipping position with AssetType: {}".format(__AssetType))
                continue

            # Only touch open positions
            __status = __pos_base["Status"]  # Open, Closed, Pending, Rejected, Cancelled
            if __status != "Open":
                self.logger.debug("Skipping position with status: {}".format(__status))
                continue

            # Only touch positions in profit
            __PL = __pos_view["ProfitLossOnTrade"]
            if __PL < 0:
                self.logger.debug("Skipping position with ProfitLossOnTrade < 0: {}".format(__PL))
                continue

            # TODO
            # Position might already have a stop loss
            # If SL is far away we set it to break even
            # If SL is close we do nothing
            """
            related_orders = __pos_base["RelatedOpenOrders"]
            print(related_orders)
            if len(related_orders) > 0:
                for o in related_orders:
                    print(o)
                    _orderType = o["OrderType"]
                    pass
            """

            # Only touch positions with specific ticker??
            # TODO: Implement this

            # Set stop loss to break even
            self.logger.info("Setting stop loss to break even for position: {}".format(__pos_id))
            
            _amount = __pos_base["Amount"] * -1  # Reverse of the position amount
            _BuySell = "Buy" if _amount > 0 else "Sell"
            _orderPrice = __pos_base["OpenPrice"]  # TODO: Currently, we set the stop loss at break even, which might be different from Sven's entry price
            order = {
                "PositionId": __pos_id,
                "Orders":[{
                    "ManualOrder": False,
                    "AccountKey": self.profile["AccountKey"],
                    "Uic": self.tickers[s.symbol]["Uic"],
                    "AssetType": "CfdOnIndex",
                    "Amount": _amount,
                    "BuySell": _BuySell,
                    "OrderDuration": { "DurationType":"GoodTillCancel" },
                    "OrderPrice": _orderPrice,
                    "OrderType": "StopIfTraded",
                }]
            }
            r = self.s.post(f"{self.base_url}/trade/v2/orders", json=order)
            if r.status_code != 200:
                self.logger.error("Failed to set stop loss for position: {}".format(__pos_id))
                self.logger.error("Response: {}".format(r.json()))
            else:
                self.logger.info("Successfully set stop loss for position: {}".format(__pos_id))

            return None

    def __action_scaleout(self, signal, order):
        """ 
            Create scale out order.

            In Saxobank we cannot close a partial trade. Instead we create a new order in the opposite direction.
            SaxoBank will eventually handle real-time netting of the two orders.
        """
        s = signal
        self.logger.info(f"Handling scale out signal: {s.raw}")

        order["BuySell"] = "Buy" if s.entry > s.exit else "Sell"        # Set BuySell value
        order["Amount"] = self.config["TradeSize"][s.symbol] * 0.25     # Set amount (25% of trade size)
        order["OrderType"] = self.config["OrderType"]                   # Set OrderType

        self.logger.info("Scaling out by placing a {BuySell}ing {amount}".format(
            amount=order["Amount"], 
            BuySell=order["BuySell"])
        )

    def __action_closed(self, signal, order):
        """ 
            Close position

            Example signal:
                NDX_CLOSED
        """
        # TODO: Fix this
        #positions = saxo.positions()

        # Mock positions
        positions = dict()
        positions["Data"] = [
            {
            "NetPositionId": "GBPUSD_FxSpot",
            "PositionBase": {
                "AccountId": "192134INET",
                "Amount": 80.0,
                "AssetType": "CfdOnIndex",
                "CanBeClosed": True,
                "ClientId": "654321",
                "CloseConversionRateSettled": False,
                "ExecutionTimeOpen": "2023-04-08T15:00:00Z",
                "IsForceOpen": False,
                "IsMarketOpen": False,
                "LockedByBackOffice": False,
                "OpenPrice": 3990,
                "SpotDate": "2016-09-06",
                "Status": "Open",
                "Uic": 31,
                "ValueDate": "2017-05-04T00:00:00Z"
            },
            "PositionId": "1019942425",
            "PositionView": {
                "Ask": 1.2917,
                "Bid": 1.29162,
                "CalculationReliability": "Ok",
                "CurrentPrice": 4000,
                "CurrentPriceDelayMinutes": 0,
                "CurrentPriceType": "Bid",
                "Exposure": 80.0,
                "ExposureCurrency": "GBP",
                "ExposureInBaseCurrency": 129192.0,
                "InstrumentPriceDayPercentChange": 0.26,
                "ProfitLossOnTrade": -2998.0,
                "ProfitLossOnTradeInBaseCurrency": -2998.0,
                "SettlementInstruction": {
                "ActualRolloverAmount": 0.0,
                "ActualSettlementAmount": 80.0,
                "Amount": 80.0,
                "IsSettlementInstructionsAllowed": False,
                "Month": 7,
                "SettlementType": "FullSettlement",
                "Year": 2020
                },
                "TradeCostsTotal": 0.0,
                "TradeCostsTotalInBaseCurrency": 0.0
            }
            }
        ]
        for _p in positions["Data"]:
            # Only process CFDs
            if _p["PositionBase"]["AssetType"] != "CfdOnIndex":
                continue

            # Only deal with positions opened within the last 1 hour
            _open_time = datetime.strptime(_p["PositionBase"]["ExecutionTimeOpen"], "%Y-%m-%dT%H:%M:%SZ")
            if (datetime.now() - _open_time).total_seconds() > 3600:
                self.logger.info("Position was opened more than 1 hour. Skipping.")
                continue
            else:
                self.logger.info("Position was opened less than 1 hour.")

            # Only deal with positions within 25 points of profit/loss
            _points = (_p["PositionView"]["CurrentPrice"] - _p["PositionBase"]["OpenPrice"])
            if _points >= 25 or _points <= -25:
                self.logger.info("Position is not within 25 points of profit/loss. Skipping.")  
                continue
            else:
                self.logger.info("Position is within 25 points of profit/loss. Closing.")

            # Closing position
            self.logger.info("Closing position.")
            _position_size = _p["PositionBase"]["Amount"]
            order["Amount"] = -int(_position_size)
            order["PositionId"] = _p["PositionId"]
            order["AccountKey"] = self.profile["AccountKey"]
            print(order)
            
            # Close position using saxo_openapi
            r = tr.positions.ExercisePosition(order["PositionId"], data=order)
            print(r)
            rv = self.client.request(r)

            # Close order using requests
            """
            self.authenticate()
            r = self.s.put(f"{self.base_url}/trade/v1/positions/stringValue/exercise", data=order)
            print(r.content)
            """

    def __action_limit(self, signal, order):
        """
            Handle Limit Order

            Example signal:
                SPX_LIMIT_LONG_IN_3749_OUT_3739_SL_10
        """
        s = signal

        # Market order
        order["BuySell"] = "Buy" if s.direction == "LONG" else "Sell"  # Set BuySell value
        order["Amount"] = self.config["TradeSize"][s.symbol]  # Set order quantity
        order["OrderPrice"] = s.entry
        order["OrderType"] = "Limit"

        # Stop Loss order
        _SL_price = self.get_stoploss_price(entry=s.entry, stoploss=s.stoploss, BuySell=order["BuySell"])
        _SL_BuySell_Direction = "Sell" if order["BuySell"] == "Buy" else "Buy"
        order["Orders"] =  [{
            "BuySell": _SL_BuySell_Direction,
            "ManualOrder": False,
            "OrderDuration": { "DurationType": "GoodTillCancel" },
            "OrderPrice": _SL_price,
            "OrderType": "StopIfTraded"
        }]
        self.logger.info("{} was converted to a limit order at ~{} with stop loss at {}".format(s.raw, s.entry, _SL_price))

    def price(self, uic=None, symbol=None):
        """ Get price for one or more UICs """
        assetType = "CfdOnIndex"
        uic = uic if uic is not None else self.uic_lookup(symbol)["Uic"]
        path = f"/trade/v1/infoprices/?Uic={uic}&AssetType={assetType}"
        time.sleep(1)  # Lame way to avoid rate limiting
        return self.get(path=path).json

    ####### TRADING #######
    def stoploss_order(self, uic, stoploss_price, BuySell):
        """ Create stop loss order """
        _SL_BuySell_Direction = "Sell" if BuySell == "Buy" else "Buy"  # Invert BuySell value
        stoploss_order = {
            "Uic": uic,
            "AccountKey": self.profile["AccountKey"],
            "AssetType": "CfdOnIndex",
            "OrderType": "StopIfTraded",
            "ManualOrder": False,
            "BuySell": _SL_BuySell_Direction,
            "Amount": self.order["Amount"],
            "OrderDuration": { "DurationType": "GoodTillCancel" },
            "OrderPrice": stoploss_price,
        }
        return [stoploss_order]

    def base_order(self, symbol, amount, buy=True, 
                   limit=None, stoploss_points=None, stoploss_price=None, OrderType="Market"):
        """
            Handle Trade Orders 

            Example signal:
                SPX_TRADE_SHORT_IN_4162_SL_10
        """
        # Base order parameters
        self.order = dict()
        self.order["Uic"] = self.uic_lookup(symbol)["Uic"]
        self.order["AssetType"] = self.uic_lookup(symbol)["AssetType"]
        self.order["OrderType"] = OrderType
        self.order["ManualOrder"] = False

        # Market order
        self.order["BuySell"] = "Buy" if buy == True else "Sell"
        self.order["Amount"] = amount
        self.order["AccountKey"] = self.profile["AccountKey"]
        self.order["OrderDuration"] = { "DurationType": "DayOrder" }

        # Limit order
        if limit is not None:
            self.order["OrderPrice"] = limit
            self.order["OrderType"] = "Limit"

        # Stop Loss
        if stoploss_price is not None:
            # Set fixed Stop Loss
            order = self.stoploss_order(uic=self.order["Uic"], stoploss_price=stoploss_price, BuySell=self.order["BuySell"])
            self.order["Orders"] = order
        elif stoploss_points is not None:
            # Set Stop Loss on Market Order
            
            # When adding SL to a market order, we don't know the entry price of the trade yet.
            # We therefore estimate the entry price by looking at the current bid price.
            bid = self.bid(symbol=symbol)  # estimated entry price
            #print("Estimated entry price: {}".format(bid))

            stoploss_points = 25 if symbol == "NDX" else 10 # TODO: Make this dynamic
            #print("Stop loss points: {}".format(stoploss_points))

            stoploss_price = self.get_stoploss_price(entry=bid, stoploss=stoploss_points, BuySell=self.order["BuySell"])
            #print("Stop loss price: {}".format(stoploss_price))

            order = self.stoploss_order(uic=self.order["Uic"], stoploss_price=stoploss_price, BuySell=self.order["BuySell"])

            self.order["Orders"] = order
        else:
            # No Stop Loss added to order
            pass

        # Execute order
        self.logger.info(self.order)
        rsp = self.post(path="/trade/v2/orders", data=self.order)
        
        # Sleep to avoid rate limiting
        time.sleep(2)

        return rsp

    def market(self, symbol, amount, buy=True, stoploss_points=None, stoploss_price=None):
        return self.base_order(symbol=symbol,
                               amount=amount,
                               buy=buy, 
                               stoploss_points=stoploss_points,
                               stoploss_price=stoploss_price)

    def close(self, position):
        """ Close position """
        PositionId = position["PositionId"]
        pb = position["PositionBase"]
        BuySell = "Sell" if pb["Amount"] > 0 else "Buy"
        inserse_amount = pb["Amount"] * -1
        
        order = {
            "PositionId": PositionId,
            "Orders": [{
                "AccountKey": self.accountKey,
                "Uic": pb["Uic"],
                "AssetType": pb["AssetType"],
                "OrderType": "Market",
                "BuySell": BuySell,
                "ManualOrder": False,
                "Amount": inserse_amount,
                "OrderDuration": {
                    "DurationType": "DayOrder"
                },
                "OrderRelation": "StandAlone",
            }]
        }

        # Execute order
        self.logger.debug(order)
        self.logger.info("Closing position: {}".format(PositionId))
        rsp = self.post(path="/trade/v2/orders", data=order)
        time.sleep(1) # Sleep to avoid rate limiting
        return rsp

    def limit(self, symbol, amount, buy=True, limit=None, stoploss_points=None, stoploss_price=None):
        print(f"symbol={symbol}, amount={amount}, buy={buy}, price={limit}, stoploss_price={stoploss_price}, points={stoploss_points}")
        if stoploss_points is not None:
            stoploss_price = limit - stoploss_points if buy else limit + stoploss_points
        return self.base_order(symbol=symbol, 
                               amount=amount, 
                               buy=buy, 
                               limit=limit, 
                               stoploss_price=stoploss_price)

    def bid(self, symbol):
        return self.price(symbol=symbol)["Quote"]["Bid"]

    def set_stoploss(self, position, points=0):
        """
            Set stop loss for position

            Args:
                position (dict): Position object
                price (float): Stop loss price
        """
        p = position

        pos_id = p["PositionId"]
        uic = p["PositionBase"]["Uic"]
        entry = p["PositionBase"]["OpenPrice"]
        self.order["Amount"] = p["PositionBase"]["Amount"] * -1
        BuySell = "Buy" if self.order["Amount"] < 0 else "Sell"
        
        stoploss_price = self.get_stoploss_price(entry=entry, stoploss=points, BuySell=BuySell)
        print("Stoploss set {points} away from entry {entry} @ {stoploss_price}".format(stoploss_price=stoploss_price, entry=entry, points=points))

        __order = {
            "PositionId": pos_id,
            "Orders": self.stoploss_order(uic=uic, stoploss_price=stoploss_price, BuySell=BuySell)
        }
        
        rsp = self.post(path="/trade/v2/orders", data=__order)
        return rsp

