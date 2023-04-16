import ast
import json
import pyprowl
from dotenv import dotenv_values
from datetime import datetime
class Utils:
    def __init__(self):
        self.config = None
        self.get_config()

    def write_json(self, data, filename='.saxo-session'):
        with open(filename,'w') as f:
            json.dump(data, f, indent=4)

    def read_json(self, filename='.saxo-session'):
        with open(filename,'r') as f:
            data = json.load(f)
        return data
    
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

    def serialize_datetime(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()

    def prowl(self, message, priority=0, url=None, app_name='Northy'):
        """
            Send push notification using Prowl.
        """
        p = pyprowl.Prowl(self.config["prowl_api_key"])

        try:
            p.verify_key()
            #print("Prowl API key successfully verified!")
        except Exception as e:
            #print("Error verifying Prowl API key: {}".format(e))
            exit()

        try:
            p.notify(event="Alert", 
                     description=message, 
                     priority=priority, 
                     url=url, 
                     appName=app_name)
            print("Notification successfully sent to Prowl!")
        except Exception as e:
            print("Error sending notification to Prowl: {}".format(e))
