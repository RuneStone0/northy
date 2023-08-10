import os
import pyprowl
import logging

class Prowl:
    """
        Prowl API wrapper (https://www.prowlapp.com/)

        params:
            API_KEY: Prowl API key (attempts to get it from the environment variable PROWL_API_KEY)

    """
    def __init__(self, API_KEY=None) -> None:
        # Create a logger instance for the class
        self.logger = logging.getLogger(__name__)
        
        self.PROWL_API_KEY = os.environ.get('PROWL_API_KEY') if API_KEY is None else API_KEY
        self.prowl = pyprowl.Prowl(API_KEY)

    def test(self):
        try:
            self.prowl.verify_key()
            self.logger.debug("Prowl API key successfully verified!")
            return True
        except Exception as e:
            self.logger.error("Error verifying Prowl API key: {}".format(e))
            return False

    def send(self, message, priority=0, url=None, app_name="Northy"):
        """
            Send push notification using Prowl.
        """
        response = self.prowl.notify(event="ALERT", 
                    description=message, 
                    priority=priority, 
                    url=url, 
                    appName=app_name)
        self.logger.info("Prowl notification sent: {}".format(message))
        self.logger.debug("Prowl response: {}".format(response))
