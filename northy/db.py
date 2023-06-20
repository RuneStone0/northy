from pymongo import MongoClient
import mongomock
import bson
from .config import Config
from .config import config
import logging

# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database(object):
    def __init__(self, connection_string=config["mongodb_conn"], database_name="northy", collection_name="tweets") -> None:
        self.logger = logger
        self.config = config

        self.database_name = database_name
        self.collection_name = collection_name
        self.connection_string = connection_string
        self.production = self.config["PRODUCTION"]

        self.db = None  # DB Object
        self.collection = None # DB Collection
        self.connect(production=self.production)

    def connect(self, production=False):
        self.logger.info("Connecting to DB..")
        if production == True:
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
