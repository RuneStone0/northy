import uuid
import logging
import requests
from requests.auth import HTTPBasicAuth

logging.basicConfig()
logger = logging.getLogger()
logger.setLevel(logging.INFO)

conf = {
  "AppName": "Sim Timon",
  "AppKey": "c96263868bf745aa9ea697b6aef0f500",
  "AuthorizationEndpoint": "https://sim.logonvalidation.net/authorize",
  "TokenEndpoint": "https://sim.logonvalidation.net/token",
  "GrantType": "Code",
  "OpenApiBaseUrl": "https://gateway.saxobank.com/sim/openapi/",
  "RedirectUrls": [
    "http://timon.rtk-cv.dk",
    "http://localhost/"
  ],
  "AppSecret": "aa2b0b4d070e4950b576b9c024a69914"
}

client_id = conf["AppKey"]
redirect_uri = conf["RedirectUrls"][1]
state = str(uuid.uuid4())
user = "17470793"
pwd = "4ueax1y3"
basic = HTTPBasicAuth(conf["AppKey"], conf["AppSecret"])

# https://www.developer.saxo/openapi/learn/oauth-authorization-code-grant

def parse_url(url):
    from urllib.parse import urlparse, parse_qs
    parsed_url = urlparse(url)
    return parse_qs(parsed_url.query)

def auth_request():
    auth_endpoint = conf["AuthorizationEndpoint"]
    url = f"{auth_endpoint}?response_type=code&client_id={client_id}&state={state}&redirect_uri={redirect_uri}"
    logger.info(f"GET {url}")
    r = requests.get(url, allow_redirects=False)
    #logger(r.content)
    redirect_url = r.headers["Location"]
    return redirect_url

def manual_auth(redirect_url):
    """ Authenticate "manually" using user/pass """
    s = requests.session()

    # Login
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {"field_userid": user, "field_password": pwd}
    logger.info(f"POST {redirect_url}")
    r = s.post(redirect_url, data=data, headers=headers, allow_redirects=False)
    post_login_url = r.headers["Location"]

    # Post login, fetch auth code
    logger.info(f"GET {post_login_url}")
    r = s.get(post_login_url, allow_redirects=False)
    auth_code_url = r.headers["Location"]
    auth_code = parse_url(auth_code_url)["code"][0]
    logger.debug(f"Auth Code: {auth_code}")
    return auth_code

def access_token(auth_code, grant_type):
    url = conf["TokenEndpoint"]
    data = { "redirect_uri": redirect_uri, "grant_type": grant_type}

    if grant_type == "authorization_code":
        data["code"] = auth_code
    elif grant_type == "refresh_token":
        data["refresh_token"] = auth_code
    
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    logger.info(f"POST {url}")
    r = requests.post(url, auth=basic, data=data, headers=headers)
    access_token = r.json()
    logger.debug("Access Token: "+access_token["access_token"]+" Refresh Token: "+access_token["refresh_token"])
    return access_token

if __name__ == "__main__":
    # Step 1, make auth request
    redirect_url = auth_request()

    # Step 2, bypass manual auth process
    auth_code = manual_auth(redirect_url)

    # Step 3, get access token
    access_obj = access_token(auth_code, grant_type="authorization_code")
    
    # Step 4, refresh token
    access_token(access_obj["refresh_token"], grant_type="refresh_token")

