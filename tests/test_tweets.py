from northy.tweets import Tweets
from northy.config import config

tweets = Tweets(config=config)

def test_me():
    me = tweets.me()
    assert isinstance(me, tuple)
    assert me.data.username == "52544B"

def test_fetch():
    # Simple fetch
    data = tweets.fetch(user_auth=False, user_id="1366565625401909249")
    assert isinstance(data, tuple)

def test_fetch_with_since_id():
    # Fetch with since_id
    data = tweets.fetch(user_auth=False, user_id="1366565625401909249", since_id="1679125392462864384")
    assert isinstance(data, tuple)

def test_print():
    # Handling tweepy.tweet.Tweet Object
    # Un-authenticated fetch for WallStreetSilv, to avoid rate limiting
    response = tweets.fetch(user_auth=False, user_id="1366565625401909249")
    for tweet in response.data:
        assert tweets.pprint(tweet=tweet) == None

    # Handling Tweet data dict
    data = {
	  "tid": "1679125392462864384",
	  "author_id": "897502744298258432",
	  "created_at": "2023-07-12T13:47:44.000Z",
	  "text": "ALERT: Flat stopped $NDX\nRe-entry short    \nIN 15305- 25 pt stop"
	}
    assert tweets.pprint(tweet=data) == None
    assert tweets.pprint(tweet=data, inserted=True) == None

def test_print_errors():
    data = {
      "tid": "1234",
	  "text": "ALERT: Flat stopped $NDX\nRe-entry short    \nIN 15305- 25 pt stop",
      "author_id": "unittest",
      "created_at": "2023-07-12T13:47:44.000Z"
	}
    assert tweets.pprint(tweet=data) == None

def test_rate_limit_handler():
    assert tweets.rate_limit_handler(sleep=1) == None, "rate_limit_handler should complete without errors"

def test_is_trading_hours():
    tweets.is_trading_hours(sleep=1)

def test_get_user_tweets():
    tweets.get_user_tweets(user_id="897502744298258432", max_results=5)
