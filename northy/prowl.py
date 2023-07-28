import pyprowl
from .logger_config import logger

class Prowl:
    def __init__(self, API_KEY=None) -> None:
        self.prowl = pyprowl.Prowl(API_KEY)

    def test(self):
        try:
            self.prowl.verify_key()
            logger.debug("Prowl API key successfully verified!")
        except Exception as e:
            logger.error("Error verifying Prowl API key: {}".format(e))

    def send(self, message, priority=0, url=None, app_name="Northy"):
        """
            Send push notification using Prowl.
        """
        response = self.prowl.notify(event="ALERT", 
                    description=message, 
                    priority=priority, 
                    url=url, 
                    appName=app_name)
        logger.debug("Prowl response: {}".format(response))
        if response["status"] == "success":
            logger.info("Prowl notification sent: {}".format(message))
        else:
            logger.error("Error sending notification to Prowl: {}".format(response))
