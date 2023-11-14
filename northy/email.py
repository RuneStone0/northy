import os
from postmarker.core import PostmarkClient

class Email:
    def __init__(self, API_KEY=None) -> None:
        self.API_KEY = os.environ.get('POSTMARK_SERVER_TOKEN') if API_KEY is None else API_KEY
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
