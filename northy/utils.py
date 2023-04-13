import json
import logging
import os
from dotenv import dotenv_values
from logging.handlers import RotatingFileHandler
import coloredlogs

config = dotenv_values(".env")
log_level = config["LOG_LEVEL"]

class Utils:
    def __init__(self):
        pass

    def write_json(self, data, filename='.saxo-session'):
        with open(filename,'w') as f:
            json.dump(data, f, indent=4)

    def read_json(self, filename='.saxo-session'):
        with open(filename,'r') as f:
            data = json.load(f)
        return data
    
    def json_to_string(self, data):
        return json.dumps(data)
    
    def setup_logging(self, loggername="main", filename="logs.log"):
        config = dotenv_values(".env")
        log_level = config["LOG_LEVEL"]
        root = logging.getLogger(loggername)

        # Log to console
        coloredlogs.install(
            level=log_level,
            logger=root,
            fmt='%(asctime)s %(name)s %(funcName)s():%(lineno)s %(levelname)s %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            level_styles={
                'debug': {'color': 'white'},
                'info': {'color': 'green'},
                'warning': {'color': 'yellow'},
                'error': {'color': 'red'},
                'critical': {'color': 'purple'},
            },
            field_styles={
                'asctime': {'color': 'white'},
                'name': {'color': 'white'},
                'levelname': {'color': 'white'},
                'message': {'color': 'blue'},
            },
        )

        # Log to file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        logs_dir = os.path.join(dir_path, 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        log_fname = os.path.join(logs_dir, filename)

        fileHandler = RotatingFileHandler(log_fname, maxBytes=1000000, backupCount=10) #10 files of 1MB each
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fileHandler.setFormatter(formatter)
        root.addHandler(fileHandler)

        return root
