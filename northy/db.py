import logging
from pymongo import MongoClient
from .config import config
import mongomock
import bson

class Database(object):
    def __init__(self, connection_string=None, database_name="northy", collection_name="tweets", production=True) -> None:
        # Create a logger instance for the class
        self.logger = logging.getLogger(__name__)
        
        self.connection_string = config["MONGODB_CONN"]
        self.production = production
        self.database_name = database_name
        self.collection_name = collection_name

        self.db = None  # DB Object
        self.collection = None # DB Collection
        self.__connect()

    def __connect(self):
        self.logger.info("Connecting to DB..")
        if self.production:
            self.logger.critical("Using MongoDB Atlas (PRODUCTION MODE)")
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            self.tweets = self.db[self.collection_name]
            return self.client
        else:
            self.logger.warning("Using mongomock (testing mode)")
            self.client = mongomock.MongoClient()

            # create a database and collection
            self.db = self.client[self.database_name]
            self.tweets = self.db[self.collection_name]

            # load BSON data from file
            with open('backups/tweets.bson', 'rb') as f:
                data = bson.decode_all(f.read())

            # insert data into collection
            self.tweets.insert_many(data)
            return self.client
