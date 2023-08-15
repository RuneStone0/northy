import os
from dotenv import dotenv_values
from .utils import Utils
utils = Utils()

config = {
    **dotenv_values(".env"),
    #**os.environ,  # override loaded values with environment variables
}

production = utils.str2bool(config["PRODUCTION"])

def set_env():
    """
        Set environment variables from config.
    """
    for key, value in config.items():
        os.environ[key] = str(value)
