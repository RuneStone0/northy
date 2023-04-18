import os
import sys
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from northy import utils

u = utils.Utils()

def test_json_to_string():
    assert isinstance(u.json_to_string({"hello": "world"}), str)  # Is string

    # write more tests for utils.py
    
def test_file_rw():
    filename = "unittest.file"
    test_data = {"hello": "world"}
    assert u.write_json(test_data, filename=filename) == None
    assert u.read_json(filename=filename) == test_data
    assert u.read_json(filename="invalid.file") == None

def test_get_config():
    conf = u.get_config()
    assert isinstance(conf, dict)
    assert "mongodb_conn" in conf

def test_serialize_datetime():
    dt = datetime(2022, 4, 17, 10, 30, 45)
    assert u.serialize_datetime(dt) == "2022-04-17T10:30:45"
    assert isinstance(u.serialize_datetime(dt), str)

def test_prowl():
    assert u.prowl(message="test", priority=1) == None

test_prowl()