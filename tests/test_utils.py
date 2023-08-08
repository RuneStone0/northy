import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from northy.utils import Utils

u = Utils()

def test_json_to_string():
    assert isinstance(u.json_to_string({"hello": "world"}), str)  # Is string
    # write more tests for utils.py
    
def test_file_rw():
    filename = "tests/unittest.file"
    test_data = {"hello": "world"}
    assert u.write_json(test_data, filename=filename) == None
    assert u.read_json(filename=filename) == test_data
    assert u.read_json(filename="nonexistingfile.txt") == None

    # Cleanup
    os.remove(filename)

if __name__ == "__main__":
    test_json_to_string()
    test_file_rw()
