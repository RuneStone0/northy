from northy.config import config
from postmarker.core import PostmarkClient

class Email:
    def __init__(self) -> None:
        self.token = config["POSTMARK_SERVER_TOKEN"]
        self.client = PostmarkClient(server_token=self.token)

    def send(self, _from="rtk@rtk-cv.dk", to="rtk@rtk-cv.dk",
             subject="Postmark test", content=None):
        self.client.emails.send(
            From=_from,
            To=to,
            Subject=subject,
            #TextBody=content,
            HtmlBody=content
        )
