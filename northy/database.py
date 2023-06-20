from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from .logger import get_logger
from .config import config
import bson
import mongomock

logger = get_logger("db", "db.log")

class Database:
    _instance = None  # Class-level variable to store the singleton instance
    db_name = "northy"
    tweets_collection_name = "tweets"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            return cls._instance
        else:
            return cls._instance

    def __init__(self):
        if not hasattr(self, 'client'):
            self.client = None
            self.init_db(production=config["PRODUCTION"])

    def init_db(self, production=False):
        logger.info("Connecting to DB..")
        if production == True:
            logger.critical("Using MongoDB Atlas (PRODUCTION MODE)")
            self.client = MongoClient(config["mongodb_conn"])
            self.db = self.client[self.db_name]
            self.tweets = self.db[self.tweets_collection_name]
            return self.client
        else:
            logger.warning("Using mongomock (testing mode)")
            self.client = mongomock.MongoClient()

            # create a database and collection
            self.db = self.client[self.db_name]
            self.tweets = self.db[self.tweets_collection_name]

            # load BSON data from file
            with open('backups/tweets.bson', 'rb') as f:
                data = bson.decode_all(f.read())

            # insert data into collection
            self.tweets.insert_many(data)
            return self.client

    def prepare_db(self):
        """
            Prepare the database by creating the collection and index.
        """
        print("Preparing Database")
        
        # create collection
        print("Creating tweets collection..")
        self.db().create_collection(self.tweets_collection_name)

        # create index
        print("Creating tid index on tweets collection..")
        self.tweets().create_index('tid', unique=True)

class Tweets:
    def __init__(self):
        db = Database()
        self.collection = db.tweets

    def get(self):
        return self.collection

    def add(self, data):
        """
            Add a tweet to the database.
        """
        try:
            r = self.collection.insert_one(data)
            logger.debug("Added Tweet to DB")
        except DuplicateKeyError:
            logger.debug("Tweet already exists")
        except Exception as e:
            logger.error(e)

