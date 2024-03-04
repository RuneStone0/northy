from northy.email import Email
from northy.config import Config
config = Config().config

def test_send():
    # Use API from environment variable
    email = Email()
    email.send(subject="pytest", content="Test")

    # Pass API  key as argument
    email = Email(API_KEY=config["POSTMARK_SERVER_TOKEN"])
    email.send(subject="pytest", content="Test")
