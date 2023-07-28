import os
import logging
from concurrent_log_handler import ConcurrentRotatingFileHandler

def setup_logger():
    # Configure the logger
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Use an absolute path to prevent file rotation trouble.
    logfile = os.path.abspath("northy.log")

    # Create a formatter for the logs
    log_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # File Logging Handler
    # Rotate log after reaching 512K, keep 5 old copies.
    file_handler = ConcurrentRotatingFileHandler(logfile, "a", 512 * 1024, 5)
    # Create a FileHandler and set the log file path
    #file_handler = logging.FileHandler('northy.log')
    # Set the log level for the file handler (optional, can be different from the root logger)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(log_formatter)
    # Add the file handler to the logger
    logger.addHandler(file_handler)

    # Console Logging Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(log_formatter)
    #logger.addHandler(console_handler)

    return logger

logger = setup_logger()