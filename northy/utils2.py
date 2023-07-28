import json
from .logger_config import logger

class Utils:
    def __init__(self):
        pass

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
