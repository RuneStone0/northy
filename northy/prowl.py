import os
import pyprowl
import logging
from northy.config import Config

class Prowl:
    """
        Prowl API wrapper (https://www.prowlapp.com/)

        params:
            API_KEY: Prowl API key (attempts to get it from the environment variable PROWL_API_KEY)

    """
    def __init__(self, API_KEY=None) -> None:
        # Create a logger instance for the class
        self.logger = logging.getLogger(__name__)
        self.config = Config().config
        self.prowl = pyprowl.Prowl(apiKey=self.config["PROWL"]["API_KEY"])

    def test(self) -> bool:
        try:
            self.prowl.verify_key()
            self.logger.debug("Prowl API key successfully verified!")
            return True
        except Exception as e:
            self.logger.error("Error verifying Prowl API key: {}".format(e))
            return False

    def send(self, message, priority=0, url=None, app_name="Northy") -> None:
        """
            Send push notification using Prowl.
        """
        # If not in production, do not send the notification
        if self.config["PRODUCTION"] == False:
            self.logger.debug(f"Prowl.send() called with message: {message}")
            return

        self.prowl.notify(event="ALERT", 
                    description=message, 
                    priority=priority, 
                    url=url, 
                    appName=app_name)
        self.logger.info("Prowl notification sent: {}".format(message))
