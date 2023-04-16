import os
import logging
from logging.handlers import RotatingFileHandler
import coloredlogs
from .utils import Utils

u = Utils()

def get_logger(self, loggername="main", filename="logs.log"):
    config = u.get_config()
    log_level = config["LOG_LEVEL"]
    root = logging.getLogger(loggername)

    # Log to console
    coloredlogs.install(
        level=log_level,
        logger=root,
        fmt='%(asctime)s %(name)s %(funcName)s():%(lineno)s %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        level_styles={
            # Colors: 'black', 'blue', 'cyan', 'green', 'magenta', 'red', 'white' and 'yellow'
            'debug': {'color': 'white'},
            'info': {'color': 'green'},
            'warning': {'color': 'yellow'},
            'error': {'color': 'red'},
            'critical': {'color': 'magenta'},
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