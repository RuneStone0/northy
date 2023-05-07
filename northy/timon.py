import time
import tweepy
from pymongo.errors import NetworkTimeout
from datetime import datetime
from termcolor import colored
from . import TradeSignal
from . import SaxoTrader
from .utils import Utils
from .database import Database, Tweets
from .logger import get_logger
import sys

u = Utils()
logger = get_logger("timon", "timon.log")
config = u.get_config()

class Timon:
    _instance = None  # Class-level variable to store the singleton instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'api'):
            self.api = None
            self.__authenticate()

        # MongoDB
        db = Database()
        self.db_tweets = db.tweets

    def __authenticate(self):
        """ 
            Authenticate to Twitter App as specific user and initialize API object
        """
        logger.info("Authenticating to Twitter...")
        auth = tweepy.OAuthHandler(config["consumer_key"], config["consumer_secret"])
        auth.set_access_token(config["access_key"], config["access_secret"])
        self.api = tweepy.API(auth, wait_on_rate_limit=True)

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

    def readdb(self, username, limit=10):
        pipeline = [
            {"$sort": { "created_at": -1 }},        # Get latest tweets
            {"$match": { "username": username }},   # Filter by username
            {"$limit": limit},                      # Limit output
            {"$sort": { "created_at": 1 }}          # Reverse output order so oldest -> latest
        ]
        for tweet in self.db_tweets.aggregate(pipeline):
            self.__print_nice(tweet)

    def fetch(self, username="NTLiveStream", limit=1) -> list:
        """
            Fetch tweet(s) from User Timeline and add them into the DB.
        """
        logger.info(f"Fetching tweets from {username} limit {limit}")
        signal = TradeSignal.Signal()
        tweets = Tweets()

        try:
            tweet_timeline = self.api.user_timeline(screen_name=username, count=limit)
        except Exception as e:
            logger.error(e)
            u.prowl(message=f"Timon.py: {e}")
        
        ret_data = list()
        for tweet in tweet_timeline:
            # Prepare Tweet data
            is_alert = signal.is_trading_signal(tweet.text)
            tid = str(tweet.id)
            data = {
                "tid": tid,
                "username": tweet.user.screen_name,
                "created_at": tweet.created_at,
                "text": tweet.text,
                "alert": is_alert,
            }

            # Add TradeSignal
            data["signals"] = signal.text_to_signal(tweet=data)

            # Add Tweet to DB
            self.__print_nice(data)
            tweets.add(data)
            ret_data.append(data)
            
        return ret_data

    def watch_tweets(self):
        """
            Watch for new Tweets every 5 seconds and add them into the DB.
        """
        while True:
                # Sleep to avoid rate limit
                sleep_time = 5
                logger.debug(f"Sleeping for {sleep_time} seconds...")
                time.sleep(sleep_time)

                # If market is closed, skip
                if not u.is_market_open():
                    continue

                # Fetch latest tweet
                tweet = self.fetch(limit=1)[0]

                if tweet["alert"]:
                    # send prowl notification
                    u.prowl(tweet["text"])

                    # Add TradeSignal
                    signal = TradeSignal.Signal()
                    signals = signal.update(tweet["tid"])

                    # Execute TradeSignal
                    for signal in signals:
                        # Must be initialized every time, otherwise trade() might fail
                        # TODO: handle re-authentication within the trade() method
                        saxo = SaxoTrader.Saxo()
                        saxo.trade(signal)

    def watch_alerts(self):
        """
            Watch for new Tweets inserted into the DB. If a new Tweet is a trade alert, send a notification and execute the trade.
        """
        def _stream():
            logger.info("Setting up change stream...")
            pipeline = [{ '$match': { 'operationType': { '$in': ['update', 'insert'] } } }]
            stream = self.db_tweets.watch(pipeline=pipeline)
            logger.debug("Stream ready. Waiting for changes to happen..")
            return stream
        
        def _process(tweet):
            tid = tweet["tid"]

            # Skip if not an alert
            if not tweet["alert"]:
                logger.debug("{} is not an alert".format(tid))
                return

            logger.info(f"Alert detected: {tid} {tweet['text']}")

            # send prowl notification
            u.prowl(tweet["text"])

            # Execute TradeSignal
            for signal in tweet["signals"]:
                # Must be initialized every time, otherwise trade() might fail
                # TODO: handle re-authentication within the trade() method
                saxo = SaxoTrader.Saxo()
                orders = saxo.trade(signal)
                logger.info("Successfully executed trade(s):", u.json_to_string(orders))
        
        while True:
            try:
                for change in _stream():
                    operationType = change["operationType"]
                    _id = change["documentKey"]["_id"]
                    logger.debug(f"Change ({operationType}) detected on document ID: {_id}")

                    # Get document that changed
                    tweet = self.db_tweets.find_one({"_id": _id})
                    
                    _process(tweet)
                    logger.info("Done processing. Waiting for next change...")
            except NetworkTimeout as e:
                logger.error("Stream network timeout. Retrying...")
                pass
            except KeyboardInterrupt:
                logger.info("KeyboardInterrupt detected. Exiting...")
                sys.exit(0)
            except Exception as e:
                logger.error(e)
                pass


