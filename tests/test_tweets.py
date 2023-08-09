import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from northy.tweets import Tweets
from northy.config import config

tweets = Tweets(config=config)

def test_me():
    me = tweets.me()
    assert isinstance(me, tuple)
    assert me.data.username == "52544B"

def test_fetch():
    # Un-authenticated fetch for WallStreetSilv, to avoid rate limiting
    data = tweets.fetch(user_auth=False, user_id="1366565625401909249")
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

"""
def test_is_trading_hours():
    assert isinstance(tweets.is_trading_hours(), bool)
"""

if __name__ == "__main__":
    test_me()
    test_fetch()
    test_print()
    pass
