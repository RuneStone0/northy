from northy.email import Email
from northy.config import config, set_env

def test_send():
    # Pass API key as environment variable
    set_env()
    email = Email()
    email.send(to_email="test@rtk-cv.dk", subject="Test", content="Test")

    # Pass API  key as argument
    email = Email(API_KEY=config["SPARKPOST_API_KEY"])
    email.send(to_email="test@rtk-cv.dk", subject="Test", content="Test")
