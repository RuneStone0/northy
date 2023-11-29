import os
import logging
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timezone
from northy.color import colored
from northy.config import config
import mongomock
import bson

class Database(object):
    def __init__(self, connection_string=None, production=None,
                 database_name="northy", collection_name="tweets") -> None:
        # Create a logger instance for the class
        self.logger = logging.getLogger(__name__)
        
        self.connection_string = config["MONGODB_CONN"] if connection_string is None else connection_string
        self.production = config["PRODUCTION"] if production is None else production
        self.database_name = database_name
        self.collection_name = collection_name

        self.db = None  # DB Object
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

    def backup(self, output_directory="backups"):
        # Create the backups directory if it doesn't exist
        os.makedirs(output_directory, exist_ok=True)
        
        # Get the current date and time
        current_datetime = datetime.now()
        timestamp = current_datetime.strftime("%Y-%m-%d-%H-%M-%S")
        
        # Construct the backup file path
        backup_filename = f"{timestamp}.bson"
        backup_file_path = os.path.join(output_directory, backup_filename)
        
        # Retrieve all documents from the collection
        documents = self.db.tweets.find()
            
        # Convert documents to BSON format and write to the output file
        with open(backup_file_path, 'wb') as f:
            for document in documents:
                bson_data = bson.BSON.encode(document)
                f.write(bson_data)
        
        print(f"Backup of '{self.db.tweets.name}' collection saved to '{backup_file_path}'")

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
        
        # Check if created_at is UTC
        if data["created_at"].tzinfo != timezone.utc:
            self.logger.error("created_at is not UTC")
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