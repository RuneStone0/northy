from northy.noc import Noc
from northy.db import Database
from unittest.mock import patch
from unittest import mock

db = Database(production=False)
noc = Noc(wpndatabase_path='tests/noc/wpndatabase.db')
def test_simple():
    # Test with default path
    Noc(wpndatabase_path=None)

@patch('os.name', 'posix')
def test_check_os():
    noc = Noc(wpndatabase_path=None)
    noc.check_os()

def test_get_notifications():
    noc = Noc(wpndatabase_path='tests/noc/wpndatabase.db')
    notifications = noc.get_notifications()
    assert len(notifications) > 0

def test_process_notification():
    # Test all sample .db files in tests/noc
    files = [
        'wpndatabase.db',  # contains only tweets
        'wpndatabase-surfacex.db',  # contains no tweets (important for testing)
        'wpndatabase-windows10.db',
        'wpndatabase-meme.db', # contains tweets without text, only images
        'wpndatabase-whatsapp.db' # contains db rows that are un-parseable
    ]
    for file in files:
        noc = Noc(wpndatabase_path='tests/noc/'+file)
        noc.process_notification(db=db)

def test_process_notification_cache():
    # Test with a full cache
    noc.cache = list(range(1, 111))
    noc.process_notification(db=db)

def test_watch():
    # Make 5 iterations
    loops = mock.Mock(side_effect=[True]*5 + [False])
    noc.watch(loops=loops)
