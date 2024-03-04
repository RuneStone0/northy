import os
from northy import utils
from northy.tweets import Tweets, TweetsDB
from northy.config import Config
config = Config().config

tweets = Tweets(config=config)

def get_mock_data(filename):
    u = utils.Utils()
    dir = os.path.dirname(__file__)
    file_path = f"mock_data/tweets/{filename}"
    path = os.path.join(dir, file_path)
    return u.read_json(path)

def test_me():
    me = tweets.me()
    assert isinstance(me, dict)
    assert me["username"] == "52544B"

def test_fetch():
    # Simple fetch
    data = tweets.fetch(user_auth=False, user_id="1366565625401909249")
    assert isinstance(data, dict)

def test_fetch_with_since_id():
    # Fetch with since_id
    data = tweets.fetch(user_auth=False,
                        user_id="1366565625401909249", 
                        since_id="1679125392462864384")
    assert isinstance(data, dict)

def test_pprint():
    # Handling Tweet data dict
    doc = get_mock_data("pprint2.json")
    assert tweets.pprint(tweet=doc) == None
    assert tweets.pprint(tweet=doc, inserted=True) == None

def test_print_errors():
    doc = get_mock_data("pprint3.json")
    assert tweets.pprint(tweet=doc) == None

def test_rate_limit_handler():
    assert tweets.rate_limit_handler(sleep=1) == None, "rate_limit_handler should complete without errors"

def test_tweet_throttle():
    # TODO
    #tweets.tweet_throttle()
    pass
    
def test_get_user_tweets():
    tweets.get_user_tweets(user_id="897502744298258432", max_results=5)

def test_test_latest():
    # Use mock DB
    config["PRODUCTION"] = False
    tdb = TweetsDB(config)
    out = tdb.get_latest()
    assert isinstance(out, dict)
