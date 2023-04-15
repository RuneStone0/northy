from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from .utils import Utils
from .logger import get_logger

logger = get_logger("db", "db.log")

class Database:
    def __init__(self):
        u = Utils()
        config = u.get_config()
        client = MongoClient(config["mongodb_conn"])
        self.db = client.get_default_database()
        self.tweets = self.db[config["tweets_collection_name"]]

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
