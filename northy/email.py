import os
import logging
from northy.config import config
from postmarker.core import PostmarkClient

class Email:
    def __init__(self, API_KEY=None) -> None:
        # Create a logger instance for the class
        self.logger = logging.getLogger(__name__)

        self.API_KEY = config['POSTMARK_SERVER_TOKEN'] if API_KEY is None else API_KEY
        self.client = PostmarkClient(server_token=self.API_KEY)

    def send(self, _from="rtk@rtk-cv.dk", to="rtk@rtk-cv.dk",
             subject="Postmark test", content=None):
        self.client.emails.send(
            From=_from,
            To=to,
            Subject=subject,
            #TextBody=content,
            HtmlBody=content
        )
