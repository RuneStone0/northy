from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from .utils import Utils
from .logger import get_logger
import bson
import mongomock

logger = get_logger("db", "db.log")
config = Utils().get_config()

testing = True

class Database:
    def __init__(self):
        self.init_db(testing=config["PRODUCTION"])

    def init_db(self, testing=True):
        if testing == "True":
            logger.critical("Using MongoDB Atlas (PRODUCTION MODE)")
            client = MongoClient(config["mongodb_conn"])
            self.db = client["tweets"]
            self.tweets = self.db[config["tweets_collection_name"]]
            return client
        else:
            logger.warning("Using mongomock (testing mode)")
            client = mongomock.MongoClient()

            # create a database and collection
            self.db = client['northy']
            self.tweets = self.db['tweets']

            # load BSON data from file
            with open('backups/tweets.bson', 'rb') as f:
                data = bson.decode_all(f.read())
            
            # insert data into collection
            self.tweets.insert_many(data)
            return client

    def prepare_db(self):
        """
            Prepare the database by creating the collection and index.
        """
        print("Preparing Database")
        
        # create collection
        print("Creating tweets collection..")
        self.db().create_collection(self.config["tweets_collection_name"])

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
            self.collection.insert_one(data)
            logger.debug("Added Tweet to DB")
        except DuplicateKeyError:
            logger.debug("Tweet already exists")

