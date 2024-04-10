import sys
import os
import re
import time
import sqlite3
import xmltodict
import logging
from datetime import datetime
from northy.config import Config
from northy.db import Database

config = Config().config

class Noc:
    """ Windows Notifications Center """
    def __init__(self, wpndatabase_path=None):
        # Create a logger instance for the class
        self.logger = logging.getLogger(__name__)

        # Prepare class
        self.__prepare_cache()
        self.check_os()
        if wpndatabase_path is None:
            self.__set_db_path()
        else:
            self.db_path = wpndatabase_path
        self.logger.critical("The browser must be kept open to receive notifications!")
        self.logger.critical("Only one browser can Twitter Notifications enabled. If another browser is enabled, it can hijack the notifications")
        self.logger.critical("Enable Twitter notification (https://twitter.com/settings/push_notifications). Setting is managed per-browser and not per Twitter/Chrome profile.")
        self.logger.critical("Add twitter.com / x.com to Always Active Sites (chrome://settings/performance)")
        self.logger.info(f"Using: {self.db_path}")

    def check_os(self):
        # Check if the OS is Windows
        _os = os.name
        if _os != "nt":
            self.logger.critical("This script only works on Windows")

    def __set_db_path(self):
        # Get path to noc db
        path = 'AppData\\Local\\Microsoft\\Windows\\Notifications\\wpndatabase.db'
        # add userprofile to path
        path = os.path.join(os.getenv('USERPROFILE'), path)
        
        self.db_path = path

    def __prepare_cache(self):
        """
            Cache is used to keep track of which notifications have already been processed.
            This is necessary because the notifications are not deleted from the database.
            Using a cache presents us from making unnecessary database queries.
            The cache is a list of notification ids.

            When the cache reaches a certain size, we clean it up, to avoid memory issues.
        """
        self.cache = []
        self.cache_max = 100
        self.cache_clean = self.cache_max / 2

    def get_notifications(self) -> dict:
        notidications = []

        # connect to the database
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT * FROM Notification WHERE type = 'toast'")
        for row in cur.fetchall():
            # extract data from rows
            order = row[0]
            _id = row[1]
            #handler_id = row[2]
            #activity_id = row[3]
            #_type = row[4]
            payload = row[5]
            #tag = row[6]
            #group = row[7]
            #expirey_time = row[8]
            #arrival_time = row[9]
            #data_version = row[10]
            #payload_type = row[11]
            #boot_id = row[12]
            #expires_on_reboot = row[13]

            # convert relevant data to dict
            notidication = {
                "order": order,
                "id": _id,
                #"handler_id": handler_id,
                #"activity_id": activity_id,
                #"type": _type,
                #"payload": payload,
                #"tag": tag,
                #"group": group,
                #"expirey_time": expirey_time,
                #"arrival_time": arrival_time,
                #"data_version": data_version,
                #"payload_type": payload_type,
                #"boot_id": boot_id,
                #"expires_on_reboot": expires_on_reboot
            }

            # convert payload from bytes -> str -> xml -> dict
            payload_str = payload.decode('utf-8')
            payload_dict = xmltodict.parse(payload_str)
            notidication["payload"] = payload_dict
            notidications.append(notidication)

        # Close the connection
        conn.close()

        return notidications

    def notification_to_tweet(self, notification) -> dict:
        """
            Convert a notification to a tweet-like dict
            The notification is a dict with the following structure:
            {
                "order": 1,
                "id": 1,
                "payload": {
                    "toast": {
                        "@launch": "twitter://timeline|Twitter|Twitter|twitter://timeline",
                        "visual": {
                            "binding": {
                                "text": [
                                    "Northy",
                                    "Hello World!"
                                ]
                            }
                        }
                    }
                }
            }

            The tweet-like dict has the following structure:
            {
                "tid": 1,
                "from": "Northy",
                "text": "Hello World!"
            }

            The tid is the tweet id, which is extracted from the notification id.
        """
        toast = notification["payload"]["toast"]
        # convert notification to tweet
        tid = toast["@launch"].split("|")[-1].split("-")[-1]
        _from = toast["visual"]["binding"]["text"][0]
        _text = toast["visual"]["binding"]["text"][1]
        
        # Convert displayTimestamp to datetime
        displayTimestamp = toast["@displayTimestamp"]
        date_string = displayTimestamp.replace("Z", "+00:00")
        created_at = datetime.fromisoformat(date_string)

        # Text is none, when only a picture is posted
        if _text is None:
            _text = ""
        
        _text = re.sub(r'\s+', ' ', _text)
        tweet = {
            "tid": tid,
            "from": _from,
            "text": _text,
            "created_at": created_at
        }
        return tweet

    def process_notification(self, db):
        notifications = self.get_notifications()
        for notification in notifications:
            nid = notification["id"]
            if nid in self.cache:
                #self.logger.info(f"Notification {nid} already processed")
                continue

            # Check if notification is a tweet
            is_tweet = "twitter" in notification.get("payload", {}).get("toast", {}).get("@launch", "")

            if is_tweet:
                # Tweet notification
                data = self.notification_to_tweet(notification)
                self.logger.info("{}: {}".format(data["from"], data["text"]))

                # Add tweet to database
                if data["from"] == "Northy":
                    db.add_tweet(data)
            else:
                # Non-Tweet notification
                self.logger.info(f"Ignore non-Tweet notification")

            # Add notification id to cache and clean it if necessary
            self.cache.append(nid)
            if len(self.cache) >= self.cache_max:
                self.logger.info(f"Remove {self.cache_clean} items from cache")
                for _ in range(int(self.cache_clean)): self.cache.pop(0)

    def watch(self, loops=lambda: True):
        """
            Continuously watch for changes in the Windows Notification Center
        """
        db = Database()
        while loops():
            self.process_notification(db=db)
            
            # Check for new notifications every second
            time.sleep(1)
