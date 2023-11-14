import os
import sys
import time
import tweepy
import logging
from .db import Database
from .config import config
from termcolor import colored
from pymongo import DESCENDING
from pymongo.errors import DuplicateKeyError
from datetime import datetime
from zoneinfo import ZoneInfo
import time

class Tweets:
    """
        Class handling everything Twitter related.
    """
    def __init__(self, config):
        """
            Initialize the class.

            Hardcoded UID for NTLiveStream
        """
        # Create a logger instance for the class
        self.logger = logging.getLogger(__name__)

        # Authenticate to Twitter
        self.logger.info("Authenticating to Twitter...")
        self.client = tweepy.Client(
            consumer_key=config["TWITTER_CONSUMER_KEY"],
            consumer_secret=config["TWITTER_CONSUMER_SECRET"],
            bearer_token=config["TWITTER_BEARER_TOKEN"],
            access_token=config["TWITTER_TOKEN_KEY"],
            access_token_secret=config["TWITTER_TOKEN_SECRET"],
            wait_on_rate_limit=True)

        # Set the pagination_token to None
        self.pagination_token = None

        # Prepare for DB
        self.db = None

    def fetch(self, user_id="897502744298258432", max_results=5, user_auth=True, since_id=None) -> list:
        """
            Fetch tweet(s) from User Timeline

            Args:
                limit (int): Number of tweets to fetch
                user_id (str): User ID to fetch tweets from (default: NTLiveStream)
                user_auth (bool): Enable use user authentication, required for accessing private tweets
        """
        # Set max_results to min 5 or max 100
        max_results = min(100, max(5, max_results))
        uid = user_id

        # Get tweets
        self.logger.info(f"Fetching {max_results} tweets from {uid} User Timeline...")
        if since_id != None: self.logger.info(f"since_id: {since_id}")
        tweets = self.client.get_users_tweets(
            id=uid, 
            max_results=max_results,
            user_auth=user_auth,
            since_id=None,
            tweet_fields=["created_at", 'entities', 'author_id'])  # Entities contains tweet URL and other metadata

        return tweets

    def get_user_tweets(self, user_id="897502744298258432", max_results=5):
        # Connect to DB
        self.db = TweetsDB(config) if self.db is None else self.db
        
        # Fetch a batch of tweets from the user
        tweets = self.client.get_users_tweets(
            id=user_id,
            max_results=max_results,  # Adjust the batch size as needed
            tweet_fields=["created_at", 'entities', 'author_id'],
            user_auth=True,
            pagination_token=self.pagination_token  # Pass the pagination_token
        )

        # Check if no more tweets are available
        next_token = tweets.meta.get('next_token')
        if not next_token:
            logging.info("No more tweets available")
            sys.exit(0)

        # Process and store the tweets
        for tweet in tweets.data:
            # Store the tweet in the database or perform any desired actions
            self.db.add_tweet(tweet)

        # Set the pagination_token to fetch the next batch of tweets
        self.pagination_token = tweets.meta['next_token']

    def fetchall(self, user_id="897502744298258432"):
        """
            Fetch all tweets from User Timeline and add them into the DB.

            Args:
                user_id (str): User ID to fetch tweets from (default: NTLiveStream)
        """
        while True:
            self.get_user_tweets(user_id=user_id, max_results=100)
            self.rate_limit_handler()

    def me(self):
        me = self.client.get_me()
        self.logger.info(f"Authenticated as: {me.data.name} (@{me.data.username})")
        return me

    def rate_limit_handler(self, sleep=None):
        # Configure rate limit
        rate_limit_per_app = 15 * 60 / 10  # 10 requests per 15 minutes
        rate_limit_per_user = 15 * 60 / 5  #  5 requests per 15 minutes
        buffer = 2
        rate_limit_per_user = rate_limit_per_user + buffer
        
        # Used to avoid waiting when unit testing
        sleep = rate_limit_per_user if sleep is None else sleep

        self.logger.info(f"rate_limit_handler, waiting {sleep} seconds...")
        time.sleep(sleep)

    def pprint(self, tweet, inserted=False):
        """
            Print tweet nicely
        """
        if isinstance(tweet, dict):
            # Handle Tweet data dict
            try:
                _tid = str(tweet["tid"])
                _author_id = tweet["author_id"]
                _created_at = tweet["created_at"]
                _text = tweet["text"]
            except Exception as e:
                self.logger.error(f"Error parsing {e} from {tweet}")
                self.logger.error(tweet)
                return None
        else:
            # Handle tweepy.tweet.Tweet Object
            msg = "Parsing Tweet Objects are deprecated. Use dict instead."
            self.logger.warning(msg)
            return None
        
        # Coloring
        inserted_indicator = colored("[+]", "green") if inserted else colored("[-]", "red")
        tid_color = colored(_tid, "green")
        author_id_color = colored(_author_id, "blue")
        created_at_color = colored(_created_at, "red")
        text_color = colored(' '.join(_text.splitlines()), "white")

        # Output to log
        indicator = "[+]" if inserted else "[-]"
        self.logger.debug(f"{indicator} {_tid} {_author_id} {_created_at} {_text}")

        # Friendly print
        print(inserted_indicator, tid_color, author_id_color, created_at_color, text_color)

    def is_trading_hours(self, sleep=None):
        """
            Check if it's trading hours
        """
        # Set the timezone to US Central Time
        

        us_central_timezone = ZoneInfo('America/Chicago')

        # if not weekday, sleep for 1 hour
        if datetime.now(tz=us_central_timezone).weekday() >= 5:
            sleep_minutes = 60
            sleep = sleep_minutes if sleep is None else sleep  # Used to avoid waiting when unit testing
            self.logger.info(f"It's the weekend. Sleeping for {sleep} minutes..")
            time.sleep(sleep)
            return False

        # if time is not between 8:30 and 15:00 Central Time, sleep for 15 minutes
        now = datetime.now(tz=us_central_timezone)
        trading_start_time = now.replace(hour=8, minute=30, second=0, microsecond=0)
        trading_end_time = now.replace(hour=15, minute=0, second=0, microsecond=0)

        if now < trading_start_time or now > trading_end_time:
            sleep_minutes = 15
            sleep = sleep_minutes * 60 if sleep is None else sleep  # Used to avoid waiting when unit testing
            self.logger.info(f"It's not trading hours. Sleeping for {sleep} minutes..")
            time.sleep(sleep)
            return False
        
        return True
        
class TweetsDB:
    def __init__(self, config):
        self.logger = logging.getLogger(__name__)

        # Connect to MongoDB
        self.logger.info("Connecting to MongoDB...")
        self.db = Database()

        self.pprint = Tweets(config).pprint

    def get_tweet(self, tid:str):
        """
            Get a tweet from the database.
        """
        return  self.db.tweets.find_one({"tid": tid})

    def get_latest(self):
        """
            Get a tweet from the database.
        """
        doc =  self.db.tweets.find_one({}, sort=[("created_at", DESCENDING)])
        return doc
    
    def add_tweet(self, data):
        """
            Add a tweet to the database.
        """
        _data = None

        if isinstance(data, dict):
            # Handle basic dict data
            self.logger.debug("Handling basic dict data")
            data["tid"] = str(data["tid"])  # Ensure tid is always a string
            _data = data
        else:
            # Handle tweepy.tweet.Tweet Object
            self.logger.debug("Handling tweepy.tweet.Tweet Object")
            _data = {
                "tid": str(data.id),
                "author_id": str(data.author_id),
                "created_at": data.created_at,
                "text": data.text,
            }

        try:
            self.db.tweets.insert_one(_data)
            self.pprint(_data, inserted=True)
        except DuplicateKeyError:
            tid = _data["tid"]
            self.logger.debug(f"Tweet ({tid}) already exists")
        except Exception as e:
            self.logger.error(e)
