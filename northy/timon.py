import time
import tweepy
import pyprowl
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from dotenv import dotenv_values
from termcolor import colored
from . import TradeSignal
from . import SaxoTrader
import click

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
            # Indicate that new Tweet was added
            return True
        except DuplicateKeyError:
            # Indicate that Tweet already exists
            return False

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

    def fetch(self, username="NTLiveStream", limit=1):
        """
            Fetch tweet(s) from User Timeline and add them into the DB.
        """
        response = self.api.user_timeline(screen_name=username, count=limit)

        signal = TradeSignal.Signal()
        for tweet in response:
            is_alert = signal.is_trading_signal(tweet.text)
            tid = str(tweet.id)
            data = {
                "tid": tid,
                "username": tweet.user.screen_name,
                "created_at": tweet.created_at,
                "text": tweet.text,
                "alert": is_alert
            }

            # Add Tweet to DB
            new_tweet = self.__add_tweet_to_db(data)

            if limit > 1:
                self.__print_nice(data)
            else:
                return data

    def watch(self):
        saxo = SaxoTrader.Saxo()

        last_tid = None
        while True:
            try:
                # Sleep to avoid rate limit
                time.sleep(5)

                # Fetch latest tweet
                tweet = self.fetch()

                # If not a new tweet, print dot
                if last_tid == tweet["tid"]:
                    click.echo(".", nl=False)
                    continue
                
                # Process new tweet
                self.__print_nice(tweet)
                last_tid = tweet["tid"]

                if tweet["alert"]:
                    # send prowl notification
                    self.prowl(tweet["text"])

                    # Add TradeSignal
                    signal = TradeSignal.Signal()
                    signals = signal.update(tweet["tid"])

                    # Execute TradeSignal
                    for signal in signals:
                        saxo.trade(signal)

            except Exception as e:
                print(f"Exception {e}")
                print(f"Going to sleep for 1 min.")
                time.sleep(60)

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

