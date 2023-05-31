import time
import tweepy
from pymongo.errors import DuplicateKeyError
from .config import Config
from termcolor import colored
import logging

# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
uid = "897502744298258432"  # NTLiveStream

class Tweets:
    def __init__(self, db=None, config=None):
        # Placeholder for Class Variables
        self.db = db # DB Object
        self.tweets = None # DB Collection
        self.client = None # Twitter Client

        # Initialize Class
        self.config = Config().config

        # TODO: Move twitter out of init and only call it when needed
        self.init_twitter()

    def init_twitter(self):
        """ 
            Authenticate to Twitter App as specific user and initialize API object
        """
        logger.info("Authenticating to Twitter...")

        # Step 1: Obtain a User Context Bearer Token
        config = self.config
        self.client = tweepy.Client(
            consumer_key=config["consumer_key"],
            consumer_secret=config["consumer_secret"],
            access_token=config["access_key"],
            access_token_secret=config["access_secret"],
            wait_on_rate_limit=True
        )
        #me = self.client.get_me()
        #logger.info(f"Authenticated to Twitter as: {me.data.name} ({me.data.username})")

    def __print_nice(self, tweet, inserted=False):
        """ 
            Takes Tweets from DB and prints them nicely
        """
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        tid = colored(tweet["tid"], "green")
        created_at = colored(tweet["created_at"].strftime("%Y-%m-%d %H:%M:%S"), "red")
        text = tweet["text"].replace('\n', '')
        inserted_indicator = colored("[+]", "green") if inserted else colored("[-]", "red")
        print(inserted_indicator, now, tid, created_at, text)
            
    def insert_tweet(self, data):
        """
            Insert Tweet into DB
        """
        try:
            r = self.db.tweets.insert_one(data)
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
            tweet_fields=["created_at", 'entities'])  # Entities contains tweet URL and other metadata

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
        """
            Watch for new tweets and add them into the DB.
        """
        exponential_backoff = 1
        while True:
            try:
                self.fetch(limit=1)
                time.sleep(5)  # 1 second caused API violation. Trying with 5 seconds..
                exponential_backoff = 1
            except Exception as e:
                logger.error(e)
                logger.error("Error fetching tweets. Sleeping for %d seconds.." % exponential_backoff)
                time.sleep(exponential_backoff)
                exponential_backoff *= 2

def test_cases():
    t = Tweets()
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
    # TODO: Change to CLI tool
    # TODO: Implement caching, to avoid attempting to insert into db every time
    t = Tweets()
    t.watcher()
