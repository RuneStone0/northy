from northy.config import config, set_env

def test_config():
    assert isinstance(config, dict)
    config["PRODUCTION"]
    assert set_env() == None
