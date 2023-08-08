import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from northy.signal2 import Signal
from northy.db import Database

production = False
db = Database(production=production)
signal = Signal()

def test_TradeSignal_get():
    """ 
        Test cases for TradeSignal.get()
    """
    # Invalid Twitter IDs
    assert signal.get("123") == None
    assert signal.get(123) == None
    assert signal.get("") == None

    # Valid IDs, but not alerts
    assert signal.get("1646967277659607054") == None

    # Valid IDs, with alerts
    ret = signal.get("1646880502702301189")
    assert isinstance(ret, list)
    assert ret[0] == "SPX_FLAT"

    # Loop through all valid IDs, with alerts
    for i in db.tweets.aggregate([{"$match": {"alert": True}}]):
        assert isinstance(signal.get(i["tid"]), list)

def test_TradeSignal_getall():
    # generate test cases for TradeSignal.getall()
    assert signal.getall() == None

def test_TradeSignal_update():
    """ generate test cases for TradeSignal.update() """
    # Invalid Twitter IDs
    assert signal.update("123") == None
    assert signal.update(123) == None
    assert signal.update("") == None

    # Loop through all sample set of tweets
    pipe = [
        {"$match": {"alert": True}},
        {"$sample": {"size": 10}}
    ]
    for i in db.tweets.aggregate(pipe):
        assert isinstance(signal.update(i["tid"]), list)

def test_TradeSignal_updateall():
    # generate test cases for TradeSignal.updateall()
    assert signal.updateall() == None

def test_TradeSignal_parse():
    # generate test cases for TradeSignal.parse()
    # Invalid Twitter IDs
    assert signal.parse("123") == None
    assert signal.parse(123) == None
    assert signal.parse("") == None

    # Run parse() without update_db (False)
    pipe = [
        {"$match": {"alert": True}},
        {"$sample": {"size": 5}}
    ]
    for i in db.tweets.aggregate(pipe):
        assert isinstance(signal.parse(i["tid"]), list)

    # Run parse() with update_db=True
    pipe = [
        {"$match": {"alert": True}},
        {"$sample": {"size": 5}}
    ]
    for i in db.tweets.aggregate(pipe):
        assert isinstance(signal.parse(i["tid"], update_db=True), list)

def test_TradeSignal_parseall():
    # generate test cases for TradeSignal.parseall()
    assert signal.parseall() == None

"""
def test_text_to_signal():
    # generate test cases for TradeSignal.text_to_signal()
    assert signal.text_to_signal(tweet="invalid") == []
    assert signal.text_to_signal(tweet={"empty": "dict"}) == []

    tweet_no_alert = db_tweets.find_one({"tid": "1646974851037405190"})  # Tweet without alert
    assert isinstance(signal.text_to_signal(tweet=tweet_no_alert), list) == True

    ignored_tweet = db_tweets.find_one({"tid": "1645367498823352320"})  # Tweet on ignore list
    assert signal.text_to_signal(tweet=ignored_tweet) == []

    # Tweet with alert
    valid_tweet = db_tweets.find_one({"tid": "1646877915961782274"})
    assert isinstance(signal.text_to_signal(tweet=valid_tweet), list) == True
    assert signal.text_to_signal(tweet=valid_tweet), list == ["SPX_SCALEOUT_IN_3809_OUT_4153_POINTS_344"]

    # Loop through all alert Tweets
    for i in db_tweets.find({"alert": True}):
        assert isinstance(signal.text_to_signal(tweet=i), list) == True
"""

def test_is_trading_signal():
    # generate test cases for TradeSignal.is_trading_signal()
    assert signal.is_trading_signal("ALERT: Closed 3rd scale $SPX long\nIN: 3809 OUT 4153+344") == True
    assert signal.is_trading_signal("Market Dashboard:\n\nhttps://signal.co/baFzYOi3V7") == False
    assert signal.is_trading_signal("") == False

def test_TradeSignal_export():
    # generate test cases for TradeSignal.export()
    assert signal.export() == None
    assert signal.export(filename="signals", format="csv") == None

def test_TradeSignal_backtest():
    # generate test cases for TradeSignal.backtest()
    assert signal.backtest() == None

"""
def test_TradeSignal_manual():
    # generate test cases for TradeSignal.manual()
    assert signal.manual("123") == []

def test_TradeSignal_manualall():
    # generate test cases for TradeSignal.manualall()
    assert signal.manualall() == []
"""

test_TradeSignal_export()

if __name__ == "__main__":
    test_TradeSignal_get()
    #test_TradeSignal_getall()
    #test_TradeSignal_update()
    #test_TradeSignal_updateall()
    #test_TradeSignal_parse()
    #test_TradeSignal_parseall()
    # test_text_to_signal()
    #test_is_trading_signal()
    #test_TradeSignal_export()
    #test_TradeSignal_backtest()
    # test_TradeSignal_manual()
    # test_TradeSignal_manualall()