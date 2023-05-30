import ast
from dotenv import dotenv_values

class Config(object):
    def __init__(self) -> None:
        self.config = self.__get()

    def __get(self):
        """
            Get config from .env file. If already fetched, return cached version.
        """
        self.config = dotenv_values(".env")

        # Convert string to bool
        self.config["PRODUCTION"] = ast.literal_eval(self.config["PRODUCTION"])

        return self.config
