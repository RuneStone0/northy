import os
import time
import tweepy
import logging
from termcolor import colored
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

logger = logging.getLogger(__name__)

class Helper:
    def __init__(self) -> None:
        self.last_request = None

    def pprint(self, tweet, inserted=False):
        """
            Print tweet nicely
        """
        _tid = str
        _author_id = None
        _created_at = None
        _text = None

        if isinstance(tweet, dict):
            # Handle Tweet data dict
            logger.debug("Handling Tweet data dict")
            try:
                _tid = str(tweet["tid"])
                _author_id = tweet["author_id"]
                _created_at = tweet["created_at"]
                _text = tweet["text"]
            except Exception as e:
                print("Error:", e)
                print(tweet)
        else:
            # Handle tweepy.tweet.Tweet Object
            logger.info("Handling tweepy.tweet.Tweet Object")
            try:
                _tid = tweet.id
                _author_id = tweet.author_id
                _created_at = tweet.created_at
                _text = tweet.text
            except Exception as e:
                print("Error:", e)
                print(tweet)
        
        # Coloring
        inserted_indicator = colored("[+]", "green") if inserted else colored("[-]", "red")
        tid_color = colored(_tid, "green")
        author_id_color = colored(_author_id, "blue")
        created_at_color = colored(_created_at, "red")
        text_color = colored(' '.join(_text.splitlines()), "white")

        print(inserted_indicator, tid_color, author_id_color, created_at_color, text_color)

    def rate_limit_handler(self):
        rate_limit_per_app = 15 * 60 / 10  # 10 requests per 15 minutes
        rate_limit_per_user = 15 * 60 / 5  #  5 requests per 15 minutes
        print(f"rate_limit_handler, waiting {rate_limit_per_user} seconds...")
        time.sleep(rate_limit_per_user)

class Tweets:
    """
        Class handling everything Twitter related.
    """
    def __init__(self, config):
        # Hardcoded UID for NTLiveStream
        self.uid = "897502744298258432"

        # Authenticate to Twitter
        logger.info("Authenticating to Twitter...")
        self.client = tweepy.Client(
            consumer_key=config["TWITTER_CONSUMER_KEY"],
            consumer_secret=config["TWITTER_CONSUMER_SECRET"],
            bearer_token=config["TWITTER_BEARER_TOKEN"],
            access_token=config["TWITTER_TOKEN_KEY"],
            access_token_secret=config["TWITTER_TOKEN_SECRET"],
            wait_on_rate_limit=True)

    def search(self, query="from:BarackObama", tweet_fields=['author_id', 'created_at'], max_results=100):
        """
            Search for tweets matching a query and return them as a list of dicts.
        """
        tweets = self.client.search_recent_tweets(
            query=query, 
            tweet_fields=tweet_fields,
            max_results=max_results)

        if tweets.data == None:
            logger.info(f"No data found matching query '{query}'")
            return []
        
        return tweets.data

    def prepare_data(self, tweet):
        """
            Prepare Tweet data for DB insertion
        """
        tid = str(tweet.id)
        data = {
            "tid": tid,
            "created_at": tweet.created_at, 
            "text": tweet.text,
        }
        return data

    def fetch(self, limit=5, user_auth=True, rate_limit=False) -> list:
        """
            Fetch tweet(s) from User Timeline and add them into the DB.

            Args:
                limit (int): Number of tweets to fetch
                user_auth (bool): Enable use user authentication, required for accessing private tweets
                rate_limit (bool): Pause after each request to avoid rate limit
        """
        # Set max_results to min 5 or max 100
        max_results = min(100, max(5, limit))
        uid = self.uid

        # Get tweets
        logger.info(f"Fetching {max_results} tweets from {uid} User Timeline...")
        tweets = self.client.get_users_tweets(
            id=uid, 
            max_results=max_results,
            user_auth=user_auth,
            tweet_fields=["created_at", 'entities', 'author_id'])  # Entities contains tweet URL and other metadata

        if rate_limit:
            self.rate_limit_handler()
        
        return tweets

    def fetchall(self):
        from .config import config
        db = TweetsDB(connection_string=config["mongodb_conn"])
        helper = Helper()
        
        pagination_token = None  # Set the initial pagination_token to None
        
        while True:
            # Fetch a batch of tweets from the user
            tweets = self.client.get_users_tweets(
                id=self.uid,
                max_results=100,  # Adjust the batch size as needed
                tweet_fields=["created_at", 'entities', 'author_id'],
                user_auth=True,
                pagination_token=pagination_token  # Pass the pagination_token
            )

            # Check if no more tweets are available
            next_token = tweets.meta.get('next_token')
            print("next_token:", next_token)
            if not next_token:
                break

            # Process and store the tweets
            for tweet in tweets.data:
                print(tweet)
                # Store the tweet in the database or perform any desired actions
                db.add_tweet(tweet)

            # Set the pagination_token to fetch the next batch of tweets
            pagination_token = tweets.meta['next_token']
            helper.rate_limit_handler()

    def me(self):
        me = self.client.get_me()
        logger.info(f"Authenticated as: {me.data.name} (@{me.data.username})")
        return me

    def test(self):
        c = tweepy.Client(
            consumer_key=self.consumer_key,
            consumer_secret=self.consumer_secret,
            access_token=self.access_key,
            access_token_secret=self.access_secret,
            wait_on_rate_limit=True
        )
        print(c)
        data = c.get_users_tweets(id="897502744298258432", max_results=5, user_auth=True)
        print(data)

        rate_limit = 15 * 60 / 10  # 10 requests per 15 minutes, per user
        self.logger.info(f"Wainting {rate_limit} seconds...")
        time.sleep(rate_limit)

    def print(tweet, inserted=False):
        """
            Print Tweet Objects nicely
        """
        tid_color = colored(tweet.id, "green")
        created_at_color = colored(tweet.created_at, "red")
        author_id = colored(tweet.author_id, "blue")
        inserted_indicator = colored("[+]", "green") if inserted else colored("[-]", "red")
        print(inserted_indicator, tid_color, author_id, created_at_color, tweet.text)

class TweetsDB:
    def __init__(self, config):
        self.logger = logging.getLogger(__name__)

        self.client = MongoClient(config["mongodb_conn"])
        self.db = self.client["northy"]
        self.collection = self.db["tweets"]

    def get_tweet(self, tid:str):
        """
            Get a tweet from the database.
        """
        return self.collection.find_one({"tid": tid})
    
    def add_tweet(self, data):
        """
            Add a tweet to the database.
        """
        helper = Helper()
        _data = None

        if isinstance(data, dict):
            # Handle basic dict data
            logger.debug("Handling basic dict data")
            data["tid"] = str(data["tid"])  # Ensure tid is always a string
            _data = data
        else:
            # Handle tweepy.tweet.Tweet Object
            logger.debug("Handling tweepy.tweet.Tweet Object")
            _data = {
                "tid": str(data.id),
                "author_id": str(data.author_id),
                "created_at": data.created_at,
                "text": data.text,
            }

        try:
            r = self.collection.insert_one(_data)
            helper.pprint(_data, inserted=True)
        except DuplicateKeyError:
            self.logger.debug("Tweet already exists")
            helper.pprint(_data, inserted=False)
        except Exception as e:
            self.logger.error(e)

