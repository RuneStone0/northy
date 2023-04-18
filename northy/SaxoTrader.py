import random, string
import time, uuid, json
import requests
from requests.auth import HTTPBasicAuth
import jwt
from jwt.exceptions import ExpiredSignatureError
from datetime import datetime
from saxo_openapi import API
import saxo_openapi.endpoints.rootservices as rs
import saxo_openapi.endpoints.trading as tr
import saxo_openapi.endpoints.portfolio as pf
from .logger import get_logger
from .utils import Utils
u = Utils()

logger = get_logger("SaxoTrader", "SaxoTrader.log")

conf = {
    "AppName": "Sim Timon",
    "AppKey": "c96263868bf745aa9ea697b6aef0f500",
    "AuthorizationEndpoint": "https://sim.logonvalidation.net/authorize",
    "TokenEndpoint": "https://sim.logonvalidation.net/token",
    "GrantType": "Code",
    "OpenApiBaseUrl": "https://gateway.saxobank.com/sim/openapi",
    "RedirectUrls": [
        "http://timon.rtk-cv.dk",
        "http://localhost/"
    ],
    "AppSecret": "aa2b0b4d070e4950b576b9c024a69914"
}

# https://www.developer.saxo/openapi/learn/oauth-authorization-code-grant
base_url = conf["OpenApiBaseUrl"]
client_id = conf["AppKey"]
redirect_uri = conf["RedirectUrls"][1]
state = str(uuid.uuid4())
user = "17470793"
pwd = "4ueax1y3"
basic = HTTPBasicAuth(conf["AppKey"], conf["AppSecret"])
session_filename = ".saxo-session"

# create random context that contain letters (a-z) and numbers (0-9) as well as - (dash) and _ (underscore). It is case insensitive. Max length is 50 characters.
ContextId = ''.join(random.choice(string.ascii_letters + string.digits + '-_') for i in range(50))
ReferenceId = ''.join(random.choice(string.ascii_letters + string.digits + '-_') for i in range(50))

TraderConfig = {
    "SAXO_TICKER_LOOKUP": 
        {
        "NDX": {
            "Uic": 4912,
            "AssetType": "CfdOnIndex"
        },
        "SPX": {
            "Uic": 4913,
            "AssetType": "CfdOnIndex"
        }
    },
    "SAXO_DEMO": {
        # Saxo Demo Account
        'AccountId': '17470793',
        'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==',
        'ContextId': ContextId,
        "ReferenceId": ReferenceId,

        # Set stake size (aka. 100%) for each instrument
        # Scales will be 25% of the stake size defined
        'TradeSize': {
            'NDX': 20.0,
            'SPX': 70.0
        },

        # Set preferred order type
        # Market, will be executed immediately
        # Limit, will be executed when price is reached (you might risk missing the trade)
        'OrderType': 'Market',
    }
}

class Saxo:
    def __init__(self):
        self.s = requests.session()
        self.s.headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        self.token = self.__get_bearer()
        self.client = None
        self._connect()

        # Set trade account config
        self.config = TraderConfig["SAXO_DEMO"]

    def __parse_url(sefl, url):
        """ Parse URL and return query string as dict """
        from urllib.parse import urlparse, parse_qs
        parsed_url = urlparse(url)
        return parse_qs(parsed_url.query)

    def __auth_request(self):
        auth_endpoint = conf["AuthorizationEndpoint"]
        url = f"{auth_endpoint}?response_type=code&client_id={client_id}&state={state}&redirect_uri={redirect_uri}"
        logger.info(f"GET {url}")
        r = self.s.get(url, allow_redirects=False)
        #logger(r.content)
        redirect_url = r.headers["Location"]
        return redirect_url

    def __manual_auth(self, redirect_url):
        """ Authenticate "manually" using user/pass """
        # Login
        data = {"field_userid": user, "field_password": pwd}
        logger.info(f"POST {redirect_url}")
        r = self.s.post(redirect_url, data=data, allow_redirects=False)
        post_login_url = r.headers["Location"]

        # Post login, fetch auth code
        logger.info(f"GET {post_login_url}")
        r = self.s.get(post_login_url, allow_redirects=False)
        auth_code_url = r.headers["Location"]
        auth_code = self.__parse_url(auth_code_url)["code"][0]
        logger.debug(f"Auth Code: {auth_code}")
        return auth_code

    def __access_token(self, auth_code, grant_type):
        url = conf["TokenEndpoint"]
        data = { "redirect_uri": redirect_uri, "grant_type": grant_type}

        if grant_type == "authorization_code":
            data["code"] = auth_code
        elif grant_type == "refresh_token":
            data["refresh_token"] = auth_code
        
        logger.info(f"POST {url}")
        r = self.s.post(url, auth=basic, data=data)
        if r.status_code == 401:
            logger.warning("401 Unauthorized")
            return None
        else:
            __jwt = r.json()
            # mask middle of token
            _access_token_masked = __jwt["access_token"][:10] + "..." + __jwt["access_token"][-10:]
            _masked_refresh_token = __jwt["refresh_token"][:5] + "..." + __jwt["refresh_token"][-5:]

            logger.debug("Access Token: " + _access_token_masked + " Refresh Token: " + _masked_refresh_token)

            # Write access token to file
            u.write_json(data=__jwt, filename=session_filename)

            # Set token
            self.token = __jwt["access_token"]
            
            return __jwt

    def __get_bearer(self):
        """ Get bearer token from .saxo-session file """
        __jwt = u.read_json(filename=session_filename)
        if __jwt is None:
            logger.warning("No .saxo-session file found, authenticating..")
            __jwt = self.__authenticate()

        if "access_token" not in __jwt:
            logger.warning("No access_token in .saxo-session file, authenticating..")
            __jwt = self.__authenticate()
        
        access_token = __jwt["access_token"]
        return access_token

    def __get_sl_price(self, entry_price, sl_points, BuySell):
        """ Calculate stop loss price """
        if BuySell == "Buy":
            exit_price = entry_price - sl_points
        else:
            exit_price = entry_price + sl_points
        return exit_price

    def __authenticate(self) -> dict:
        """
            Authenticate using OAuth 2.0 Authorization Code Grant
            Reference: https://www.developer.saxo/openapi/learn/oauth-authorization-code-grant
        """
        # Step 1, make auth request
        redirect_url = self.__auth_request()

        # Step 2, bypass manual auth process
        auth_code = self.__manual_auth(redirect_url)

        # Step 3, get access token
        access_obj = self.__access_token(auth_code, grant_type="authorization_code")

        # Store valid headers in session
        logger.debug("Connected. Storing valid headers in session..")
        headers = {'Authorization': 'Bearer ' + access_obj["access_token"]}
        self.s.headers = headers

        return access_obj

    def __refresh_token(self):
        # Read refresh token from file
        self.access_obj = u.read_json(filename=session_filename)

        # Attempt to refresh token
        _token = self.__access_token(self.access_obj["refresh_token"], grant_type="refresh_token")
        if _token is None:
            logger.error("Unable to refresh token. Attempting to re-authenticate.")
            self.__authenticate()
        else:
            logger.info("Token refreshed.")
            return self.token

    def __has_token_expired(self, token):
        try:
            jwt.decode(token, options={"verify_signature": False})
            return False
        except ExpiredSignatureError:
            logger.error("Token has expired")
            return True
        except Exception as e:
            logger.error("Something else went wrong", e)
            return True

    def _connect(self):
        logger.debug("Test existing session..")

        # Check if token has expired
        if self.__has_token_expired(self.token):
            logger.warning("Token has expired. Attempting to use refresh token..")
            self.__refresh_token()

        # Test if token is valid
        try:
            self.client = API(access_token=self.token)
            self.client.request(rs.diagnostics.Get())

            # TODO: Use this instead
            """
            r = self.s.get("https://gateway.saxobank.com/sim/openapi/root/v1/user")
            print(r.status_code)
            if r.status_code == 200:
                print("OK")
            """

            self.s.headers = headers = {'Authorization': 'Bearer ' + self.token}
            logger.debug("Connected. Storing valid headers in session..")
        except Exception as e:
            logger.error(e)
            logger.warning("Connection failed. Re-authenticating..")
            self.__authenticate()

    def __signal_to_order(self, signal):
        """ Convert signal to Saxo order """
        logger.debug(f"Input Signal: {signal}")
        s = signal.split("_")
        _symbol = s[0]
        _action = s[1]

        # Fixed order parameters
        order = dict()
        order["Uic"] = TraderConfig["SAXO_TICKER_LOOKUP"][_symbol]["Uic"]
        order["AssetType"] = TraderConfig["SAXO_TICKER_LOOKUP"][_symbol]["AssetType"]
        order["OrderType"] = self.config["OrderType"]
        order["ManualOrder"] = "false"
        
        if _action == "TRADE":
            """ Handle Trade Orders """
            # Market order
            order["BuySell"] = "Buy" if s[2] == "LONG" else "Sell"  # Set BuySell value
            order["Amount"] = self.config["TradeSize"][_symbol]  # Set order quantity

            # Stop Loss order
            _IN = float(s[4])
            _SL = float(s[6])
            _SL_price = self.__get_sl_price(_IN, _SL, order["BuySell"]) # Get stop loss price
            _SL_BuySell_Direction = "Sell" if order["BuySell"] == "Buy" else "Buy"
            order["Orders"] =  [{
                "BuySell": _SL_BuySell_Direction,
                "ManualOrder": "false",
                "OrderDuration": { "DurationType": "GoodTillCancel" },
                "OrderPrice": _SL_price,
                "OrderType": "StopIfTraded"
            }]
            logger.info("{} was converted to market order at ~{} with stop loss at {}".format(signal, _IN, _SL_price))
            
        elif _action == "SCALEOUT":
            """ 
                Create scale out order.

                In Saxobank we cannot close a partial trade. Instead we create a new order in the opposite direction.
                SaxoBank will eventually handle real-time netting of the two orders.
            """
            logger.info(f"Handling scale out signal: {signal}")

            _IN = float(s[3])
            _OUT = float(s[5])
            order["BuySell"] = "Buy" if _IN > _OUT else "Sell"              # Set BuySell value
            order["Amount"] = self.config["TradeSize"][_symbol] * 0.25      # Set amount (25% of trade size)
            order["OrderType"] = self.config["OrderType"]                   # Set OrderType

            logger.info("Scaling out by placing a {BuySell}ing {amount}".format(
                amount=order["Amount"], 
                BuySell=order["BuySell"])
            )

        elif _action == "FLAT":
            """ Set position to break even """
            logger.info(f"Handling FLATSTOP signal: {signal}")
            __positions = self.positions()
            for _p in __positions["Data"]:
                
                #logger.debug("Position: {}".format(_p))
                __pos_base = _p["PositionBase"]
                __pos_view = _p["PositionView"]
                __pos_id = _p["PositionId"]
                
                # Only touch CFDs
                __AssetType = __pos_base["AssetType"]
                if __AssetType != "CfdOnIndex":
                    logger.debug("Skipping position with AssetType: {}".format(__AssetType))
                    continue

                # Only touch open positions
                __status = __pos_base["Status"]  # Open, Closed, Pending, Rejected, Cancelled
                if __status != "Open":
                    logger.debug("Skipping position with status: {}".format(__status))
                    continue

                # Only touch positions in profit
                __PL = __pos_view["ProfitLossOnTrade"]
                if __PL < 0:
                    logger.debug("Skipping position with ProfitLossOnTrade < 0: {}".format(__PL))
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
                logger.info("Setting stop loss to break even for position: {}".format(__pos_id))
                
                _amount = __pos_base["Amount"] * -1  # Reverse of the position amount
                _BuySell = "Buy" if _amount > 0 else "Sell"
                _orderPrice = __pos_base["OpenPrice"]  # TODO: Currently, we set the stop loss at break even, which might be different from Sven's entry price
                order = {
                    "PositionId": __pos_id,
                    "Orders":[{
                        "ManualOrder": False,
                        "AccountKey": TraderConfig["SAXO_DEMO"]["AccountKey"],
                        "Uic": TraderConfig["SAXO_TICKER_LOOKUP"][_symbol]["Uic"],
                        "AssetType": "CfdOnIndex",
                        "Amount": _amount,
                        "BuySell": _BuySell,
                        "OrderDuration": { "DurationType":"GoodTillCancel" },
                        "OrderPrice": _orderPrice,
                        "OrderType": "StopIfTraded",
                    }]
                }
                r = self.s.post(f"{base_url}/trade/v2/orders", json=order)
                if r.status_code != 200:
                    logger.error("Failed to set stop loss for position: {}".format(__pos_id))
                    logger.error("Response: {}".format(r.json()))
                else:
                    logger.info("Successfully set stop loss for position: {}".format(__pos_id))

                return None

        elif _action == "CLOSED":
            """ Close position """
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
                    logger.info("Position was opened more than 1 hour. Skipping.")
                    continue
                else:
                    logger.info("Position was opened less than 1 hour.")

                # Only deal with positions within 25 points of profit/loss
                _points = (_p["PositionView"]["CurrentPrice"] - _p["PositionBase"]["OpenPrice"])
                if _points >= 25 or _points <= -25:
                    logger.info("Position is not within 25 points of profit/loss. Skipping.")  
                    continue
                else:
                    logger.info("Position is within 25 points of profit/loss. Closing.")

                # Closing position
                logger.info("Closing position.")
                _position_size = _p["PositionBase"]["Amount"]
                order["Amount"] = -int(_position_size)
                order["PositionId"] = _p["PositionId"]
                order["AccountKey"] = TraderConfig["SAXO_DEMO"]["AccountKey"]
                print(order)
                
                # Close position using saxo_openapi
                r = tr.positions.ExercisePosition(order["PositionId"], data=order)
                print(r)
                rv = self.client.request(r)

                # Close order using requests
                """
                self.authenticate()
                r = self.s.put(f"{base_url}/trade/v1/positions/stringValue/exercise", data=order)
                print(r.content)
                """

                return None

            return "CLOSE"
        
        elif _action == "FLATSTOP":
            logger.debug("FLATSTOP. No action needed.")
            return "FLATSTOP"

        elif _action == "LIMIT":
            """ Handle Trade Orders """
            _IN = float(s[4])
            _SL = float(s[8])

            # Market order
            order["BuySell"] = "Buy" if s[2] == "LONG" else "Sell"  # Set BuySell value
            order["Amount"] = self.config["TradeSize"][_symbol]  # Set order quantity
            order["OrderPrice"] = _IN
            order["OrderType"] = "Limit"
            
            # Stop Loss order
            _SL_price = self.__get_sl_price(_IN, _SL, order["BuySell"]) # Get stop loss price
            _SL_BuySell_Direction = "Sell" if order["BuySell"] == "Buy" else "Buy"
            order["Orders"] =  [{
                "BuySell": _SL_BuySell_Direction,
                "ManualOrder": "false",
                "OrderDuration": { "DurationType": "GoodTillCancel" },
                "OrderPrice": _SL_price,
                "OrderType": "StopIfTraded"
            }]
            logger.info("{} was converted to a limit order at ~{} with stop loss at {}".format(signal, _IN, _SL_price))

        return order

    def trade(self, signal):
        """ Execute Trade based on signal """
        logger.debug("Executing trade({})".format(json.dumps(signal)))

        order = self.__signal_to_order(signal)
        logger.debug("Order: {}".format(json.dumps(order)))
        if isinstance(order, dict):
            logger.debug("Order: {}".format(json.dumps(order)))
            r = tr.orders.Order(data=order)
            rv = self.client.request(r)
            logger.debug("Response: {}".format(json.dumps(rv)))
            time.sleep(1)  # Max 1 request per second (https://www.developer.saxo/openapi/learn/rate-limiting?phrase=Rate+Limit)
            return rv
        elif isinstance(order, str):
            logger.warning(f"Ignoring Order: {order}")
            return None
        else:
            logger.error(f"Unable to execute order {order}")
            return None
  
    def positions(self):
        """
            Get all positions

            Example output:
                See `tests/mock_data/SaxoTrader_Saxo_positions.json`
        """
        logger.debug("Getting positions.")
        r = pf.positions.PositionsMe()
        rv = self.client.request(r)
        logger.debug("Response: {}".format(json.dumps(rv)))
        return rv
