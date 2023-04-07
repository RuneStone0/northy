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
from datetime import datetime, timezone

from saxo_openapi import API
import saxo_openapi.endpoints.rootservices as rs
import saxo_openapi.endpoints.trading as tr
import saxo_openapi.endpoints.portfolio as pf
from saxo_openapi.contrib.session import account_info

try:
    import colorlog
except ImportError:
    pass

def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
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
        j = jwt.decode(token, options={"verify_signature": False})
        exp = float(j["exp"])
        now = time.time()
        if exp < time.time():
            return True
        else:
            return False

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

        # Test if token is valid
        try:
            self.client = API(access_token=self.token)
            r = self.client.request(rs.diagnostics.Get())
            self.s.headers = self.token
            logger.debug("Connected. Storing valid headers in session..")
        except:
            logger.warning("Connection failed. Re-authenticating..")
            sys.exit()
            self.authenticate()

    def signal_to_order(self, signal):
        """ Convert signal to order """
        """
            TICKER - the ticker code e.g. SPX
            ACTION - the action to take on a signal
                TRADE       - enter new trade, based on direction we either go long / short
                FLATADJ     - adjust stop loss to break even
                FLATSTOP    - stop loss was triggered, this is just an observation, no action needed
                CLOSE       - close open position by buying/selling depending on the trade direction
            DIRECTION - define the position direction
                LONG        - go long a trade (buy)
                SHORT       - go short a trade (sell)
            PRICE - the price at which the signal was entered
            SL - the number of points from which to set the stop loss
        """
        s = signal.split("_")
        _symbol = s[0]

        # Fixed order parameters
        order = {}
        order["Uic"] = TraderConfig["SAXO_TICKER_LOOKUP"][_symbol]["Uic"]
        order["AssetType"] = TraderConfig["SAXO_TICKER_LOOKUP"][_symbol]["AssetType"]
        order["OrderType"] = self.config["OrderType"]
        order["ManualOrder"] = "false"

        if s[1] == "TRADE":
            """
                Handle Trade Orders

                Examples:
                    NDX_TRADE_LONG_11815_SL_385
            """
            logger.info(f"Handling Trade signal: {signal}")

            # Set BuySell value
            order["BuySell"] = "Buy" if s[2] == "LONG" else "Sell"

            # Set amount
            order["Amount"] = self.config["TradeSize"][_symbol]
            return order
        
        elif s[2] == "SCALE":
            """
                Handle Scale In/Out Orders

                Examples:
                    NDX_CLOSE_SCALE_IN_11815_OUT_12200_POINTS_385 (Long Scale)
                    SPX_CLOSE_SCALE_IN_4039_OUT_3965_POINTS_74 (Short Scale)
            """
            logger.info(f"Handling Scale signal: {signal}")

            # Set BuySell value
            _in = s[4]
            _out = s[6]
            order["BuySell"] = "Buy" if _in > _out else "Sell"
            _posType = "SHORT" if _in > _out else "LONG"
            logger.info(f"Scaling out of {_posType} position")

            # Set amount (25% of trade size)
            order["Amount"] = self.config["TradeSize"][_symbol] * 0.25

            # Set OrderType
            order["OrderType"] = self.config["OrderType"]

            logger.info(order)
            return order


    def trade(self, signal):
        # Convert signal to order format
        client = API(access_token=self.token)

        # Create Order requests
        if order is not None:
            r = tr.orders.Order(data=order)
            rv = client.request(r)
        else:
            logger.error(f"Unable to convert signal {signal} to order")
            return None
        
        print(json.dumps(rv, indent=2))
        return rv
  
    def positions(self):
        r = pf.positions.PositionsMe()
        rv = self.client.request(r)
        self.__write_json(rv, filename='.saxo-positions')
        return rv

if __name__ == "__main__":
    saxo = Saxo()
    #saxo.positions()

    # Long SPX
    #saxo.trade("SPX_TRADE_LONG_IN_3609_SL_10")
    
    # Close Long Scale
    order = saxo.signal_to_order("NDX_CLOSE_SCALE_IN_11680_OUT_12510_POINTS_830")
    order = saxo.signal_to_order("SPX_CLOSE_SCALE_IN_4039_OUT_3965_POINTS_74")
    #saxo.trade(order)
    
    # TODO 
    # tid: 1621139482593615872
    # FLATADJ
    # FLATSTOP
    # Support multiple orders in one signal
        # 1559260332106850315
        # 1559207058800611332

    # 1635259329120182274
        # ^ contains wrong signal

    

