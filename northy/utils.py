import json
from datetime import datetime
import datetime
import pytz

from .logger import get_logger
logger = get_logger("logger", "logger.log")

class Utils:
    def __init__(self):
        self.config = None

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

    def is_market_open(self):
        # Set the timezone to Central Time (CT)
        tz = pytz.timezone('US/Central')

        # Get the current time in Central Time (CT)
        now = datetime.datetime.now(tz)

        # If Friday after 4pm skip
        if now.weekday() == 4 and now.hour >= 16:
            logger.debug("Market is closed. It's Friday after 5pm.")
            return False

        # If Saturday skip
        if now.weekday() == 5:
            logger.debug("Market is closed. It's Saturday.")
            return False

        # If Sunday before 5pm skip
        if now.weekday() == 6 and now.hour < 17:
            logger.debug("Market is closed. It's Sunday before 5pm.")
            return False

        logger.debug("Market is open!")
        return True
