import pytest
from northy.config import Config
c = Config()

def test_config():
    assert isinstance(c.config, dict)
    c.config["PRODUCTION"]

def test_config_str2bool():
    # Test False values
    for i in ["false", "0", "no", "f"]:
        assert c.str2bool(i) == False
    
    # Test True values
    for i in ["true", "1", "yes", "t"]:
        assert c.str2bool(i) == True

def test_config_str2bool_invalid():
    with pytest.raises(ValueError):
        c.str2bool("invalid")
