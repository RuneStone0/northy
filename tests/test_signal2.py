from northy.signal2 import Signal, SignalHelper
from northy.db import Database
from northy.logger import setup_logger
setup_logger()

db = Database(production=False)
signal = Signal(production=False)
signal_helper = SignalHelper()

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

def test_signal2_parse_update_false():
    # Run parse() without update_db (False)
    pipe = [
        {"$match": {"alert": True}},
        {"$sample": {"size": 5}}
    ]
    for i in db.tweets.aggregate(pipe):
        assert isinstance(signal.parse(i["tid"]), dict)

def test_signal2_parse_update_true():
    # Run parse() with update_db=True
    pipe = [
        {"$match": {"alert": True}},
        {"$sample": {"size": 5}}
    ]
    for i in db.tweets.aggregate(pipe):
        assert isinstance(signal.parse(i["tid"], update_db=True), dict)

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

    # Invalid action in tweet
    invalid_tweet = {
        "tid": "1577295787616264194",
        "text": "ALERT: 2nd $SPX\nIN 3576 OUT 3766 +190",
        "alert": True,
    }
    out = signal.text_to_signal(tweet=invalid_tweet)
    assert out == []

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
    # Create new instance of Signal class (and copy of DB)
    __signal = Signal(production=False)

    # Insert tweet with mis-matching signals into DB
    tweet = {
        "tid": "123456",
        "text": "ALERT: 2nd $SPX\nIN 3576 OUT 3766 +190",
        "alert": True,
        "signals":        [ "SPX_SCALEOUT_IN_3576_OUT_0000_POINTS_190" ],
        "signals_manual": ["SPX_SCALEOUT_IN_3576_OUT_3766_POINTS_190" ]
    }
    __signal.db.tweets.insert_one(tweet)

    # Run all backtests
    assert __signal.backtest(manual_review=False) == None

    # Clean up
    __signal.db.tweets.delete_one({"tid": "123456"})

def test_find_INOUT():
    # Get all alerts, where text contains "IN" more than 2 times
    pipeline = [
        {
            '$match': {
                'alert': True,
                'text': {
                    '$regex': 'IN',
                    '$options': 'i'
                }
            }
        },
        {
            '$addFields': {
                'in_count': {
                    '$size': {
                        '$split': ['$text', 'IN']
                    }
                }
            }
        },
        {
            '$match': {
                'in_count': {
                    '$gt': 2
                }
            }
        },
        {
            '$project': {
                'text': 1
            }
        }
    ]
    for doc in db.tweets.aggregate(pipeline):
        res = signal_helper.find_INOUT(doc["text"])
        assert isinstance(res, list) == True

def test_normalize_text():
    # Preload helper function for better performance
    normalize_text = signal_helper.normalize_text

    # Fetch only the necessary fields to reduce data transfer
    projection = {"text": 1}

    # Attempt to normalize all alerts
    for doc in db.tweets.find({"alert": True}, projection):
        text = doc["text"]
        out = normalize_text(text)
        assert isinstance(out, str) == True

def test_find_SCALE_POINTS():
    # Get all alerts, where text contains "SCALE" more than 2 times
    query = {
        'alert': True,
        'text': { '$regex': 'SCALE', '$options': 'i' }
    }

    # Fetch only the necessary fields to reduce data transfer
    projection = {"text": 1}

    # Preload the signal helper function for better performance
    find_SCALE_POINTS = signal_helper.find_SCALE_POINTS

    # Test all scales in DB
    for doc in db.tweets.find(query, projection):
        text = doc["text"]
        res = find_SCALE_POINTS(text)
        assert isinstance(res, int) == True

    # Test specific cases
    cases = [
        {
            "in": "CLOSED FINAL SCALE $NDX LONG |IN 11060 OUT 13250 +2190",
            "expected": 2190
        },
        {
            "in": "CLOSED 1 SCALE $SPX SHORT |  |IN 4193 OUT 4045 +148",
            "expected": 148
        },
        {
            "in": "CLOSED 3RD SCALE $NDX ADD-ON | IN 11818 OUT 12760 + 942",
            "expected": 942
        },
    ]
    for case in cases:
        assert signal_helper.find_SCALE_POINTS(case["in"]) == case["expected"]

def test_get_closest_symbols():
    numbers = [
        # Multiple numbers
        [3713,11348],
        [1703,30932],
        [3713,11348,1703,30932],
        
        # Single numbers
        [3713], # SPX
        [11348], # NDX
        [35675], # DJIA
        [1703] # RUT
    ]
    for num in numbers:
        out = signal_helper.get_closest_symbols(num)
        print(out)
        assert isinstance(out, dict) == True

def test_parseall():
    signal.parseall()

def test_watch_log():
    # Get a sample of tweets without alerts
    pipeline = [
        { "$match": { "alert": { "$exists": False } } }, # Get tweets where "alerts" it not set (yet)
        { "$sort": { "created_at": 1 } }, # Sort, oldest first
        { "$sample": { "size": 30 } } # Get 10 random tweets
    ]
    db = Database(production=False)
    for doc in db.tweets.aggregate(pipeline):
        data = signal.parse(tid=doc["tid"], update_db=False)
        assert signal.watch_log(doc=doc, data=data) == None 

def test_refresh_backlog():
    signal.refresh_backlog(limit=100)

def test_manual():
    # Non-existing tweet
    assert signal.manual(tid="1234567890") == None

    # Tweet on ignore list
    assert signal.manual(tid="1557516667357380608") == None

    # Tweet with no `signal`and `signal_manual` fields
    assert signal.manual(tid="1548003680191844355") == None

