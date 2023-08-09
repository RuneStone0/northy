import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from northy.db import Database
from northy.logger import setup_logger
setup_logger()

def test_db_mock():
    db = Database(production=False)
    assert db.client != None
    assert db.db != None
    assert db.tweets != None
    assert isinstance(db.tweets.find_one(), dict)
    assert db.production == False

def test_db_prod():
    db = Database(production=True)
    assert db.client != None
    assert db.db != None
    assert db.tweets != None
    assert isinstance(db.tweets.find_one(), dict)
    assert db.production == True

def test_db_env():
    from northy.config import config
    env_prod = config["PRODUCTION"]
    db = Database()
    assert db.production == env_prod

if __name__ == "__main__":
    test_db_mock()
    test_db_prod()
    test_db_env()
