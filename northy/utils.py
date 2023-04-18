import ast
import json
import pyprowl
from dotenv import dotenv_values
from datetime import datetime

from .logger import get_logger
logger = get_logger("logger", "logger.log")

class Utils:
    def __init__(self):
        self.config = None
        self.get_config()

    def write_json(self, data, filename):
        logger.debug("Writing data to: {}".format(filename))
        with open(filename,'w') as f:
            json.dump(data, f, indent=4)

    def read_json(self, filename):
        logger.debug("Reading data from: {}".format(filename))
        try:
            with open(filename,'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"File {filename} not found.")
            return None
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return None
    
    def json_to_string(self, data):
        return json.dumps(data)

    def get_config(self):
        """
            Get config from .env file. If already fetched, return cached version.
        """
        if self.config is None:
            self.config = dotenv_values(".env")
            
            # convert string to bool
            self.config["PRODUCTION"] = ast.literal_eval(self.config["PRODUCTION"])

        return self.config

    def serialize_datetime(self, obj) -> str:
        if isinstance(obj, datetime):
            return obj.isoformat()

    def prowl(self, message, priority=0, url=None, app_name='Northy'):
        """
            Send push notification using Prowl.
        """
        p = pyprowl.Prowl(self.config["prowl_api_key"])

        try:
            p.verify_key()
            logger.debug("Prowl API key successfully verified!")
        except Exception as e:
            logger.error("Error verifying Prowl API key: {}".format(e))

        response = p.notify(event="Alert", 
                    description=message, 
                    priority=priority, 
                    url=url, 
                    appName=app_name)
        logger.debug("Prowl response: {}".format(response))
        if response["status"] == "success":
            logger.info("Prowl notification successfully sent: {}".format(message))
        else:
            logger.error("Error sending notification to Prowl: {}".format(response))
