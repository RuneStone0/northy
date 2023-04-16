import time
import tweepy
from datetime import datetime
from termcolor import colored
from . import TradeSignal
from . import SaxoTrader
from .utils import Utils
from .database import Database, Tweets
from .logger import get_logger

u = Utils()
logger = get_logger("timon", "timon.log")
config = u.get_config()

class Timon:
    def __init__(self):
        # MongoDB
        db = Database()
        self.db_tweets = db.tweets

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

    def __twitter_api(self):
        """ 
            Authenticate to Twitter and return API object
        """
        # APIv1 - Authenticate as a user
        logger.info("Authenticating to Twitter...")
        auth = tweepy.OAuthHandler(config["consumer_key"], config["consumer_secret"])
        auth.set_access_token(config["access_key"], config["access_secret"])
        api = tweepy.API(auth, wait_on_rate_limit=True)
        return api

    def readdb(self, username, limit=10):
        pipeline = [
            {"$sort": { "created_at": -1 }},        # Get latest tweets
            {"$match": { "username": username }},   # Filter by username
            {"$limit": limit},                      # Limit output
            {"$sort": { "created_at": 1 }}          # Reverse output order so oldest -> latest
        ]
        for tweet in self.db_tweets.aggregate(pipeline):
            self.__print_nice(tweet)

    def fetch(self, username="NTLiveStream", limit=1):
        """
            Fetch tweet(s) from User Timeline and add them into the DB.
        """
        signal = TradeSignal.Signal()
        tweets = Tweets()
        api = self.__twitter_api()
        for tweet in api.user_timeline(screen_name=username, count=limit):
            # Prepare Tweet data
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
            tweets.add(data)

            # TODO: Move this out of fetch() into the function that's using it
            if limit > 1:
                self.__print_nice(data)
            
            return data

    def watch(self):
        last_tid = None
        while True:
            try:
                # Sleep to avoid rate limit
                time.sleep(5)

                # Fetch latest tweet
                tweet = self.fetch()

                # If not a new tweet, print dot
                if last_tid == tweet["tid"]:
                    #click.echo(".", nl=False)
                    continue
                
                # Process new tweet
                self.__print_nice(tweet)
                last_tid = tweet["tid"]

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


            except Exception as e:
                # TODO: use logger
                print(f"Exception {e}")
                print(f"Going to sleep for 1 min.")
                time.sleep(60)

    def watch2(self):
        pipeline = [{ '$match': { 'operationType': { '$in': ['update', 'insert'] } } }]
        logger.info("Setting up change stream...")

        try:
            resume_token = u.read_json(filename="temp/resume_token.json")
        except Exception as e:
            logger.debug("No resume token found")
        
        try:
            print("Setting up stream using resume token: ", u.json_to_string(resume_token))
            stream = self.db_tweets.watch(pipeline=pipeline, resume_after=resume_token)
            u.write_json(data=stream.resume_token, filename="temp/resume_token.json")
            print("Stream setup complete. Writing resume token to file.")
        except Exception as e:
            print("Failed to resume stream, setting up new stream")
            stream = self.db_tweets.watch(pipeline=pipeline)
            u.write_json(data=stream.resume_token, filename="temp/resume_token.json")
            print("Stream setup complete. Writing resume token to file.")

        for change in stream:
            operationType = change["operationType"]
            _id = change["documentKey"]["_id"]
            print(f"Change ({operationType}) detected on document ID: {_id}")
            tweet = self.db_tweets.find_one({"_id": _id})

            # Skip if not an alert
            print(tweet["text"])
            if not tweet["alert"]:
                print(tweet["tid"], "is not an alert")
            else:
                print(tweet["tid"], "Alert detected, sending notification and executing trade(s)...")
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
                    orders = saxo.trade(signal)
                    print("Successfully executed trade(s):", u.json_to_string(orders))
