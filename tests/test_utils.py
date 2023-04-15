import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from northy import utils

u = utils.Utils()

def test_json_to_string():
    assert isinstance(u.json_to_string({"hello": "world"}), str)  # Is string

    # write more tests for utils.py
    
