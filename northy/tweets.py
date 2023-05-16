import ast
import time
import bson
import tweepy
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
import mongomock
from datetime import datetime
from dotenv import dotenv_values
from termcolor import colored
import logging

# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

uid = "897502744298258432"  # NTLiveStream

class Timon:
    def __init__(self):
        # Placeholder for Class Variables
        self.db = None # DB Object
        self.tweets = None # DB Collection
        self.client = None # Twitter Client

        # Initialize Class
        self.get_config()
        self.init_db(production=self.config["PRODUCTION"])
        self.init_twitter()

    def get_config(self):
        """
            Get config from .env file. If already fetched, return cached version.
        """
        logger.debug("Getting config...")
        self.config = dotenv_values(".env")

        # Convert string to bool
        self.config["PRODUCTION"] = ast.literal_eval(self.config["PRODUCTION"])

        return self.config

    def init_twitter(self):
        """ 
            Authenticate to Twitter App as specific user and initialize API object
        """
        logger.info("Authenticating to Twitter...")
        #auth = tweepy.OAuthHandler(config["consumer_key"], config["consumer_secret"])
        #auth.set_access_token(config["access_key"], config["access_secret"])
        #self.api = tweepy.API(auth, wait_on_rate_limit=True)

        # Step 1: Obtain a User Context Bearer Token
        #api = tweepy.Client(config["bearer_token"])
        config = self.config
        self.client = tweepy.Client(
            consumer_key=config["consumer_key"],
            consumer_secret=config["consumer_secret"],
            access_token=config["access_key"],
            access_token_secret=config["access_secret"],
            wait_on_rate_limit=True
        )
        me = self.client.get_me()
        #print(me)
        print(f"Authenticated to Twitter as: {me.data.name} ({me.data.username})")

    def init_db(self, production=False):
        logger.info("Connecting to DB..")
        db_name = "northy"
        tweets_collection_name = "tweets"
        if production == True:
            logger.warning("Using MongoDB Atlas (PRODUCTION MODE)")
            client = MongoClient(self.config["mongodb_conn"])
            self.db = client[db_name]
            self.tweets = self.db[tweets_collection_name]
        else:
            logger.warning("Using mongomock (testing mode)")
            client = mongomock.MongoClient()

            # create a database and collection
            self.db = client[db_name]
            self.tweets = self.db[tweets_collection_name]

            # load BSON data from file
            with open('backups/tweets.bson', 'rb') as f:
                data = bson.decode_all(f.read())

            # insert data into collection
            self.tweets.insert_many(data)

    def __print_nice(self, tweet, inserted=False):
        """ 
            Takes Tweets from DB and prints them nicely
        """
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        tid = colored(tweet["tid"], "green")
        created_at = colored(tweet["created_at"].strftime("%Y-%m-%d %H:%M:%S"), "red")
        text = tweet["text"].replace('\n', '')
        if inserted:
            inserted_indicator = colored("[+]", "green")
            print(inserted_indicator, now, tid, created_at, text)
        else:
            inserted_indicator =  colored("[-]", "red")
            print(inserted_indicator, now, tid, created_at, text)
            
    def insert_tweet(self, data):
        """
            Insert Tweet into DB
        """
        try:
            r = self.tweets.insert_one(data)
            self.__print_nice(data, inserted=True)
        except DuplicateKeyError:
            logger.debug("Tweet already exists")
            self.__print_nice(data, inserted=False)
        except Exception as e:
            logger.error(e)
            self.__print_nice(data, inserted=False)

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

    def fetch(self, limit=100) -> list:
        """
            Fetch tweet(s) from User Timeline and add them into the DB.
        """
        # Set max_results to min 5 or max 100
        max_results = min(100, max(5, limit))

        # Get tweets
        tweets = self.client.get_users_tweets(
            id=uid, 
            max_results=max_results, 
            user_auth=True, 
            tweet_fields=["created_at"])

        # Set the maximum number of results to process
        ret_limit_left = limit

        for tweet in tweets.data:
            # Prepare Tweet data
            data = self.prepare_data(tweet)

            # Add Tweet to DB
            self.insert_tweet(data)

            ret_limit_left -= 1
            if ret_limit_left == 0:
                return 

    def fetchall(self):
        """
            Fetch all tweets (up to 3,200) from User Timeline and add them into the DB.
        """
        # Set the maximum number of results per page
        max_results = 100

        def __get_tweets(next_token=None):
            # Get the first page of tweets
            tweets = self.client.get_users_tweets(uid,
                                                user_auth=True,
                                                max_results=max_results,
                                                pagination_token=next_token,
                                                tweet_fields=["created_at"])

            # Iterate over the tweets and print them
            for tweet in tweets.data:
                # Prepare Tweet data
                data = self.prepare_data(tweet)

                # Add Tweet to DB
                self.insert_tweet(data)

            return tweets

        # Get the first page of tweets
        tweets = __get_tweets()

        # If there is a next page, get the next page of tweets
        next_token = tweets.meta.get("next_token")
        while next_token is not None:
            tweets = __get_tweets(next_token=next_token)

            # Get the next token
            next_token = tweets.meta.get("next_token")

    def watcher(self):
        while True:
            self.fetch(limit=1)
            time.sleep(1)

def test_cases():
    t = Timon()
    # Fetching all tweets
    t.fetchall()

    # Fetching tweets with limit
    t.fetch(limit=1)
    t.fetch(limit=2)
    t.fetch(limit=5)
    t.fetch(limit=20)
    t.fetch(limit=100)
    t.fetch(limit=200)

    # Watching tweets
    t.watch_tweets()

if __name__ == '__main__':
    t = Timon()
    #t.fetchall()

    #t.fetch(limit=1)
    #t.fetch(limit=2)
    #t.fetch(limit=5)
    #t.fetch(limit=20)
    #t.fetch(limit=100)
    #t.fetch(limit=200)

    t.watcher()
    


