import os
import logging
from northy import utils
from northy.config import set_env
from northy.saxo import SaxoHelper
from datetime import datetime
from unittest.mock import patch

saxo_helper = SaxoHelper()
u = utils.Utils()

def get_mock_data(filename):
    dir = os.path.dirname(__file__)
    file_path = f"mock_data/saxo_helper/{filename}"
    path = os.path.join(dir, file_path)
    return u.read_json(path)

def test_symbol_to_uic():
    spx = saxo_helper.symbol_to_uic("SPX")
    assert spx == 4913
    assert isinstance(spx, int)

    invalid = saxo_helper.symbol_to_uic("INVALID")
    assert invalid == None

def test_uic_to_symbol():
    spx = saxo_helper.uic_to_symbol(4913)
    assert spx == "SPX"
    assert isinstance(spx, str)

    invalid = saxo_helper.uic_to_symbol("000")
    assert invalid == "N/A"

def test_get_position_stop_details():
    positions = get_mock_data("positions.json")["Data"][0]
    details = saxo_helper.get_position_stop_details(positions)
    assert isinstance(details, dict)
    assert details["stop_price"] == 4148.49

def test_pprint_positions():
    positions = get_mock_data("positions.json")
    saxo_helper.pprint_positions(positions)

def test_filter_positions():
    positions = get_mock_data("positions.json")
    positions_filtered = saxo_helper.filter_positions(positions, cfd_only=True)
    assert positions_filtered["__count"] == 2