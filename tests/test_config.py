from northy.config import Config
config = Config().config

def test_config():
    assert isinstance(config, dict)
    config["PRODUCTION"]
