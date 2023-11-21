import sys
import os
import re
import time
import sqlite3
import xmltodict
import logging
from northy.config import config
from northy.db import Database

class Noc:
    """ Windows Notifications Center """
    def __init__(self, production=None, wpndatabase_path=None):
        # Create a logger instance for the class
        self.logger = logging.getLogger(__name__)

        # MongoDB
        self.production = config["PRODUCTION"] if production is None else production
        self.db = Database(production=self.production)

        # Prepare class
        self.__check_os()
        if wpndatabase_path is None:
            self.__set_db_path()
        else:
            self.db_path = wpndatabase_path

    def __set_db_path(self):
        # Get path to noc db
        path = 'AppData\\Local\\Microsoft\\Windows\\Notifications\\wpndatabase.db'
        self.db_path = os.path.join(os.getenv('USERPROFILE'), path)

    def __check_os(self):
        """ check if we're running on Windows """
        _os = os.name
        if _os != "nt":
            self.logger.critical("This script only works on Windows")
            sys.exit()

    def get_notifications(self) -> dict:
        notidications = []

        # connect to the database
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT * FROM Notification")
        for row in cur.fetchall():
            # extract data from rows
            order = row[0]
            _id = row[1]
            #handler_id = row[2]
            #activity_id = row[3]
            _type = row[4]
            payload = row[5]
            #tag = row[6]
            #group = row[7]
            #expirey_time = row[8]
            #arrival_time = row[9]
            #data_version = row[10]
            #payload_type = row[11]
            #boot_id = row[12]
            #expires_on_reboot = row[13]

            # skip if not a toast notification
            if _type != "toast":
                continue
            
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

    def notification_to_tweet(self, notification):
        toast = notification["payload"]["toast"]
        # convert notification to tweet
        tid = toast["@launch"].split("|")[-1].split("-")[-1]
        _from = toast["visual"]["binding"]["text"][0]
        _text = toast["visual"]["binding"]["text"][1]
        
        _text = re.sub(r'\s+', ' ', _text)
        tweet = {
            "tid": tid,
            "from": _from,
            "text": _text
        }
        return tweet

    def delete_notification(self, _id):
        """ Delete a notification from the database """
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()

        cur.execute("DELETE FROM Notification WHERE id = ?", (_id,))
        conn.commit()
        self.logger.debug(f"Deleted notification id: {_id}")
        
        conn.close()

    def process_notification(self):
        notifications = self.get_notifications()
        for notification in notifications:
            data = self.notification_to_tweet(notification)
            if data["from"] == "Northy":
                self.db.add_tweet(data)
            else:
                self.logger.debug(f"Ignore notification: {data}")
            
            # Delete notification after processing
            self.delete_notification(notification["id"])

    def watch(self):
        while True:
            self.process_notification()
            
            # Check for new notifications every second
            time.sleep(5)
