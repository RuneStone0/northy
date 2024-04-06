import os
import json
import logging
from jsmin import jsmin

class Utils:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def write_json(self, data, filename):
        self.logger.debug("Writing data to: {}".format(filename))
        with open(filename,'w') as f:
            json.dump(data, f, indent=4)

    def read_json(self, filename):
        """
            Read JSON or JS file and return data.
        """
        self.logger.debug("Reading data from: {}".format(filename))
        try:
            with open(filename,'r') as f:
                minified = jsmin(f.read())
                return json.loads(minified)
        except FileNotFoundError:
            self.logger.warning(f"File '{filename}' not found.")
            return None

    def json_to_string(self, data):
        return json.dumps(data)
