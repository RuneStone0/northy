import tempfile
import pytest
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

if __name__ == "__main__":
    test_db_mock()
    test_db_prod()
    #test_db_env()
    #test_backup()  # only works by calling pytest from the command line
    pass
