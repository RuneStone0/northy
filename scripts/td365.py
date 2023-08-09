import sys
import os
import re
import requests
import dotenv
import pandas as pd
from pprint import pprint

dotenv_path = ".td365"

class t365:
    def __init__(self, username, password):
        self.T365_USER = username
        self.T365_PASS = password
        self.CLIENT_ID = dotenv.get_key(dotenv_path, "CLIENT_ID")
        self.ACCESS_TOKEN = dotenv.get_key(dotenv_path, "ACCESS_TOKEN")
        
        self.s = requests.Session()
        self.s.headers.update({"Authorization": f"Bearer {self.ACCESS_TOKEN}"})

        if self.auth_check() is False:
            print(f"+ Environment auth tokens expired. Re-authenticating..")
            self.__authenticate()

    def __authenticate(self):
        self.CLIENT_ID = self.__get_client_id()
        self.ACCESS_TOKEN = self.oauth_token()["access_token"]
        print(f"+ Successfully authenticated..")
        
        dotenv.set_key(dotenv_path, "ACCESS_TOKEN", self.ACCESS_TOKEN)
        dotenv.set_key(dotenv_path, "CLIENT_ID", self.CLIENT_ID)
        print(f"+ Storing auth token in environment variables")

    def __get_client_id(self):
        print(f"+ Getting client ID")
        rsp = self.s.get("https://traders.tradedirect365.com.au/static/js/bundle.js")
        x = re.findall(r'client_id:\s"(\w*)', rsp.text)
        client_id = x[0]
        return client_id

    def oauth_token(self):
        print(f"+ Getting OAuth Token")
        post_data = {
            "realm": "Username-Password-Authentication",
            "client_id": self.CLIENT_ID,
            "scope": "openid",
            "grant_type": "http://auth0.com/oauth/grant-type/password-realm",
            "username": self.T365_USER,
            "password": self.T365_PASS
        }
        rsp = self.s.post("https://tradedirect365.au.auth0.com/oauth/token", json=post_data)
        return rsp.json()

    def auth_check(self):
        rsp = self.s.get("https://portal-api.tradenation.com/TD365AU/user/123372/launch/")
        verdict = True if rsp.status_code == 200 else False
        return verdict

    def get_ct_url(self):
        rsp = self.s.get("https://portal-api.tradenation.com/TD365AU/user/123372/launch/")
        ct_finlogin = rsp.json()["url"]

        rsp = self.s.get(ct_finlogin)
        data = rsp.text
        print(data)

    def accounts(self):
        rsp = self.s.get("https://portal-api.tradenation.com/TD365AU/user/173041/accounts/")
        accounts = rsp.json()["results"]
        return accounts


class cloudtrade:
    def __init__(self):
        pass

    def w(self):
        import websocket

        websocket.enableTrace(True)
        ws = websocket.WebSocket()
        ws.connect("ws://echo.websocket.events/", origin="testing_websockets.com")
        ws.send("Hello, Server")
        print(ws.recv())
        ws.close()


if __name__ == '__main__':

    t = t365(username="runekristensen.la@gmail.com", password="vhe.jmn@GJA4ecn6xbg")
    accounts = t.accounts()
    #print(" ".join(df.columns))
    df = pd.DataFrame.from_dict(accounts)
    print(df[['id', 'platform', 'account', 'accountType', "currencySymbol", "balance", "ct_login_id", "ct_login_password"]])
    t.get_ct_url()

    #ct = cloudtrade()
    #ct.w()
