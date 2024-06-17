import tempfile
import pytest
from datetime import datetime, timezone
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
    from northy.config import Config
    config = Config().config
    env_prod = config["PRODUCTION"]
    db = Database()
    assert db.production == env_prod

@pytest.fixture
def temp_folder():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir

def test_backup(temp_folder):
    # Perform the backup
    db = Database(production=False)
    result = db.backup(output_directory=temp_folder)
    assert result is None, "Backup should complete without errors"

def test_add_tweet():
    db = Database(production=False)

    # New Insert
    now = datetime.now(tz=timezone.utc)
    data = {"tid": "1234567890", "from": "test", "text": "test", "created_at": now}
    add_tweet = db.add_tweet(data)
    assert isinstance(add_tweet, bool)
    assert add_tweet == True

    # Test when tweet already exists
    add_tweet = db.add_tweet(data)
    assert isinstance(add_tweet, bool)
    assert add_tweet == False

    # created_at is missing
    data = {"tid": "1234567890", "from": "test", "text": "test"}
    add_tweet = db.add_tweet(data)
    assert isinstance(add_tweet, bool)
    assert add_tweet == False

    # created_at is not datetime
    now = datetime.now(tz=timezone.utc)
    data = {"tid": "1234567890", "from": "test", "text": "test", "created_at": ""}
    add_tweet = db.add_tweet(data)
    assert isinstance(add_tweet, bool)
    assert add_tweet == False

def test_get_tweet():
    db = Database(production=False)

    # Test when tweet exists
    data = db.get_tweet(tid="1547926636393218051")
    assert isinstance(data, dict)
    assert data["tid"] == "1547926636393218051"

    # Test when tweet does not exist
    data = db.get_tweet(tid="1234567891")
    assert data == None

def test_find():
    db = Database(production=False)

    # Test when tweet exists
    data = db.find({"tid": "1547926636393218051"}, limit=1)
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["tid"] == "1547926636393218051"

def test_aggregate():
    db = Database(production=False)

    # Test when tweet exists
    data = db.aggregate([{"$match": {"tid": "1547926636393218051"}}])
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["tid"] == "1547926636393218051"
