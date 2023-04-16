import json
import logging
import os
from dotenv import dotenv_values
from logging.handlers import RotatingFileHandler
import coloredlogs

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
        if self.config is not None:
            return self.config
        else:
            self.config = dotenv_values(".env")
            return self.config
