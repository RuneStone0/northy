from northy.prowl import Prowl

def test_prowl_send():
    prowl = Prowl()
    prowl.send(
        "Test message from northy.prowl.py",
        priority=0,
        url="https://www.google.com/")
