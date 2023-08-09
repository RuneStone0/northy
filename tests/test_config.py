import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from northy.config import config

def test_():
    assert config

if __name__ == "__main__":
    test_()
