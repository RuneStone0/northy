import os
import logging
import shutil
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from datetime import datetime
from northy.color import colored
from northy.config import Config
from northy.secrets_manager import SecretsManager
import mongomock
import bson

sm = SecretsManager()
sm.read()

class Database(object):
    def __init__(self, connection_string=None, production:bool=None,
                 database_name="northy", collection_name="tweets") -> None:
        # Create a logger instance for the class
        self.logger = logging.getLogger(__name__)
        config = Config().config
        URI = sm.get_dict()["MONGODB"]["URI"]
        self.connection_string = URI if connection_string is None else connection_string
        self.production = config["PRODUCTION"] if production is None else production
        self.database_name = database_name
        self.collection_name = collection_name

        self.db = None  # DB Object
        self.__connect()

    def __connect(self):
        if self.production:
            self.logger.critical("Connecting to MongoDB (PRODUCTION)")
            self.client = MongoClient(self.connection_string)
            self.db = self.client[self.database_name]
            self.tweets = self.db[self.collection_name]
            return self.client
        else:
            self.logger.warning("Connecting to mongomock (TESTING)")
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

    def backup(self, output_directory="backups", cluster_name="northy", collection_name="tweets"):
        """
            Backup the tweets collection to a BSON file.
        """
        # Because this class is used for testing and is often connected to the
        # mongomock client, we want to force a switch to the prod db before
        # backing up the data.
        self.logger.info("Switching to production database for backup")
        self.production = True
        self.__connect()
        collection = self.db[collection_name]

        # Create the backups directory if it doesn't exist
        os.makedirs(output_directory, exist_ok=True)
        
        # Get the current date and time
        current_datetime = datetime.now()
        timestamp = current_datetime.strftime("%Y-%m-%d-%H-%M-%S")
        
        # Create a folder for the backup
        backup_folder = os.path.join(output_directory, timestamp, cluster_name)
        backup_file_path = os.path.join(backup_folder, f"{collection_name}.bson")
        os.makedirs(backup_folder, exist_ok=True)
        
        # Retrieve all documents from the collection
        # Save the documents to a BSON file
        with open(backup_file_path, 'wb') as file:
            for doc in collection.find():
                file.write(bson.BSON.encode(doc))
        self.logger.info(f"Backup of '{collection.name}' collection saved to '{backup_file_path}'")

        # Prepare mock db for testing
        # Copy backups/$folderName/tweets.bson to backups/tweets.bson
        shutil.copy(os.path.join(backup_folder, 'tweets.bson'), os.path.join('backups', 'tweets.bson'))

    def pprint(self, tweet, inserted=False):
        """
            Print tweet nicely
        """
        # Parse Tweet data
        _tid = str(tweet["tid"])
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

    def add_tweet(self, data) -> bool:
        """
            Add a tweet to the database.
        """
        # Check if created_at exists
        if "created_at" not in data.keys():
            self.logger.error("created_at is missing")
            return False
        
        # Check if created_at is datetime format
        if not isinstance(data["created_at"], datetime):
            self.logger.error("created_at is not datetime")
            return False
                
        # Attempt to insert tweet into database
        try:
            self.db.tweets.insert_one(data)
            self.pprint(data, inserted=True)
            return True
        except DuplicateKeyError:
            tid = data["tid"]
            self.logger.debug(f"Tweet {tid} already exists")
        except Exception as e:
            self.logger.error(e)
        
        return False

    def get_tweet(self, tid:str) -> dict:
        """
            Get a tweet from the database.
        """
        return self.db.tweets.find_one({"tid": tid})

    def find(self, query:dict, limit=0) -> list:
        """
            Run find query.
        """
        data = list(self.db.tweets.find(query).limit(limit))
        return data

    def aggregate(self, pipeline: list) -> list:
        """
            Run aggregate query.
        """
        data = list(self.db.tweets.aggregate(pipeline))
        return data
