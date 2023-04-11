import random, string
import time
import uuid
import logging
from logging.handlers import RotatingFileHandler
import requests
from requests.auth import HTTPBasicAuth
import json
import sys
import os
import jwt
from jwt.exceptions import ExpiredSignatureError
from datetime import datetime, timezone

from saxo_openapi import API
import saxo_openapi.endpoints.rootservices as rs
import saxo_openapi.endpoints.trading as tr
import saxo_openapi.endpoints.portfolio as pf
from saxo_openapi.contrib.session import account_info
from dotenv import dotenv_values

try:
    import colorlog
except ImportError:
    pass

def setup_logging():
    config = dotenv_values(".env")
    log_level = config["LOG_LEVEL"]
    root = logging.getLogger()
    logging.basicConfig(level=log_level)
    format = '%(asctime)s|%(levelname)8s|%(funcName)16s():%(lineno)3s|%(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    consoleFormat = logging.Formatter(format, date_format)
    
    # Log to console
    if 'colorlog' in sys.modules and os.isatty(2):
        cformat = '%(log_color)s' + format
        # The available color names are black, red, green, yellow, blue, purple, cyan and white.
        colorFormat = colorlog.ColoredFormatter(
            cformat,
            date_format,
            log_colors = {
                'DEBUG': 'white',
                'INFO' : 'green',
                'WARNING': 'yellow',
                'ERROR': 'red',
                'CRITICAL': 'purple' 
            })
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(colorFormat)
        root.addHandler(consoleHandler)
    else:
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(consoleFormat)
        root.addHandler(consoleHandler)

    # Log to file
    log_dir = os.path.join(os.path.normpath(os.getcwd() + os.sep + os.pardir), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_fname = os.path.join(log_dir, 'main.log')

    fileHandler = RotatingFileHandler(log_fname, maxBytes=1000000, backupCount=10) #10 files of 1MB each
    fileHandler.setFormatter(consoleFormat)
    root.addHandler(fileHandler)

setup_logging()
logger = logging.getLogger(__name__)


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

base_url = conf["OpenApiBaseUrl"]
client_id = conf["AppKey"]
redirect_uri = conf["RedirectUrls"][1]
state = str(uuid.uuid4())
user = "17470793"
pwd = "4ueax1y3"
basic = HTTPBasicAuth(conf["AppKey"], conf["AppSecret"])
session_filename = ".saxo-session"

# https://www.developer.saxo/openapi/learn/oauth-authorization-code-grant



# create random context that contain letters (a-z) and numbers (0-9) as well as - (dash) and _ (underscore). It is case insensitive. Max length is 50 characters.
ContextId = ''.join(random.choice(string.ascii_letters + string.digits + '-_') for i in range(50))
ReferenceId = ''.join(random.choice(string.ascii_letters + string.digits + '-_') for i in range(50))

#print(self.ContextId)
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
        self.connect()

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
            _jwt = r.json()
            # mask middle of token
            _access_token_masked = _jwt["access_token"][:10] + "..." + _jwt["access_token"][-10:]
            _masked_refresh_token = _jwt["refresh_token"][:5] + "..." + _jwt["refresh_token"][-5:]

            logger.debug("Access Token: " + _access_token_masked + " Refresh Token: " + _masked_refresh_token)

            # Write access token to file
            self.__write_json(_jwt)

            # Set token
            self.token = _jwt["access_token"]
            
            return _jwt

    def __write_json(self, data, filename='.saxo-session'):
        with open(filename,'w') as f:
            json.dump(data, f, indent=4)

    def __read_json(self, filename='.saxo-session'):
        with open(filename,'r') as f:
            data = json.load(f)
        return data
    
    def __get_bearer(self):
        """ Get bearer token from .saxo-session file """
        access_token = None
        try:
            data = self.__read_json()
            access_token = data["access_token"]
        except FileNotFoundError:
            logger.warning("No .saxo-session file found, authenticating..")
            self.authenticate()
            data = self.__read_json()
            access_token = data["access_token"]
        
        return access_token

    def __get_sl_price(self, entry_price, sl_points, BuySell):
        """ Calculate stop loss price """
        if BuySell == "Buy":
            exit_price = entry_price - sl_points
        else:
            exit_price = entry_price + sl_points
        return exit_price

    def authenticate(self):
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

    def refresh_token(self):
        # Read refresh token from file
        self.access_obj = self.__read_json()

        # Attempt to refresh token
        _token = self.__access_token(self.access_obj["refresh_token"], grant_type="refresh_token")
        if _token is None:
            logger.error("Unable to refresh token. Attempting to re-authenticate.")
            self.authenticate()
        else:
            logger.info("Token refreshed.")
            return self.token

    def has_token_expired(self, token):
        try:
            jwt.decode(token, options={"verify_signature": False})
            return False
        except ExpiredSignatureError:
            # Token has expired
            return True
        except Exception as e:
            # Something else went wrong
            logger.error(e)
            return True

    def get_balance(self):
        url = f"{base_url}/port/v1/balances/me"
        logger.debug(f"GET {url}")
        data = self.s.get(url)
        return data

    def connect(self):
        logger.debug("Test existing session..")

        # Check if token has expired
        if self.has_token_expired(self.token):
            logger.warning("Token has expired. Attempting to use refresh token..")
            self.refresh_token()
            return

        # Test if token is valid
        try:
            self.client = API(access_token=self.token)
            r = self.client.request(rs.diagnostics.Get())
            self.s.headers = self.token
            logger.debug("Connected. Storing valid headers in session..")
        except:
            logger.warning("Connection failed. Re-authenticating..")
            self.authenticate()

    def signal_to_order(self, signal):
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
            for _p in self.positions():
                # Only handle CFDs
                if _p["AssetType"] != "CfdOnIndex":
                    continue

                # Show positions without stop loss
                print(_p)
                #if _p["StopLoss"] is None:

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

        order = self.signal_to_order(signal)

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
        r = pf.positions.PositionsMe()
        rv = self.client.request(r)
        return rv

    def test_orders(self, ACTION="TRADE"):
        # TRADE LONG
        if ACTION == "TRADE":
            # 1564611389154627584, 1587398208833159174
            for s in ["SPX_TRADE_LONG_IN_3703_SL_10", "SPX_TRADE_SHORT_IN_3911_SL_10"]:
                saxo.trade(s)

        # FLAT - adjust existing order
        if ACTION == "FLAT":
            saxo.trade("NDX_FLAT")  # 1572950706344148993

        # FLATSTOP - ignore :)
        if ACTION == "FLATSTOP":
            saxo.trade("NDX_FLATSTOP")  # 1579486112367923201

        # CLOSED
        if ACTION == "CLOSED":
            saxo.trade("SPX_CLOSED")  # 1552366393990971392

        # SCALEOUT
        if ACTION == "SCALEOUT":
            orders = [
                "SPX_SCALEOUT_IN_3492_OUT_3685_POINTS_193",  # 1580876949982846976
                "NDX_SCALEOUT_IN_13720_OUT_12484_POINTS_1236",  # 1564010447782776832
            ]
            for s in orders:
                saxo.trade(s)

        # LIMIT
        if ACTION == "LIMIT":
            orders = [
                "SPX_LIMIT_LONG_IN_4000_OUT_3985_SL_15",  # 1641890973302116358
                "SPX_LIMIT_SHORT_IN_4318_OUT_4308_SL_10",  # 1560000766043119617
            ]
            for s in orders:
                saxo.trade(s)

if __name__ == "__main__":
    saxo = Saxo()
    #saxo.test_orders(ACTION="CLOSED")
    #saxo.positions()
