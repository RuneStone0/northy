import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from northy import signal
from northy.database import Tweets

t = signal.Signal()
db_tweets = Tweets().get()

def test_TradeSignal_get():
    """ 
        Test cases for TradeSignal.get()
    """
    # Invalid Twitter IDs
    assert t.get("123") == None
    assert t.get(123) == None
    assert t.get("") == None

    # Valid IDs, but not alerts
    assert t.get("1646967277659607054") == None

    # Valid IDs, with alerts
    ret = t.get("1646880502702301189")
    assert isinstance(ret, list)
    assert ret[0] == "SPX_FLAT"

    # Loop through all valid IDs, with alerts
    for i in db_tweets.aggregate([{"$match": {"alert": True}}]):
        assert isinstance(t.get(i["tid"]), list)

def test_TradeSignal_getall():
    # generate test cases for TradeSignal.getall()
    assert t.getall() == None

def test_TradeSignal_update():
    """ generate test cases for TradeSignal.update() """
    # Invalid Twitter IDs
    assert t.update("123") == None
    assert t.update(123) == None
    assert t.update("") == None

    # Loop through all sample set of tweets
    pipe = [
        {"$match": {"alert": True}},
        {"$sample": {"size": 10}}
    ]
    for i in db_tweets.aggregate(pipe):
        assert isinstance(t.update(i["tid"]), list)

def test_TradeSignal_updateall():
    # generate test cases for TradeSignal.updateall()
    assert t.updateall() == None

def test_TradeSignal_parse():
    # generate test cases for TradeSignal.parse()
    # Invalid Twitter IDs
    assert t.parse("123") == None
    assert t.parse(123) == None
    assert t.parse("") == None

    # Run parse() without update_db (False)
    pipe = [
        {"$match": {"alert": True}},
        {"$sample": {"size": 5}}
    ]
    for i in db_tweets.aggregate(pipe):
        assert isinstance(t.parse(i["tid"]), list)

    # Run parse() with update_db=True
    pipe = [
        {"$match": {"alert": True}},
        {"$sample": {"size": 5}}
    ]
    for i in db_tweets.aggregate(pipe):
        assert isinstance(t.parse(i["tid"], update_db=True), list)

def test_TradeSignal_parseall():
    # generate test cases for TradeSignal.parseall()
    assert t.parseall() == None

"""
def test_text_to_signal():
    # generate test cases for TradeSignal.text_to_signal()
    assert t.text_to_signal(tweet="invalid") == []
    assert t.text_to_signal(tweet={"empty": "dict"}) == []

    tweet_no_alert = db_tweets.find_one({"tid": "1646974851037405190"})  # Tweet without alert
    assert isinstance(t.text_to_signal(tweet=tweet_no_alert), list) == True

    ignored_tweet = db_tweets.find_one({"tid": "1645367498823352320"})  # Tweet on ignore list
    assert t.text_to_signal(tweet=ignored_tweet) == []

    # Tweet with alert
    valid_tweet = db_tweets.find_one({"tid": "1646877915961782274"})
    assert isinstance(t.text_to_signal(tweet=valid_tweet), list) == True
    assert t.text_to_signal(tweet=valid_tweet), list == ["SPX_SCALEOUT_IN_3809_OUT_4153_POINTS_344"]

    # Loop through all alert Tweets
    for i in db_tweets.find({"alert": True}):
        assert isinstance(t.text_to_signal(tweet=i), list) == True
"""

def test_is_trading_signal():
    # generate test cases for TradeSignal.is_trading_signal()
    assert t.is_trading_signal("ALERT: Closed 3rd scale $SPX long\nIN: 3809 OUT 4153+344") == True
    assert t.is_trading_signal("Market Dashboard:\n\nhttps://t.co/baFzYOi3V7") == False
    assert t.is_trading_signal("") == False

def test_TradeSignal_export():
    # generate test cases for TradeSignal.export()
    assert t.export() == None
    assert t.export(filename="signals", format="csv") == None

def test_TradeSignal_backtest():
    # generate test cases for TradeSignal.backtest()
    assert t.backtest() == None

"""
def test_TradeSignal_manual():
    # generate test cases for TradeSignal.manual()
    assert t.manual("123") == []

def test_TradeSignal_manualall():
    # generate test cases for TradeSignal.manualall()
    assert t.manualall() == []
"""

test_TradeSignal_export()