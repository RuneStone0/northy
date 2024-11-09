import os
import sys
from zoneinfo import ZoneInfo
import dateutil.parser
import jwt
import requests
from requests import Response
import pandas as pd
import time, uuid
from northy.utils import Utils
from northy.db import Database
from northy.secrets_manager import SecretsManager
from datetime import datetime, timezone
from collections import namedtuple
from requests.auth import HTTPBasicAuth
from jwt.exceptions import ExpiredSignatureError
import logging

utils = Utils()

class Saxo:
    def __init__(self, profile_name="dev"):
        # Create a logger instance for the class
        self.logger = logging.getLogger(__name__)
        self.saxo_helper = SaxoHelper()

        # Load profile
        self.set_profile(profile_name)

        # Misc vars
        self.session_filename = ".saxo-session-{}".format(self.env["username"])
        self.base_url = self.env["OpenApiBaseUrl"]
        self.state = str(uuid.uuid4())

        # Setup Saxo API connection
        self.s = requests.session()
        self.token = self.__get_bearer()

    def tradesize(self, symbol):
        """ Get trade size for symbol """
        return self.profile[symbol]
    
    def set_profile(self, profile_name) -> None:
        """ Load saxo profile form encrypted file """
        sm = SecretsManager()
        sm.read(file="conf/saxo_config.encrypted")
        try:
            self.profile = sm.get_dict()[profile_name]
        except KeyError:
            profile_names = [p for p in sm.get_dict() if "env" not in p]
            self.logger.error(f"Profile {profile_name} not found in saxo_config.encrypted. Available profiles: {profile_names}")
            sys.exit(1)
        self.env = sm.get_dict()[self.profile["environment"]]

        # Setting because it's used in multiple places
        self.AccountKey = self.profile["AccountKey"]

        # Log profile info
        self.logger.info(f"Using Saxo profile: {profile_name} ({self.profile})")

    def signal_to_tuple(self, signal):
        """ 
            Convert signal into a namedtuple
            
            Returns:
                namedtuple: signal

            Example namedtuple:
                signal(symbol='SPX', action='TRADE', direction='SHORT', entry=4162.0, stoploss=10.0, raw='SPX_TRADE_SHORT_IN_4162_SL_10')
        """
        s = signal.split("_")
        __action = s[1]

        if __action == "TRADE":
            # NDX_TRADE_SHORT_IN_13199_SL_25
            _entry, _sl = float(s[4]), float(s[6])
            # add buy boolean, if direction is LONG, buy is True else False
            _buy = True if s[2] == "LONG" else False
            return namedtuple("signal", [
                "symbol", "action", "direction", "entry", "stoploss", "raw", 
                "buy"])(s[0], s[1], s[2], _entry, _sl, signal, _buy)
        
        if __action == "SCALEOUT":
            # SPX_SCALEOUT_IN_3809_OUT_4153_POINTS_344
            _entry, _exit, _points = float(s[3]), float(s[5]), float(s[7])
            return namedtuple("signal", ["symbol", "action", "entry", "exit", "points", "raw"])(s[0], s[1], _entry, _exit, _points, signal)

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
            # add buy boolean, if direction is LONG, buy is True else False
            _buy = True if s[2] == "LONG" else False
            return namedtuple("signal", [
                "symbol", "action", "direction", "entry", "exit", "stoploss", 
                "raw", "buy"])(s[0], s[1], s[2], _entry, _exit, _sl, signal, _buy)

    ### Auth ###
    def __auth_request(self):
        # Vars
        auth_endpoint = self.env["AuthorizationEndpoint"]
        client_id = self.env["AppKey"]
        redirect_uri = self.env["RedirectUrls"]

        url = f"{auth_endpoint}?response_type=code&client_id={client_id}&state={self.state}&redirect_uri={redirect_uri}"
        self.logger.debug(f"GET {url}")
        r = self.s.get(url, allow_redirects=False)

        if r.status_code == 400:
            self.logger.error("400 Bad Request")
            self.logger.error(r.content)
            self.logger.error("Ensure you've added localhsot to the App Redirect URLs")
            raise Exception("400 Bad Request")

        redirect_url = r.headers["Location"]
        return redirect_url

    def __manual_auth(self, redirect_url):
        """ Authenticate "manually" using user/pass """
        self.logger.debug("Authenticating manually using user/pass")
        def __parse_url(url):
            """ Parse URL and return query string as dict """
            from urllib.parse import urlparse, parse_qs
            parsed_url = urlparse(url)
            return parse_qs(parsed_url.query)

        # Login
        data = {
            "field_userid": self.env["username"],
            "field_password": self.env["password"]}
        self.logger.debug(f"POST {redirect_url}")
        r = self.s.post(redirect_url, data=data, allow_redirects=False)

        # Get redirect URL
        try:
            post_login_url = r.headers["Location"]
        except:
            # TODO: Add prowl notification here
            self.logger.error("Unsuccessful logon. Check password and try manual authenticaition.")
            raise Exception("Unsuccessful logon")


        if post_login_url == "/sim/login/ChangePassword":
            # TODO: Add prowl notification here
            # TODO: Use API keys instead ?
            self.logger.critical("Password change required. Manually change the password and update the config file.")
            raise Exception("Password change required")

        # Post login, fetch auth code
        self.logger.debug(f"GET {post_login_url}")
        r = self.s.get(post_login_url, allow_redirects=False)
        if "/disclaimer" in r.text:
            # disclaimer page is shown after a new API App is created.
            self.logger.critical("Disclaimer page detected. Manual accept required.")
            self.logger.critical(f"1. Go to: {redirect_url}")
            self.logger.critical("2. Login and and accept the disclaimer.")
            self.logger.critical("3. Logout and try to login again programatically.")
            sys.exit(1)

        try:
            # Sometimes we don't get the Location header
            auth_code_url = r.headers["Location"]
        except:
            self.logger.warning("No Location header found. Parsing URL..")
            self.logger.warning(r.headers)
            self.logger.warning(r.text)

            self.logger.info("Re-trying Login request..")
            r = self.s.get(post_login_url, allow_redirects=False)

        # Get auth code from URL
        auth_code = __parse_url(auth_code_url)["code"][0]
        self.logger.debug(f"Auth Code: {auth_code}")
        return auth_code

    def __access_token(self, auth_code, grant_type):
        # Vars
        redirect_uri = self.env["RedirectUrls"]
        token_endpoint = self.env["TokenEndpoint"]
        app_key = self.env["AppKey"]
        app_secret = self.env["AppSecret"]
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
        self.logger.debug("Connected to SaxoBank. Storing valid headers in session..")
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

        self.logger.debug("Refreshing token..")
        self.access_obj = utils.read_json(filename=self.session_filename)
        _token = self.__access_token(self.access_obj["refresh_token"],
                                     grant_type="refresh_token")
        
        if _token:
            self.logger.debug("Token refreshed.")
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

        # 401 - Unauthorized
        if rsp.status_code == 401:
            self.logger.warning("401 Unauthorized")
            self.__authenticate()
            self.logger.debug("POST {} (retry)".format(url))
            rsp = self.s.post(url, json=data)

        # 409 - Duplicate order operations
        # https://www.developer.saxo/openapi/learn/rate-limiting
        if rsp.status_code == 409:
            self.logger.warning("409 Conflict - Duplicate order operations (Rate limit)")
            self.logger.warning("Retryning after 15 seconds..")
            time.sleep(15)
            self.logger.debug("POST {} (retry)".format(url))
            rsp = self.s.post(url, json=data)

        # If 429, Exceeding Limits
        # https://www.developer.saxo/openapi/learn/rate-limiting
        if rsp.status_code == 429:
            self.logger.warning("409 Too Many Requests - Exceeding Limits (Rate limit)")
            self.logger.critical(rsp.headers)

            # Not all end-points return X-RateLimit-Session-Reset
            if "X-RateLimit-Session-Reset" in rsp.headers:
                session_reset = rsp.headers["X-RateLimit-Session-Reset"]
                self.logger.warning(f"Retryning after {session_reset} seconds..")
                time.sleep(session_reset)

            self.logger.debug("POST {} (retry)".format(url))
            rsp = self.s.post(url, json=data)
            #sys.exit(1)

        if rsp.status_code == 204: # 204 - No Content
            return rsp

        if rsp.status_code == 404:
            self.logger.error(f"POST {url} failed with status code {rsp.status_code}")
            raise Exception("404 Not Found. Verify AccountKey in config is correct.")
        
        if rsp.status_code != 200:
            self.logger.warning(f"POST {url} failed with status code {rsp.status_code}")
            try:
                self.logger.warning(rsp.json())
            except:
                # No JSON response
                return rsp

        return rsp

    def trade(self, signal) -> Response:
        """ 
            Execute Trade based on signal

            Args:
                signal (str): Signal to execute. (e.g. `SPX_TRADE_SHORT_IN_4162_SL_10`)

            Returns:
                requests.Response: Order response

            Example response:
                `{'OrderId': '5014824029', 'Orders': [{'OrderId': '5014824030'}]}`
        """
        self.logger.info(f"Executing trade signal: {signal}")
        self.logger.info("Positions prior to trade:")
        self.positions(cfd_only=False, profit_only=False, show=True, status=["Open"])

        # Convert signal to namedtuple
        s = self.signal_to_tuple(signal)
        self.logger.debug(s)

        # Determine action
        if s.action == "TRADE":
            # Calculate stoploss price based on signal entry
            self.logger.info(f"Calculating stoploss price for {s.symbol} "
                             f"Entry: {s.entry}, Stoploss: {s.stoploss}")
            __stoploss_price = s.entry - s.stoploss if s.buy else s.entry + s.stoploss

            if self.profile["OrderPreference"] == "Market":
                return self.market(symbol=s.symbol, 
                                   amount=self.tradesize(s.symbol),
                                   buy=s.buy, stoploss_price=__stoploss_price)
                
            elif self.profile["OrderPreference"] == "Limit":
                return self.limit(symbol=s.symbol, limit=s.entry,
                                  amount=self.tradesize(s.symbol),
                                  buy=s.buy, stoploss_price=__stoploss_price)
            else:
                self.logger.error("Profile OrderPreference is not set")
        if s.action == "FLAT":
            """ Set positions stop loss to flat """
            self.action_flat(symbol=s.symbol)
        if s.action == "SCALEOUT":
            # Scale parameters
            self.logger.info(f"Scaling out of {s.symbol}..")
            pos_size = self.tradesize(s.symbol)
            scale_size = pos_size * 0.25
            positions = self.positions(cfd_only=True, profit_only=False,
                                       show=True, symbol=s.symbol)

            # Ensure we only scaleout of an existing position
            if positions["__count"] == 0:
                self.logger.warning("No positions found. Skipping..")
                return None

            # Initiate scaleout
            pos_data = positions["Data"]
            total_pos_size = sum(_p["PositionBase"]["Amount"] for _p in pos_data)
            current_position_is_long = True if s.entry < s.exit else False
            buy_scale_out = not current_position_is_long
            self.logger.info(f"Scaling out {scale_size} of the {total_pos_size}\
{s.symbol} position.")
            order = self.market(symbol=s.symbol,
                                amount=scale_size, 
                                buy=buy_scale_out)
            return order
        if s.action == "CLOSED":
            # Close latest positions that are not flat
            self.logger.debug(f"Closing recently opened {s.symbol} position")
            positions = self.positions(cfd_only=True, profit_only=False,
                                       show=True, symbol=s.symbol)
            tz = ZoneInfo('America/Chicago')
            
            def __position_age(position) -> int:
                """
                    Return the age of a position in minutes
                """
                now = datetime.now(tz=tz)
                pos_open_local_tz = position["PositionBase"]["ExecutionTimeOpen"]
                execution_time_open = dateutil.parser.parse(pos_open_local_tz).astimezone(tz)
                delta = now - execution_time_open
                return int(delta.total_seconds() // 60)
            
            for p in positions["Data"]:
                # Don't close positions without stoploss
                # Northy positions always have a stoploss
                if len(p["PositionBase"]["RelatedOpenOrders"]) == 0:
                    self.logger.info("Position does not have a stoploss. Skipping..")
                    continue

                # Don't close positions older than 1 hour.
                # Northy usually close positions shortly after they are opened.
                # Existing (old) positions might be manual trades
                # TODO: Analyze all northy close signals and see if they are all closed within 1 hour
                if __position_age(p) > 60:
                    pos_id = p["PositionId"]
                    self.logger.info(f"Position {pos_id} is older than 1 hour. Skipping..")
                    continue

                self.close(position=p)
        if s.action == "FLATSTOP":
            """ 
                Position hit its stop loss. Depending on the signal, 
                we might re-enter the position (handled by "TRADE" action)
            """
            msg = f"Tweet indicates that {s.symbol} hit its stop loss and was closed out.."
            self.logger.info(msg)
        if s.action == "LIMIT":
            # TODO
            self.logger.info("FLATSTOP not implemented yet")
            pass

        self.logger.debug("Current positions:")
        self.positions(cfd_only=False, profit_only=False, show=True)

        # Sleep to avoid rate limiting
        self.logger.info("Sleeping for 15 seconds to avoid rate limiting..")
        time.sleep(15)

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
        time.sleep(10)

    def positions(self, cfd_only:bool=True, profit_only:bool=True, symbol=None, 
                  status:list=None, show:bool=False) -> dict:
        # TODO: symbol is set to None, it should be a str, default to "" perhaps?
        """
            Get all positions

            Args:
                cfd_only (bool): Only show CFD positions
                profit_only (bool): Only show profitable positions
                symbol (str): Filter by symbol
                status (list): Filter by status (e.g. ["Open", "Closed", "Working"])
                show (bool): Print positions

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
            profit_only=profit_only, symbol=symbol, status=status)

        if show:
            saxo_helper.pprint_positions(pos)

        return pos

    def orders(self, orderId:str=None):
        """
            Get open order(s)

            Args:
                orderId (str): Order ID

            Example output:
                See `tests/mock_data/SaxoTrader_Saxo_orders.json`
        """
        if orderId:
            # Get specific order
            ClientKey = self.AccountKey
            orders = self.get(f"/port/v1/orders/{ClientKey}/{orderId}").json()
        else:
            # Get all orders
            orders = self.get(f"/port/v1/orders/me").json()

        self.logger.info(f"Orders: {orders}")
        return orders

    def get_stoploss_price(self, entry, stoploss, BuySell):
        """ Calculate stop loss price """
        if BuySell == "Buy":
            exit_price = entry - stoploss
        else:
            exit_price = entry + stoploss
        return exit_price

    def action_flat(self, symbol, profit_only=True):
        """ Execute FLATSTOP signal """
        # Get all profitable positions
        
        # TODO: Get real-time pricing working for positions().
        # Meanwhile, we'll work with delayed prices.
        # set profit_only=False until we can get real-time prices
        positions = self.positions(cfd_only=True, 
                                    profit_only=profit_only,
                                    symbol=symbol)
        
        saxo_helper = SaxoHelper()
        saxo_helper.pprint_positions(positions)

        # Loop through positions        
        for position in positions["Data"]:
            pos_id = position["PositionId"]
            p_base = position["PositionBase"]

            # Try to get entry and stoploss price
            # If RelatedOpenOrders doesn't exist, no stoploss exists.
            is_flat = False
            try:
                entry_price = p_base["OpenPrice"]
                stoploss_price = p_base["RelatedOpenOrders"][0]["OrderPrice"]
                if entry_price == stoploss_price:
                    is_flat = True
                    self.logger.info(f"{pos_id} is flat. Skipping..")
            except:
                # No stoploss postion found
                pass

            if not is_flat:
                self.set_stoploss(position=position, points=0)

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
        asset_type = self.saxo_helper.get_asset_type(uic)
        path = f"/trade/v1/infoprices/?Uic={uic}&AssetType={asset_type}"
        rsp = self.get(path=path)
        if rsp.status_code != 200:
            return None
        
        rsp_json = rsp.json()
        self.logger.debug(rsp_json)

        if rsp_json["Quote"]["PriceTypeBid"] == "NoAccess":
            # https://openapi.help.saxo/hc/en-us/articles/4405160773661
            # https://openapi.help.saxo/hc/en-us/articles/4416934146449
            url = "https://openapi.help.saxo/hc/en-us/articles/4416934146449"
            self.logger.warning(f"No access to price data. See: {url}")

        time.sleep(1)  # Lame way to avoid rate limiting

        return rsp.json()

    ####### TRADING #######
    def stoploss_order(self, uic, stoploss_price, BuySell, amount):
        """ 
            Creates stop loss order. This is used when new positions are created.
        """
        current_BuySell = BuySell

        # Invert BuySell value
        BuySell = "Sell" if current_BuySell == "Buy" else "Buy"

        # Construct stop loss order
        stoploss_order = {
            "Uic": uic,
            "AccountKey": self.AccountKey,
            "AssetType": self.saxo_helper.get_asset_type(uic),
            "OrderType": "StopIfTraded",
            "ManualOrder": False,
            "BuySell": BuySell,
            "Amount": amount,
            "OrderDuration": { "DurationType": "GoodTillCancel" },
            "OrderPrice": stoploss_price,
        }
        return [stoploss_order]
    
    def stoploss_order_existing(self, position, points_away=0):
        """ 
            Creates stop loss order for an existing position.
        """
        # General
        uic = position["PositionBase"]["Uic"]

        # Get current position details
        current_amount = position["PositionBase"]["Amount"]
        current_BuySell = "Buy" if current_amount > 0 else "Sell"
        current_OpenPrice = position["PositionBase"]["OpenPrice"]
        
        # Prepare stop loss order
        order_BuySell = "Sell" if current_BuySell == "Buy" else "Buy"
        if current_BuySell == "Buy":
            # If we want to set a SL on a LONG position (Buy), we want the order
            # to be BuySell: "Sell" of the same amount as the current position.
            order_amount = current_amount
        if current_BuySell == "Sell":
            # If we want to set a SL on a SHORT position (Sell), we want the order
            # to be BuySell: "Buy" of the _inverse_ amount as the current position.
            order_amount = current_amount * -1

        if order_BuySell == "Buy":
            order_OrderPrice = current_OpenPrice - points_away
        else:
            order_OrderPrice = current_OpenPrice + points_away

        stoploss_order = {
            "Uic": uic,
            "AccountKey": self.AccountKey,
            "AssetType": self.saxo_helper.get_asset_type(uic),
            "OrderType": "StopIfTraded",
            "ManualOrder": False,
            "BuySell": order_BuySell,
            "Amount": order_amount,
            "OrderDuration": { "DurationType": "GoodTillCancel" },
            "OrderPrice": order_OrderPrice,
        }
        return [stoploss_order]
    
    def stoploss_order_old(self, uic, stoploss_price, BuySell, amount):
        """ 
            Creates stop loss order based on current order details.
            This method will create and invert details accordingly.

            For example, if you have an existing Buy order of 10 contracts,
            this method will create a Sell order of 10 contracts.
        """
        current_BuySell = BuySell
        
        # Invert BuySell value
        BuySell = "Sell" if current_BuySell == "Buy" else "Buy"

        # Construct stop loss order
        asset_type = self.saxo_helper.get_asset_type(uic)
        stoploss_order = {
            "Uic": uic,
            "AccountKey": self.AccountKey,
            "AssetType": asset_type,
            "OrderType": "StopIfTraded",
            "ManualOrder": False,
            "BuySell": BuySell,
            "Amount": amount,
            "OrderDuration": { "DurationType": "GoodTillCancel" },
            "OrderPrice": stoploss_price,
        }
        return [stoploss_order]

    def base_order(self, symbol, amount, buy=True, limit=None, 
                   stoploss_price=None, OrderType="Market") -> Response:
        """
            Handles placing new orders

            Args:
                symbol (str): Symbol
                amount (int): Amount of contracts
                buy (bool): Buy or Sell
                limit (float): Limit price
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
        uic = saxo_helper.symbol_to_uic(symbol)
        asset_type = self.saxo_helper.get_asset_type(uic)
        self.order = dict()
        self.order["Uic"] = uic
        self.order["AssetType"] = asset_type
        self.order["OrderType"] = OrderType
        self.order["ManualOrder"] = False

        # Market order
        self.order["BuySell"] = "Buy" if buy == True else "Sell"
        self.order["Amount"] = amount
        self.order["AccountKey"] = self.AccountKey
        self.order["OrderDuration"] = { "DurationType": "DayOrder" }

        # Limit order
        if OrderType == "Limit" and limit is not None:
            self.order["OrderPrice"] = limit

        # Stop Loss
        if stoploss_price:
            # Set fixed Stop Loss
            self.order["Orders"] = self.stoploss_order(uic=self.order["Uic"], 
                                        stoploss_price=stoploss_price, 
                                        BuySell=self.order["BuySell"],
                                        amount=self.order["Amount"])

        # Execute order
        self.logger.info(self.order)
        rsp = self.post(path="/trade/v2/orders", data=self.order)
        print(rsp, rsp.content)
        self.logger.debug(f"Response: {rsp.json()}")
        
        # Sleep to avoid rate limiting
        time.sleep(2)

        return rsp

    def market(self, symbol, amount, buy=True, stoploss_price=None):
        self.logger.debug(f"Placing market order: {symbol} ({amount} contracts)")
        return self.base_order(symbol=symbol,
                               amount=amount,
                               buy=buy, 
                               stoploss_price=stoploss_price)

    def close(self, position) -> Response:
        """ Close position """
        # Current position details
        PositionId = position["PositionId"]
        pb = position["PositionBase"]
        current_amount = position["PositionBase"]["Amount"]
        current_BuySell = "Buy" if current_amount > 0 else "Sell"

        # Prepare order
        order_BuySell = "Sell" if current_BuySell == "Buy" else "Buy"
        if current_BuySell == "Buy":
            # If we want to set a SL on a LONG position (Buy), we want the order
            # to be BuySell: "Sell" of the same amount as the current position.
            order_amount = current_amount
        if current_BuySell == "Sell":
            # If we want to set a SL on a SHORT position (Sell), we want the order
            # to be BuySell: "Buy" of the _inverse_ amount as the current position.
            order_amount = current_amount * -1

        order = {
            "PositionId": PositionId,
            "Orders": [{
                "AccountKey": self.AccountKey,
                "Uic": pb["Uic"],
                "AssetType": pb["AssetType"],
                "OrderType": "Market",
                "BuySell": order_BuySell,
                "ManualOrder": False,
                "Amount": order_amount,
                "OrderDuration": {
                    "DurationType": "DayOrder"
                },
                "OrderRelation": "StandAlone",
            }]
        }

        # Execute order
        self.logger.debug(order)
        self.logger.info(f"Closing position: {PositionId}")
        rsp = self.post(path="/trade/v2/orders", data=order)
        time.sleep(1) # Sleep to avoid rate limiting

        if rsp.status_code != 200:
            self.logger.error(f"Failed to close position: {PositionId}. Response: {rsp.json()}")
        else:
            self.logger.info(f"Position {PositionId} closed. Order placed to close: {rsp.json()}")

        return rsp

    def limit(self, symbol, amount, buy=True, limit=None, stoploss_price=None):
        self.logger.debug(f"Placing limit order: {symbol} @ {limit} ({amount} contracts)")
        return self.base_order(symbol=symbol, 
                               amount=amount, 
                               buy=buy, 
                               limit=limit, 
                               stoploss_price=stoploss_price,
                               OrderType="Limit")

    def watch(self):
        self.logger.info("Starting change stream....")
        while True:
            db = Database().db
            
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
                #if saxo_helper.doc_older_than(doc, max_age=20):
                #    continue

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
        entry = position_base["OpenPrice"]
        amount = position_base["Amount"]
        BuySell = "Buy" if amount > 0 else "Sell"

        # Prepare stop loss order (oppoiste of current position)
        stoploss_price = self.get_stoploss_price(entry=entry,
                                                 stoploss=points,
                                                 BuySell=BuySell)
        sl_order = self.stoploss_order_existing(position=position, points_away=points)
        order = { "PositionId": pos_id, "Orders": sl_order }

        msg = f"Stop loss set to {stoploss_price} ({points} points) on {pos_id}"
        self.logger.info(msg)
        rsp = self.post(path="/trade/v2/orders", data=order)
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
        
        path = f"/trade/v2/orders/{orders}/?AccountKey={self.AccountKey}"
        rsp = self.post(path=path, data=None, method_override="DELETE")

        if rsp.status_code != 200:
            self.logger.error(f"Failed to cancel order(s): {rsp.json()}")
        else:
            self.logger.info(f"Orders cancelled: {rsp.json()}")
        
        return rsp

    #### ACCOUNTS ####
    def accounts(self):
        """ Get account details """
        rsp = self.get(path="/port/v1/accounts/me")
        return rsp.json()

    def account_update(self, AccountKey, DisplayName):
        """ Update account details """
        data = { "DisplayName": DisplayName }
        rsp = self.post(path=f"/port/v1/accounts/{AccountKey}",
                        data=data, method_override="PATCH")
        return rsp

    #### UTILS ####
    def instruments(self):
        """ Get all instruments """
        rsp = self.get(path=f"/ref/v1/instruments?AccountKey={self.AccountKey}&Keywords=Micro%202000&ExchangeId=CME&AssetTypes=ContractFutures")
        return rsp.json()

    def tickers(self) -> dict:
        """
            Get ticker configuration.

            This method will generate a .tickers file to cache the configuration.
            The file contains the Saxo configuration for the different indexes.
            It will calculate the 200-day moving average for each index.

        """
        filename = ".tickers"
        
        def modification_date(filename):
            t = os.path.getmtime(filename)
            return datetime.fromtimestamp(t)
        
        def get_ma():
            # Define tickers for RUT, NDX, SPX, DJIA
            tickers = {
                'RUT': '^RUT',
                'NDX': '^NDX',
                'SPX': '^GSPC',
                'DJIA': '^DJI'
            }

            # Fetch data for the past year to calculate the 200-day moving average
            data = {ticker: yf.download(symbol, period='1y', progress=False) for ticker, symbol in tickers.items()}

            # Calculate the 200-day moving average for each index
            ma_200 = {ticker: round(data[ticker]['Close'].rolling(window=200).mean().iloc[-1]) for ticker in tickers}
            return ma_200

        # Default ticker configuration
        tickers = {
            "NDX": {
                "Uic": 4912, # US Tech 100 NAS (tracking NDX Index)
                "AssetType": "CfdOnIndex",
                "stoploss_points": 25,
                #"200ma": 11946
            },
            "SPX": {
                "Uic": 4913, # US 500 (tracking SPX Index)
                "AssetType": "CfdOnIndex",
                "stoploss_points": 10,
                #"200ma": 3946
            },
            "DJIA": {
                "Uic": 4911, # US 30 Wall Street (tracking DJIA Index)
                "AssetType": "CfdOnIndex",
                "stoploss_points": 25,
                #"200ma": 35215
            },
            "RUT": {
                #"Uic": 31933, # iShares Russell 2000 ETF (tracking RUT Index)
                "Uic": 31933, # iShares Russell 2000 ETF (tracking RUT Index)
                "AssetType": "CfdOnEtf",
                "stoploss_points": 10,
                #"200ma": 170
            }
        }

        # if .200ma file is older than 1 day, update it
        if not os.path.exists(filename) or (datetime.now() - modification_date(filename)).days > 1:
            self.logger.info(f"Updating ticker config cache ({filename})..")

            # Update 200ma values
            ma_values = get_ma()
            for symbol in ma_values:
                tickers[symbol]["200ma"] = ma_values[symbol]

            # Dynamically set the RUT Futures Uic
            rut_uic = self.instruments()["Data"][0]["Identifier"]
            tickers["RUT"]["Uic"] = rut_uic

            tickers = utils.write_json(filename=filename, data=tickers)
        else:
            self.logger.info("Getting ticker config from cache (.ticker)")
            tickers = utils.read_json(filename=filename)

        self.logger.info(tickers)
        return tickers


# Create a SaxoHelper class that inherits from Saxo
class SaxoHelper():
    def __init__(self):
        # Create a logger instance for the class
        self.logger = logging.getLogger(__name__)
        self.tickers = utils.read_json(".tickers")
        
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
        # Get current UTC time
        now = datetime.now(tz=timezone.utc)

        # Set the timezone to UTC
        created_at = document["created_at"].replace(tzinfo=timezone.utc)

        # Get minutes since created_at and now
        diff = now - created_at 
        min_since_created_at = int(diff.total_seconds() / 60)

        # Check if min_since_post is greater than max_age
        if min_since_created_at > max_age:
            tid = document["tid"]
            msg = f"Tweet {tid} is {min_since_created_at} min. old. " \
                  f"Created {created_at} compared to {now}"
            self.logger.info(msg)
            return True

        self.logger.info(f"Tweet is fresh ({min_since_created_at} min. old)")
        return False
    
    def pprint_positions(self, positions:dict) -> None:
        """
            Pretty print position(s)

            Args:
                position (dict): Dictionary of positions
        """
        if positions["__count"] == 0:
            self.logger.info("No positions found.")
            return None
        
        data = []
        for p in positions["Data"]:
            pos_id = p["PositionId"]
            entry_date = p["PositionBase"]["ExecutionTimeOpen"]
            entry_date = datetime.strptime(entry_date, "%Y-%m-%dT%H:%M:%S.%fZ")
            entry_date = entry_date.replace(second=0, microsecond=0)

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
        print(df.to_string(index=False))

    def get_position_stop_details(self, position) -> dict:
        """
            Translates position data to a dict with stop loss details.


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

    def filter_positions(self, positions:dict, cfd_only:bool=True,
                         profit_only:bool=True, symbol:bool=None,
                         status:list=None) -> dict:
        # TODO: symbol is set as bool, should be str
        """
            Filter positions

            Args:
                positions (dict): Positions object
                cfd_only (bool): Show CFDs only
                profit_only (bool): Show positions in profit only
                symbol (str): Show positions for symbol only
                status (list): Show positions with status [Open, Closed, Working]

            Returns:
                dict: Filtered positions object

            Example:
                `{'__count': len(new_positions), 'Data': [..]}`
        """
        pos = positions["Data"]

        # Set default status
        if status is None: status = ["Open", "Closed", "Waiting"]

        idx_to_remove = []
        idx = 0
        for p in pos:
            p_base = p["PositionBase"]

            # CFD only
            if cfd_only and p_base["AssetType"] != "CfdOnIndex":
                idx_to_remove.append(idx)
            
            # Profit only
            if profit_only and p["PositionView"]["ProfitLossOnTrade"] <= 0:
                idx_to_remove.append(idx)

            # Symbol only
            sym = self.uic_to_symbol(p_base["Uic"])
            if symbol is not None and symbol != sym:
                idx_to_remove.append(idx)

            # Status filter
            if p_base["Status"] not in status:
                idx_to_remove.append(idx)

            # When a position is closed, another position in the opposite
            # direction is created. To avoid confusion, we hide these "opposite"
            # positions.
            if p_base["Status"] == "Closed":
                time_open = p_base["ExecutionTimeOpen"]
                time_close = p_base["ExecutionTimeClose"]
                dt_format = "%Y-%m-%dT%H:%M:%S.%fZ"
                time_open_dt = datetime.strptime(time_open, dt_format)
                time_close_dt = datetime.strptime(time_close, dt_format)
                # if open is older than close, hide it
                if time_open_dt > time_close_dt:
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
        uic = int(uic)
        for symbol, v in self.tickers.items():
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
        symbol = symbol.upper()
        try:
            ret = self.tickers[symbol]["Uic"]
            return ret
        except Exception:
            self.logger.error(f"symbol_to_uic failed for {symbol}")
            return None

    def get_stoploss(self, symbol):
        """
            TODO: Get actual stop loss instead of using hard coded values.
            Lookup default stoploss points for a symbol.
        """
        symbol = symbol.upper()
        try:
            stoploss_points = self.tickers[symbol]["stoploss_points"]
            return stoploss_points
        except Exception as e:
            # Setting arbitrary SL for unknown symbols
            self.logger.warning(f"Unknown symbol '{symbol}'. Setting SL to 9.")
            return 9

    def get_asset_type(self, uic):
        for ticker, info in self.tickers.items():
            if info['Uic'] == uic:
                return info['AssetType']
        return None
