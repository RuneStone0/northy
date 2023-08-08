import json
from datetime import datetime
import datetime
import pytz
import logging

class Utils:
    def __init__(self):
        # Create a logger instance for the class
        self.logger = logging.getLogger(__name__)

        self.config = None

    def write_json(self, data, filename):
        self.logger.debug("Writing data to: {}".format(filename))
        with open(filename,'w') as f:
            json.dump(data, f, indent=4)

    def read_json(self, filename):
        self.logger.debug("Reading data from: {}".format(filename))
        try:
            with open(filename,'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.warning(f"File {filename} not found.")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return None
    
    def json_to_string(self, data):
        return json.dumps(data)

    def is_market_open(self):
        # Set the timezone to Central Time (CT)
        tz = pytz.timezone('US/Central')

        # Get the current time in Central Time (CT)
        now = datetime.datetime.now(tz)

        # If Friday after 4pm skip
        if now.weekday() == 4 and now.hour >= 16:
            self.logger.debug("Market is closed. It's Friday after 5pm.")
            return False

        # If Saturday skip
        if now.weekday() == 5:
            self.logger.debug("Market is closed. It's Saturday.")
            return False

        # If Sunday before 5pm skip
        if now.weekday() == 6 and now.hour < 17:
            self.logger.debug("Market is closed. It's Sunday before 5pm.")
            return False

        self.logger.debug("Market is open!")
        return True
