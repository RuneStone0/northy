import os
import logging
from sparkpost import SparkPost

class Email:
    def __init__(self, API_KEY=None):
        # Create a logger instance for the class
        self.logger = logging.getLogger(__name__)

        # Get the API key from the environment variable
        self.API_KEY = os.environ.get('SPARKPOST_API_KEY') if API_KEY is None else API_KEY

    # Make a function that sends an email using Gmail

    def send(self, to_email, subject, content):
        sp = SparkPost(self.API_KEY)
        response = sp.transmissions.send(
            use_sandbox=False,
            recipients=[to_email],
            html=f'{content}',
            from_email='northy@post.rtk-cv.dk',
            subject=subject
        )
        self.logger.info(response)


