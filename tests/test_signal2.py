from northy.signal2 import Signal
from northy.db import Database
from northy.logger import setup_logger
setup_logger()

db = Database(production=False)
signal = Signal(production=False)

def test_signal2_get():
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

def test_signal2_getall():
    # generate test cases for TradeSignal.getall()
    assert signal.getall() == None

def test_signal2_update():
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

def test_signal2_updateall():
    # generate test cases for TradeSignal.updateall()
    assert signal.updateall() == None

def test_signal2_parse():
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

def test_signal2_parseall():
    # generate test cases for TradeSignal.parseall()
    assert signal.parseall() == None

def test_text_to_signal():
    # generate test cases for TradeSignal.text_to_signal()
    assert signal.text_to_signal(tweet="invalid") == []
    assert signal.text_to_signal(tweet={"empty": "dict"}) == []

    tweet_no_alert = db.tweets.find_one({"tid": "1646974851037405190"})  # Tweet without alert
    assert isinstance(signal.text_to_signal(tweet=tweet_no_alert), list) == True

    ignored_tweet = db.tweets.find_one({"tid": "1645367498823352320"})  # Tweet on ignore list
    assert signal.text_to_signal(tweet=ignored_tweet) == []

    # Tweet with alert
    valid_tweet = db.tweets.find_one({"tid": "1646877915961782274"})
    assert isinstance(signal.text_to_signal(tweet=valid_tweet), list) == True
    assert signal.text_to_signal(tweet=valid_tweet), list == ["SPX_SCALEOUT_IN_3809_OUT_4153_POINTS_344"]

    # Loop through all alert Tweets
    for i in db.tweets.find({"alert": True}):
        assert isinstance(signal.text_to_signal(tweet=i), list) == True

def test_is_trading_signal():
    # generate test cases for TradeSignal.is_trading_signal()
    assert signal.is_trading_signal("ALERT: Closed 3rd scale $SPX long\nIN: 3809 OUT 4153+344") == True
    assert signal.is_trading_signal("Market Dashboard:\n\nhttps://signal.co/baFzYOi3V7") == False
    assert signal.is_trading_signal("") == False

def test_signal2_export():
    # generate test cases for TradeSignal.export()
    assert signal.export() == None
    assert signal.export(filename="signals", format="csv") == None

def test_signal2_backtest():
    # generate test cases for TradeSignal.backtest()
    assert signal.backtest() == None

def test_get_closest_symbols():
    ndx_numbers = [3713]
    spx_numbers = [11348]
    rut_numbers = [1703]
    dija_numbers = [30932]

    for i in ndx_numbers:
        print(signal.get_closest_symbols(i))
        print(signal.get_closest_symbols(i).index("NDX"))
        
        assert signal.get_closest_symbols(i) == ["NDX"]
    
    # generate test cases for TradeSignal.get_closest_symbols()
    assert signal.get_closest_symbols("SPX") == ["SPX"]
    assert signal.get_closest_symb
   
"""
def test_signal2_manual():
    # generate test cases for TradeSignal.manual()
    assert signal.manual("123") == []

def test_signal2_manualall():
    # generate test cases for TradeSignal.manualall()
    assert signal.manualall() == []
"""
