import sys
import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By

# Install latest version of Chrome
from webdriver_manager.chrome import ChromeDriverManager
ChromeDriverManager().install()

# Set the threshold for selenium to WARNING
from selenium.webdriver.remote.remote_connection import LOGGER as seleniumLogger
seleniumLogger.setLevel(logging.WARNING)

# Init driver
driver = webdriver.Chrome()

def Login():
    # Get Login Page
    driver.get("https://www.saxotrader.com/sim")
    
    # enter the username and password
    username = driver.find_element(By.NAME, "field_userid")
    password = driver.find_element(By.NAME, "field_password")
    user = "17470793"
    pwd = "4ueax1y3"
    username.send_keys(user)
    password.send_keys(pwd)

    # Click Login Button
    driver.find_element(By.NAME, 'button_login').click()

def GetBearerToken(liveEnvironment=False):
    token = None
    while token is None:
        # Loop until bearer token is found
        session_storage_name = "token_Live" if liveEnvironment else "token_Simulation"
        cmd = f"return sessionStorage.getItem('{session_storage_name}');"
        token = driver.execute_script(cmd)  # BEARER eyJhbGciOi...
        print(f"Token value: {token}")
        time.sleep(0.05)

    # Token is no longer None
    token = token.split(" ")[1]  # eyJhbGciOi...
    return token


if __name__ == "__main__":
    Login()
    token = GetBearerToken()
    time.sleep(60)
    driver.close()
    #sys.exit()
