import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from northy.prowl import Prowl

API_KEY = "***SECRET***"

def test_prowl_invalid_key():
    API_KEY = "invalid"
    prowl = Prowl(API_KEY=API_KEY)
    assert prowl.PROWL_API_KEY == API_KEY
    assert prowl.test() == False

def test_prowl_valid_key():
    prowl = Prowl(API_KEY=API_KEY)
    assert prowl.test() == True

def test_prowl_send():
    prowl = Prowl(API_KEY=API_KEY)
    prowl.send(
        "Test message from northy.prowl.py",
        priority=0,
        url="https://www.google.com/")

if __name__ == "__main__":
    test_prowl_invalid_key()
    test_prowl_valid_key()
    test_prowl_send()