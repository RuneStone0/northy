import os
from dotenv import dotenv_values
from northy.utils import Utils

class Config:
    """
        Config class to hold all the environment variables.
    """
    def __init__(self) -> None:
        utils = Utils()

        # Load environment variables from .env file and system environment
        self.config = {
            **dotenv_values(".env"),
            **os.environ,  # override loaded values with environment variables
        }

        # Convert PRODUCTION to boolean
        self.config["PRODUCTION"] = utils.str2bool(self.config["PRODUCTION"])

        # Set environment variables        
        self.set_env()

    def set_env(self):
        """
            Set environment variables from config.
        """
        for key, value in self.config.items():
            os.environ[key] = str(value)
        