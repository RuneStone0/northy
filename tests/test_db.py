import tempfile
import pytest
from northy.db import Database

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

@pytest.fixture
def temp_folder():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

def test_backup(temp_folder):
    from northy.config import config

    # Perform the backup
    connection_string = config["MONGODB_CONN"]
    db = Database(connection_string=connection_string)
    result = db.backup(output_directory=temp_folder)
    assert result is None, "Backup should complete without errors"

def test_add_tweet():
    db = Database(production=False)

    # New Insert
    data = {"tid": "1234567890", "from": "test", "text": "test"}
    add_tweet = db.add_tweet(data)
    assert isinstance(add_tweet, bool)
    assert add_tweet == True

    # Test when tweet already exists
    add_tweet = db.add_tweet(data)
    assert isinstance(add_tweet, bool)
    assert add_tweet == False

    add_tweet = db.add_tweet("")