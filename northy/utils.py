import json
import logging

class Utils:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

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
            self.logger.warning(f"File '{filename}' not found.")
            return None
    
    def json_to_string(self, data):
        return json.dumps(data)

    def str2bool(self, value):
        """
            Convert string to boolean.
        """
        v = str(value)
        true_values = ("yes", "true", "t", "1")
        false_values = ("no", "false", "f", "0")
        
        lower_v = v.lower()
        
        if lower_v in true_values:
            return True
        elif lower_v in false_values:
            return False
        else:
            raise ValueError("Invalid boolean string representation.")
