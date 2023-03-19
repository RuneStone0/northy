import time
import tweepy
import pyprowl
from tweepy import OAuthHandler, StreamingClient
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from dotenv import dotenv_values
from colorama import init, Fore, Back, Style
from termcolor import colored
from . import TradeSignal

config = dotenv_values(".env")
database_name = "northy"
tweets_collection_name = "tweets"

class Timon:
    def __init__(self):
        # APIv1 - Authenticate as a user
        auth = tweepy.OAuthHandler(config["consumer_key"],config["consumer_secret"])
        auth.set_access_token(config["access_key"],config["access_secret"])

        self.api = tweepy.API(auth, wait_on_rate_limit=True)
        
        # MongoDB
        client = MongoClient(config["mongodb_conn"])
        self.db = client[database_name]
        self.tweets_collection = self.db[tweets_collection_name]

        # Prepare DB
        self.db[tweets_collection_name].create_index('tid', unique=True)

        

    def __print_nice(self, tweet):
        """ 
            Takes Tweets from DB and prints them nicely
        """
        now = colored(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "yellow")
        tid = colored(tweet["tid"], "green")
        username = colored(tweet["username"], "cyan")
        created_at = colored(tweet["created_at"], "red")
        text = tweet["text"].replace('\n', '')
        print(now, tid, created_at, username, text)

    def __add_tweet_to_db(self, data):
        try:
            self.tweets_collection.insert_one(data)
            tid =  data["tid"]
            #print(f"Addeing {tid}")
        except DuplicateKeyError:
            #print("Duplicated Key")
            pass

    def readdb(self, username=None, limit=10):
        pipeline = []

        # Get latest tweets
        pipeline.append({"$sort": { "created_at": -1 }})  
        
        # Filter by username
        if username != None:
            pipeline.append({"$match": { "username": username }})
        
        # Limit output
        pipeline.append({"$limit": limit})
        
        # Reverse output order so oldest -> latest
        pipeline.append({"$sort": { "created_at": 1 }})

        for i in self.tweets_collection.aggregate(pipeline):
            self.__print_nice(i)

    def watch(self, username="NTLiveStream", limit=1):
        """
            This will watch for new Tweets in User Timeline and add them into the DB.
            Change limit to fetch older Tweets.
        """
        print("Getting", limit, "latest tweets from", username)
        response = self.api.user_timeline(screen_name=username, count=limit)

        signal = TradeSignal.Signal()
        for tweet in response:
            data = {
                "tid": str(tweet.id),
                "username": tweet.user.screen_name,
                "created_at": tweet.created_at,
                "text": tweet.text,
                "alert": signal.is_trading_signal(tweet.text)
            }

            self.__print_nice(data)
            self.__add_tweet_to_db(data)

    def prowl(self, message):
        p = pyprowl.Prowl(config["prowl_api_key"])

        try:
            p.verify_key()
            #print("Prowl API key successfully verified!")
        except Exception as e:
            #print("Error verifying Prowl API key: {}".format(e))
            exit()

        try:
            p.notify(event="Alert", description=message, priority=0, url='http://www.example.com', appName='Northy')
            print("Notification successfully sent to Prowl!")
        except Exception as e:
            print("Error sending notification to Prowl: {}".format(e))

    def pushalert(self):
        """
            This will watch for new ALERT Tweets and..
              > Send Prowl notification
              > Add 'alert' bool flag to document
        """
        latest_id = None
        while True:
            # Get latest tweet ID
            tweet = [i for i in self.tweets_collection.find({}).sort("created_at", -1).limit(1)][0]
            self.__print_nice(tweet)

            # New Tweet detected
            if latest_id != tweet["tid"]:
                # Update last seen Tweet ID
                latest_id = tweet["tid"]

                # If alert is detected
                if "ALERT" in tweet["text"]:
                    # Send prowl notification
                    self.prowl(tweet["text"])

                    # Add 'alert' bool flag to document
                    tweet["alert"] = True
                    self.tweets_collection.update_one({"tid": tweet["tid"]}, {"$set": tweet}, upsert=True)

            time.sleep(1)

    def datafeed(self):
        from tvDatafeed import TvDatafeed, Interval
        #tv = TvDatafeed(config["TW_USER"], config["TW_PASS"])
        tv = TvDatafeed()

        tickers = [
            {"symbol": "NDX", "exchange": "NASDAQ"},
            {"symbol": "SPX", "exchange": "SP"},
            {"symbol": "US100", "exchange": "CAPITALCOM"},
            {"symbol": "US500", "exchange": "CAPITALCOM"},
            {"symbol": "RUT", "exchange": "TVC"},
        ]
        for ticker in tickers:
            _symbol = ticker["symbol"]
            _exchange = ticker["exchange"]
            collection = f"twfeed-{_exchange}-{_symbol}"
            self.db[collection].create_index('dt', unique=True)

            minutes_in_day = 1440
            minutes_in_day = 100
            df = tv.get_hist(symbol=_symbol, exchange=_exchange, interval=Interval.in_1_minute, n_bars=minutes_in_day*2, extended_session=True)
            for date, row in df.T.items():
                d = { "dt": date, "h": row["high"], "l": row["low"], "o": row["open"], "c": row["close"] }
                try:
                    self.db[collection].insert_one(d)
                    print(f"+ Inserting {_exchange}:{_symbol} {d}")
                except DuplicateKeyError:
                    print(f"+ Already exist {_exchange}:{_symbol} {d}")
                    pass

