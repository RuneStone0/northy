import os
import sys
import time
import tweepy
import logging
from .db import Database
from .config import config
from northy.color import colored
from datetime import timedelta
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
            # we do this, so we can interact with tweets as dict, regardless 
            # if they are coming from Twitter API or MongoDB
            return_type=dict,
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
        next_token = tweets["meta"]["next_token"]
        if not next_token:
            logging.info("No more tweets available")
            sys.exit(0)

        # Process and store the tweets
        for tweet in tweets["data"]:
            # Store the tweet in the database or perform any desired actions

            self.db.add_tweet(tweet)

        # Set the pagination_token to fetch the next batch of tweets
        self.pagination_token = next_token

    def fetchall(self, user_id="897502744298258432"):
        """
            Fetch all tweets from User Timeline and add them into the DB.

            Args:
                user_id (str): User ID to fetch tweets from (default: NTLiveStream)
        """
        while True:
            self.get_user_tweets(user_id=user_id, max_results=5)
            #self.get_user_tweets(user_id=user_id, max_results=100)
            self.rate_limit_handler()

    def me(self) -> dict:
        me = self.client.get_me()["data"]
        name, username = me["name"], me["username"]
        self.logger.info(f"Authenticated as: {name} (@{username})")
        return me

    def rate_limit_handler(self, sleep=None):
        # Configure rate limit
        rate_limit_per_app = 15 * 60 / 10  # 10 requests per 15 minutes
        rate_limit_per_user = 15 * 60 / 5  #  5 requests per 15 minutes
        buffer = 2
        rate_limit_per_user = rate_limit_per_user + buffer
        
        # Used to avoid waiting when unit testing
        sleep = rate_limit_per_user if sleep is None else sleep

        self.logger.info(f"rate_limit_handler, waiting {int(sleep/60)} minutes...")
        time.sleep(sleep)

    def pprint(self, tweet, inserted=False):
        """
            Print tweet nicely
        """
        # Parse Tweet data
        _tid = str(tweet["id"])
        _created_at = tweet["created_at"]
        _text = tweet["text"]
        _text = ' '.join(_text.splitlines())
        
        # Coloring
        inserted_indicator = colored("[+]", "green") if inserted else colored("[-]", "red")
        tid_color = colored(_tid, "green") if inserted else colored(_tid, "red")
        created_at_color = colored(_created_at, "white")
        text_color = colored(_text, "blue")

        # Output to log
        self.logger.debug(f"{inserted_indicator} {tid_color} {created_at_color} {text_color}")

    def tweet_throttle(self) -> None:
        """
            Throttle when to look for new tweets.
            These functions are based on analysis found in
            /temp/mongodb_charts_queries/*
        """
        # Set the timezone to US Central Time
        us_central_timezone = ZoneInfo('America/Chicago')
        now = datetime.now(tz=us_central_timezone)

        def __saturday():
            """ Skip Saturday """
            if now.weekday() == 5:
                # sleep until Sunday
                sleep_time = (now.replace(hour=23, minute=59, second=59) - now).total_seconds()
                time.sleep(sleep_time)
                self.logger.info(f"It's Saturday. Sleep until Sunday..")
        __saturday()

        def __sunday():
            """ On Sunday, only look for tweets between 17:00 and 18:00 """
            sunday = now.weekday() == 6
            if sunday and now.hour == 17:
                # It's Sunday and 17:00
                # We check for new tweets every 10min.
                sleep_time = 10
                self.logger.info(f"It's {now.weekday()} on {now.hour}th hour. Sleeping for {sleep_time} minutes..")
                time.sleep(sleep_time * 60)
            elif sunday and now.hour < 17:
                # It's Sunday, but not 17:00 yet, sleep until then
                sleep_time = (now.replace(hour=17, minute=0, second=0) - now).total_seconds()
                self.logger.info(sleep_time)
                self.logger.info("It's Sunday but not 17:00 yet. Sleeping {sleep_time} seconds..")
            elif sunday and now.hour > 17:
                # It's Sunday, but past 17:00
                # Sleep until Monday
                sleep_time = (now.replace(hour=23, minute=59, second=59) - now).total_seconds()
                time.sleep(sleep_time)
                self.logger.info(f"It's Sunday, but past 17:00. Sleep until Monday..")
            else:
                # It's not Sunday
                pass
        __sunday()

        def __weekday():
            # Its not a weekday, move on
            if now.weekday() >= 5:
                return None

            # Its a weekday! We generally check for tweets all day, except
            # between 16:00 and 01:00 we'll only check once every hour
            weekday_msg = f"It's a weekday on {now.hour}th hour."
            off_hours = "We only check for new Tweets every hour betwwen 16-01"
            if now.hour >= 16 or now.hour <= 1:
                # We check for new tweets every full hour
                sleep_time = (timedelta(hours=1) - timedelta(minutes=now.minute, seconds=now.second)).total_seconds()
                sleep_msg = f"Sleeping for {int(sleep_time / 60)} minutes.."
                self.logger.info(f"{weekday_msg} {off_hours} {sleep_msg}")
                time.sleep(sleep_time)
            else:
                # We don't have any delays on weekdays during peak hours
                self.logger.debug(f"{weekday_msg} Go look for tweets..")
        __weekday()
        
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
    
    def add_tweet(self, tweet):
        """
            Add a tweet to the database.
        """
        created_at = datetime.strptime(tweet["created_at"], '%Y-%m-%dT%H:%M:%S.%fZ')
        _data = {
            "tid": str(tweet["id"]),
            "author_id": str(tweet["author_id"]),
            "created_at": created_at,
            "text": tweet["text"],
        }

        try:
            self.db.tweets.insert_one(_data)
            self.pprint(_data, inserted=True)
        except DuplicateKeyError:
            tid = _data["tid"]
            self.logger.debug(f"Tweet {tid} already exists")
        except Exception as e:
            self.logger.error(e)
