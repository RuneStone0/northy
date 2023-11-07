import jwt
import requests
from requests import Response
import pandas as pd
import random, string
import time, uuid, json
from .utils import Utils
from datetime import datetime, timezone
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

    def set_profile(self, profile_name):
        """ Set profile """
        self.profile_name = profile_name
        self.profile = self.config["profiles"][self.profile_name]
        self.environment_name = self.profile["environment"]
        self.environment = self.config["environments"][self.environment_name]
        self.username = self.profile["username"]
        self.password = self.profile["password"]

        self.logger.info(f"Using profile: {self.profile_name} ({self.environment_name})")

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

    ### Auth ###
    def __auth_request(self):
        # Vars
        auth_endpoint = self.environment["AuthorizationEndpoint"]
        client_id = self.environment["AppKey"]
        redirect_uri = self.environment["RedirectUrls"][1]

        url = f"{auth_endpoint}?response_type=code&client_id={client_id}&state={self.state}&redirect_uri={redirect_uri}"
        self.logger.debug(f"GET {url}")
        r = self.s.get(url, allow_redirects=False)
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

        if post_login_url == "/sim/login/ChangePassword":
            # TODO: Add prowl notification here
            # TODO: Use API keys instead ?
            self.logger.critical("Password change required. Manually change the password and update the config file.")
            raise Exception("Password change required")

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

    def refresh_token(self) -> str:
        """
            Refresh token using OAuth 2.0 Refresh Token Grant
            
            Reference: https://www.developer.saxo/openapi/learn/oauth-refresh-token-grant

            Returns:
                str: Access token (e.g. `eyJhbGciOiJFUzI1NiIsI...`)
        """

        self.logger.info("Refreshing token..")
        self.access_obj = utils.read_json(filename=self.session_filename)
        _token = self.__access_token(self.access_obj["refresh_token"],
                                     grant_type="refresh_token")
        
        if _token:
            self.logger.info("Token refreshed.")
            return _token
        else:
            self.logger.error("Unable to refresh token. Attempting to re-authenticate.")
            return self.__authenticate()
        
    def valid_token(self, token) -> bool:
        """
            Check if token is valid. If not, refresh token.
        """
        try:
            jwt.decode(token, options={"verify_signature": False})
            return True
        except ExpiredSignatureError:
            self.logger.error("Token has expired")
            self.refresh_token()
            return False
        except Exception as e:
            self.logger.error(f"Error in valid_token(): {e}")
            self.refresh_token()
            return False

    def get(self, path) -> Response:
        """
            Make GET request to SaxoBank API.

            Connection is checked before making request.

            Args:
                path (str): Path to resource

            Returns:
                tuple: (status_code, json)
        """
        # Check if token is valid (passive check)
        self.valid_token(self.token)

        # Make request
        url = self.base_url + path
        self.logger.debug("GET {}".format(url))
        rsp = self.s.get(url)

        if rsp.status_code == 401:
            self.logger.warning("401 Unauthorized")
            self.__authenticate()
            self.logger.debug("GET {} (retry)".format(url))
            rsp = self.s.get(url)

        return rsp

    def post(self, path, data, method_override="POST") -> Response:
        """
            Make POST request to SaxoBank API.

            Connection is checked before making request.

            Args:
                path (str): Path to resource

            Returns:
                tuple: (status_code, json)
        """
        # Check if token is valid (passive check)
        self.valid_token(self.token)

        # Method Override
        # https://www.developer.saxo/openapi/learn/openapi-request-response?phrase=405
        self.s.headers.update({"X-HTTP-Method-Override": method_override})

        # Make request
        url = self.base_url + path
        self.logger.debug("POST {}".format(url))
        rsp = self.s.post(url, json=data)

        # If 401, re-authenticate and retry
        if rsp.status_code == 401:
            self.logger.warning("401 Unauthorized")
            self.__authenticate()
            self.logger.debug("POST {} (retry)".format(url))
            rsp = self.s.post(url, json=data)
        
        if rsp.status_code != 200:
            self.logger.error(f"POST {url} failed with status code {rsp.status_code}")
            self.logger.error(rsp.json())
            return rsp

        return rsp

    def trade(self, signal) -> dict:
        """ 
            Execute Trade based on signal

            Args:
                signal (str): Signal to execute. (e.g. `SPX_TRADE_SHORT_IN_4162_SL_10`)

            Returns:
                dict: Order response

            Example response:
                `{'OrderId': '5014824029', 'Orders': [{'OrderId': '5014824030'}]}`
        """
        self.logger.debug(f"Processing signal: {signal}")

        # Convert signal to namedtuple
        s = self.signal_to_tuple(signal)
        self.logger.debug(s)

        # Determine action
        if s.action == "TRADE":
            self.logger.info("Placing trade for {signal}")
            buy = True if s.direction == "LONG" else False
            if self.profile["OrderPreference"].upper() == "MARKET":
                self.logger.info("Profile OrderPreference is set to MARKET")
                order = self.market(symbol=s.symbol, 
                                   amount=self.profile["TradeSize"][s.symbol],
                                   buy=buy, stoploss_points=s.stoploss)
                return order
            elif self.profile["OrderPreference"].upper() == "LIMIT":
                self.logger.info("Profile OrderPreference is set to LIMIT")
                order = self.limit(symbol=s.symbol, 
                                  amount=self.profile["TradeSize"][s.symbol],
                                  buy=buy, stoploss_points=s.stoploss)
                return order
            else:
                self.logger.error("Profile OrderPreference is not set")
        if s.action == "FLAT":
            """ Set positions stop loss to flat """
            self.action_flat(symbol=s.symbol)
        if s.action == "SCALEOUT":
            # TODO
            self.logger.info("SCALEOUT not implemented yet")
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
                saxo_helper = SaxoHelper()
                saxo_helper.pprint_positions(p)

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
            """ 
                Position hit its stop loss. Depending on the signal, 
                we might re-enter the position (handled by "TRADE" action)
            """
            msg = f"Tweet indicated that {s.symbol} hit its stop loss.."
            self.logger.info(msg)
        if s.action == "LIMIT":
            # TODO
            self.logger.info("FLATSTOP not implemented yet")
            pass

    def enable_real_time_prices(self):
        """
            Enable real-time prices

            https://openapi.help.saxo/hc/en-us/articles/4405160701085-How-do-I-choose-between-receiving-delayed-and-live-prices-
        """
        # TODO: Never got this working..
        # Enable real-time data
        data = { "TradeLevel": "FullTradingAndChat" }
        rsp = self.post(f"/root/v1/sessions/capabilities", method_override="PATCH", data=data)
        if rsp.status_code == 202:
            self.logger.info("Real-time data is being enabled (might take a while)")
        if rsp.status_code == 200:
            self.logger.info("Real-time data is enabled")
        print(rsp)
        time.sleep(10)


    def positions(self, cfd_only=True, profit_only=True, symbol=None, 
                  status_open=True) -> dict:
        """
            Get all positions

            Example output:
                See `tests/mock_data/SaxoTrader_Saxo_positions.json`
                {
                    '__count': 5,
                    'Data': [..]
                }
        """
        self.logger.warning("Prices are delayed by 15 minutes.")

        # Get all positions
        pos = self.get(f"/port/v1/positions/me").json()

        # Filter positions
        saxo_helper = SaxoHelper()
        pos = saxo_helper.filter_positions(pos, cfd_only=cfd_only, 
            profit_only=profit_only, symbol=symbol, status_open=status_open)

        return pos

    def orders(self, status_open=True):
        """
            Get all orders

            Example output:
                See `tests/mock_data/SaxoTrader_Saxo_orders.json`
        """
        orders = self.get(f"/port/v1/orders?ClientKey=" + self.profile["AccountKey"]).json()

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

    def action_flat(self, symbol):
        """ Execute FLATSTOP signal """
        # Get all profitable positions
        
        # TODO:Get real-time pricing working for positions(). Meanwhile,
        # set profit_only=False until we can get real-time prices

        positions = self.positions(cfd_only=True, 
                                    profit_only=False,
                                    symbol=symbol)
        
        saxo_helper = SaxoHelper()
        saxo_helper.pprint_positions(positions)

        for position in positions["Data"]:
            position_id = position["PositionId"]

            stop_details = saxo_helper.get_position_stop_details(position)

            if stop_details["stop"]:
                stop_points = stop_details["stop_points"]
                self.logger.info(f"Position ({position_id}) already have stop set to {stop_points} points.")
            else:
                self.set_stoploss(position=position, points=0)

            """
            print(stop_details)
            if stop_details["stop_points"] == 0 and stop_details["stop"]:
                # Stop loss is enable and set to flat (0 points from entry)
                self.logger.debug(f"Position ({position_id}) is already flat. Skipping..")
                continue
            else:
                self.logger.info(f"Position ({position_id}) stop loss set to flat")
                self.set_stoploss(position=position, points=0)
            """

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

    def price(self, uic):
        """ 
            Get price for uic

            Args:
                uic (int): Uic

            Returns:
                dict: Price response

            Example response:
            ```json
                {
                    'Uic': 4912
                    'AssetType': 'CfdOnIndex',
                    'LastUpdated': '2023-08-28T18:55:40.454000Z',
                    'PriceSource': 'NASDAQ',
                    'Quote': {
                        'Amount': 0,
                        'Ask': 15014.92,
                        'AskSize': 20.0,
                        'Bid': 15013.92,
                        'BidSize': 20.0,
                        'DelayedByMinutes': 0,
                        'ErrorCode': 'None',
                        'MarketState': 'Open',
                        'Mid': 15014.42,
                        'PriceSource': 'NASDAQ',
                        'PriceSourceType': 'Firm',
                        'PriceTypeAsk': 'Tradable',
                        'PriceTypeBid': 'Tradable'
                    }
                }
            ```
        """
        # TODO: Implement caching, when running e.g. "SXP_FLATSTOP", 
        # we will need to fetch prices for all positions
        path = f"/trade/v1/infoprices/?Uic={uic}&AssetType=CfdOnIndex"
        rsp = self.get(path=path)
        if rsp.status_code != 200:
            return None
        time.sleep(1)  # Lame way to avoid rate limiting
        return rsp.json()

    ####### TRADING #######
    def stoploss_order(self, uic, stoploss_price, BuySell, amount):
        """ 
            Creates stop loss order based on current order details.
            This method will create and invert details accordingly.

            For example, if you have an existing Buy order of 10 contracts,
            this method will create a Sell order of 10 contracts.
        """
        current_BuySell = BuySell
        current_amount = amount
        print(f"Current position amount: {current_amount}")
        print(f"Current position BuySell: {current_BuySell}")
        
        # Invert BuySell value
        BuySell = "Sell" if current_BuySell == "Buy" else "Buy"

        # Invert amount, but only for short positions
        if current_BuySell == "Sell":
            amount = amount * -1

        #print(f"Stop loss amount: {amount}")
        #print(f"Stop loss BuySell: {BuySell}")

        # Construct stop loss order
        stoploss_order = {
            "Uic": uic,
            "AccountKey": self.profile["AccountKey"],
            "AssetType": "CfdOnIndex",
            "OrderType": "StopIfTraded",
            "ManualOrder": False,
            "BuySell": BuySell,
            "Amount": amount,
            "OrderDuration": { "DurationType": "GoodTillCancel" },
            "OrderPrice": stoploss_price,
        }
        return [stoploss_order]

    def base_order(self, symbol, amount, buy=True, limit=None, 
                   stoploss_points=None, stoploss_price=None, 
                   OrderType="Market") -> Response:
        """
            Handles placing new orders

            Args:
                symbol (str): Symbol
                amount (int): Amount of contracts
                buy (bool): Buy or Sell
                limit (float): Limit price
                stoploss_points (int): Stop loss in points
                stoploss_price (float): Stop loss price
                OrderType (str): Market or Limit

            Returns:
                dict: Response from SaxoBank API

            Example response:
                {
                    "Orders": [
                        { "OrderId": "12345" },
                        { "OrderId": "12346" }
                    ]
                }
        """
        # Base order parameters
        saxo_helper = SaxoHelper()
        self.order = dict()
        self.order["Uic"] = saxo_helper.symbol_to_uic(symbol)
        self.order["AssetType"] = "CfdOnIndex"
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
            order = self.stoploss_order(uic=self.order["Uic"], 
                                        stoploss_price=stoploss_price, 
                                        BuySell=self.order["BuySell"],
                                        amount=self.order["Amount"])
            self.order["Orders"] = order
        elif stoploss_points is not None:
            # Set Stop Loss on Market Order
            
            # When adding SL to a market order, we don't know the entry price of the trade yet.
            # We therefore estimate the entry price by looking at the current bid price.
            bid = self.bid(self.order["Uic"])  # estimated entry price
            #print("Estimated entry price: {}".format(bid))

            stoploss_points = 25 if symbol == "NDX" else 10 # TODO: Make this dynamic
            #print("Stop loss points: {}".format(stoploss_points))

            stoploss_price = self.get_stoploss_price(entry=bid, stoploss=stoploss_points, BuySell=self.order["BuySell"])
            #print("Stop loss price: {}".format(stoploss_price))

            order = self.stoploss_order(uic=self.order["Uic"], 
                                        stoploss_price=stoploss_price, 
                                        BuySell=self.order["BuySell"],
                                        amount=self.order["Amount"])

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

    def close(self, position) -> Response:
        """ Close position """
        PositionId = position["PositionId"]
        pb = position["PositionBase"]
        BuySell = "Sell" if pb["Amount"] > 0 else "Buy"
        inserse_amount = pb["Amount"] * -1
        
        order = {
            "PositionId": PositionId,
            "Orders": [{
                "AccountKey": self.profile["AccountKey"],
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

    def bid(self, uic):
        return self.price(uic)["Quote"]["Bid"]

    def watch(self):
        from northy.db import Database
        db = Database().db
        saxo_helper = SaxoHelper()

        self.logger.info("Starting change stream....")
        while True:
            # Watch for new documents (tweets) where "alert" is not set
            pipeline = [
                # 'insert', 'update', 'replace', 'delete'
                { "$match": { "operationType": { "$in": ["update"] } } },

                # Only watch for "alert" Tweets
                { "$match": { "fullDocument.alert": True } },
            ]

            # Create a change stream
            stream = db.tweets.watch(pipeline, full_document='updateLookup')
            for change in stream:
                doc = change["fullDocument"]

                # Skip tweets older than 15 minutes
                # Safe guard to avoid executing trades on old tweets
                if saxo_helper.doc_older_than(doc, max_age=20):
                    continue

                # Execute trades for signals in tweet
                for signal in doc["signals"]:
                    self.trade(signal)

    def set_stoploss(self, position, points=0) -> bool:
        """
            Set stop loss for position

            Args:
                position (dict): Position object
                price (float): Stop loss price
        """
        # Current position details
        pos_id = position["PositionId"]
        position_base = position["PositionBase"]
        uic = position_base["Uic"]
        entry = position_base["OpenPrice"]
        amount = position_base["Amount"]
        BuySell = "Buy" if amount > 0 else "Sell"

        # Prepare stop loss order (oppoiste of current position)
        stoploss_price = self.get_stoploss_price(entry=entry, 
                                                 stoploss=points, 
                                                 BuySell=BuySell)
        orders = self.stoploss_order(uic=uic,
                                    stoploss_price=stoploss_price, 
                                    BuySell=BuySell,
                                    amount=amount)
        __order = {
            "PositionId": pos_id,
            "Orders": orders
        }
        print(__order)
        
        msg = f"Stop loss set to {stoploss_price} ({points} points) on {pos_id}"
        self.logger.info(msg)
        rsp = self.post(path="/trade/v2/orders", data=__order)
        time.sleep(1) # Sleep to avoid rate limiting

        if rsp.status_code != 200:
            # Cases
            # 1. Happens when saxo.positions() return positions that aren't in positive. The positions() method is not 100% accurate
            # {'Orders': [{'ErrorInfo': {'ErrorCode': 'OnWrongSideOfMarket', 'Message': 'Price is on wrong side of market'}}]}
            # 2. ???
            # {'Message': 'One or more properties of the request are invalid!', 'ModelState': {'Orders[0].Amount': ["'Amount' must be greater than '0'."]}, 'ErrorCode': 'InvalidModelState'}
            self.logger.error(f"Failed to set stop loss for position: {pos_id}. Response: {rsp.json()}")
            return False

        return True

    def cancel_order(self, orders:str):
        """
            Cancel order(s)

            Args:
                orders (str): Comma separated list of order IDs
        """
        self.logger.info("Cancelling orders: {}".format(orders))
        
        AccountKey = self.profile["AccountKey"]
        path = f"/trade/v2/orders/{orders}/?AccountKey={AccountKey}"
        rsp = self.post(path=path, data=None, method_override="DELETE")
        
        return rsp

# Create a SaxoHelper class that inherits from Saxo
class SaxoHelper(Saxo):
    def __init__(self, config_file="saxo_config.json", profile_name="default"):
        super().__init__(config_file, profile_name)
        self.logger = self.logger
        self.config = self.config

    def doc_older_than(self, document, max_age=15):
        """
            Check if document is older than max_age. `created_at` from db is
            converted to UTC, and compared against now()

            Args:
                document (dict): Document from MongoDB
                max_age (int): Max age in minutes

            Returns:
                bool: True if document is older than max_age
        """
        # Get current time in UTC
        now = datetime.now(timezone.utc)

        # Get created_at in UTC
        created_at = document["created_at"]
        created_at = created_at.replace(tzinfo=timezone.utc)

        # Calculate minutes since post
        min_since_post = (now - created_at).total_seconds() / 60
        min_since_post = round(min_since_post)
        self.logger.info(min_since_post)

        # Check if min_since_post is greater than max_age
        if min_since_post > max_age:
            tid = document["tid"]
            msg = f"Tweet {tid} from is {min_since_post} min. old. " \
                  f"Created at {created_at} compared to now ({now})."
            self.logger.info(msg)
            return True

        self.logger.info(f"Tweet is not older than {max_age} minutes")
        return False
    
    def pprint_positions(self, positions:dict) -> None:
        """
            Pretty print position(s)

            Args:
                position (dict): Dictionary of positions
        """
        data = []
        for p in positions["Data"]:
            pos_id = p["PositionId"]
            entry_date = p["PositionBase"]["ExecutionTimeOpen"]
            entry_date = datetime.strptime(entry_date, "%Y-%m-%dT%H:%M:%S.%fZ")
            entry_date = entry_date.replace(second=0, microsecond=0)
            print(p)

            uic = p["PositionBase"]["Uic"]
            symbol = self.uic_to_symbol(uic)
            entry = p["PositionBase"]["OpenPrice"]
            profit = p["PositionView"]["ProfitLossOnTrade"]
            sl_details = self.get_position_stop_details(p)
            sl_set = sl_details["stop"]
            amount = p["PositionBase"]["Amount"]
            status = p["PositionBase"]["Status"]
            
            data.append({
                "Pos. ID": pos_id,
                "Date": entry_date,
                "Symbol": symbol,
                "Amount": amount,
                "Entry": entry,
                "Profit": profit,
                "Status": status,
                "Stoploss Set": sl_set
            })
        df = pd.DataFrame(data)
        #print(df)
        print(df.to_string(index=False))

    def get_position_stop_details(self, position) -> dict:
        """
            Get stop loss details for position

            Args:
                position (dict): Position object

            Returns:
                dict: Stop loss details

            Example:
                `{"stop": False, "stop_price": 0, "stop_points": 0 }`
        """
        # Default values
        ret = { "stop": False, "stop_price": 0, "stop_points": 0 }
        
        # Check if stop loss order is set
        related_open_orders = position["PositionBase"].get("RelatedOpenOrders", [])
        for order in related_open_orders:
            if order["OpenOrderType"] == "StopIfTraded":
                ret["stop"] = True
                ret["stop_price"] = order["OrderPrice"]
                break

        # Find stop loss points
        if ret["stop"]:
            entry = position["PositionBase"]["OpenPrice"]
            ret["stop_points"] = entry - ret["stop_price"]

        return ret

    def filter_positions(self, positions, cfd_only=True, profit_only=True, 
                         symbol=None, status_open=True) -> dict:
        """
            Filter positions

            Args:
                positions (dict): Positions object
                cfd_only (bool): Show CFDs only
                profit_only (bool): Show positions in profit only
                symbol (str): Show positions for symbol only
                status_open (bool): Show open positions only

            Returns:
                dict: Filtered positions object

            Example:
                `{'__count': len(new_positions), 'Data': [..]}`
        """
        pos = positions["Data"]

        idx_to_remove = []
        idx = 0
        for p in pos:
            # CFD only
            if cfd_only and p["PositionBase"]["AssetType"] != "CfdOnIndex":
                idx_to_remove.append(idx)
            
            # Profit only
            if profit_only and p["PositionView"]["ProfitLossOnTrade"] <= 0:
                #print(p["PositionView"]["ProfitLossOnTrade"])
                idx_to_remove.append(idx)

            # Symbol only
            sym = self.uic_to_symbol(p["PositionBase"]["Uic"])
            if symbol is not None and symbol != sym:
                idx_to_remove.append(idx)

            # Status open only
            # Statuses: Open, Closed, Working
            if status_open and p["PositionBase"]["Status"] == "Closed":
                idx_to_remove.append(idx)
            
            idx += 1
            
        # Filter away positions
        new_positions = [p for i, p in enumerate(pos) if i not in idx_to_remove]
        return {'__count': len(new_positions), 'Data': new_positions}

    def uic_to_symbol(self, uic) -> str:
        """
            Lookup Uic and return symbol

            Args:
                uic (int): Uic to lookup (e.g. `4162`)

            Returns:
                uic (int): Uic (e.g. `4162`)

            Example:
                saxo.uic_to_symbol(4162) --> SPX
        """
        # TODO: Split this into two separate functions
        TABLE = self.config["tickers"]

        uic = int(uic)
        for symbol, v in TABLE.items():
            if v["Uic"] == uic:
                return symbol
        
        return f"N/A"

    def symbol_to_uic(self, symbol) -> int:
        """
            Lookup symbol and return uic

            Args:
                symbol (str): Symbol to lookup (e.g. `SPX`)

            Returns:
                uic (int): Uic (e.g. `4162`)

            Example:
                saxo.symbol_to_uic("SPX") --> 4162
        """
        TABLE = self.config["tickers"]
        symbol = symbol.upper()
        try:
            ret = TABLE[symbol]["Uic"]
            return ret
        except Exception:
            self.logger.error(f"symbol_to_uic failed for {symbol}")

    def generate_closed_positions_report(self, positions):
        """
            Generate a report of closed positions

            Args:
                positions (dict): Positions object

            Returns:
                dict: Report

            Example:
                >>> report = saxo.generate_closed_positions_report(positions)
                >>> print(report)
                >>> {
                >>>     "summary": "...",
                >>>     "date": "2023-07-31",
                >>>     "total_profit_loss": 725,
                >>>     "trades_profit_loss": "100,-12,678,-41",
                >>>     "count_closed_trades": 4
                >>> }
        """
        # Report values
        total_profit_loss = 0
        trades_profit_loss = []
        count_closed_trades = 0

        # Loop over all positions
        for p in positions["Data"]:
            # Extract values
            base = p["PositionBase"]
            uic = base["Uic"]
            amount = base["Amount"]
            status = base["Status"]
            ProfitLossOnTrade = p["PositionView"]["ProfitLossOnTrade"]

            # only report closed positions
            if status == "Closed":
                # filter away the parent positions
                if "CorrelationTypes" not in base.keys():
                    self.logger.info(f"Uic:{uic} Amount:{amount} P&L:{ProfitLossOnTrade}")
                    total_profit_loss += ProfitLossOnTrade
                    trades_profit_loss.append(ProfitLossOnTrade)
                    count_closed_trades += 1

        # Convert "2023-07-31T00:00:00.000000Z" to "2023-07-31"
        date = positions["Data"][0]["PositionBase"]["ValueDate"].split("T")[0]

        # Handle cases where no closed positions were found
        try:
            avg_profit_loss = total_profit_loss / count_closed_trades
        except ZeroDivisionError:
            avg_profit_loss = "N/A"
        
        return {
            "total_profit_loss": total_profit_loss,
            "count_closed_trades": count_closed_trades,
            "trades_profit_loss": trades_profit_loss,
            "avg_profit_loss": avg_profit_loss,
            "date": date
        }

    def job_generate_closed_positions_report(self, positions, force=False):
        """
            Generate a report of closed positions and send it via email.
            Report will only be generated at 17:00 on weekdays.

            Args:
                positions (dict): Positions object
                force (bool): Force report to sent via email
        """
        from .email import Email

        import pytz
        from datetime import datetime

        central = pytz.timezone('US/Central')
        now = datetime.now(central)
        is_reporting_time = now.weekday() < 5 and now.hour == 17 and now.second <= 5

        if is_reporting_time or force:
            report = self.generate_closed_positions_report(positions)

            # Create summary
            sheet = ",".join(map(str, report["trades_profit_loss"]))
            summary = """
            <p>Trading Date: %s</p>
            <p>Total Profit/Loss: %s</p>
            <p>Total Number of Trades: %s</p>
            <p>Average P&L/Trade: %s</p>
            <p>Sheet: %s</p>
            """ % (report["date"],
                    report["total_profit_loss"],
                    report["count_closed_trades"],
                    report["avg_profit_loss"],
                    sheet)

            # Send report to Email
            # TODO: remove hardcoded email
            email = Email()
            email.send(
                    to="rtk@rtk-cv.dk",
                    subject=f"Trading Report {report['date']}",
                    content=summary)
            
            if force:
                import sys
                sys.exit()
        else:
            # sleep until next full hour
            now = datetime.now()
            next_hour = now.replace(hour=(now.hour + 1) % 24, minute=0, second=1)
            sleep_time = (next_hour - now).seconds
            self.logger.info(f"Not time to report yet. Sleeping {sleep_time} seconds")
            time.sleep(sleep_time)



