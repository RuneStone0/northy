import os
import logging
from zoneinfo import ZoneInfo
from northy import utils
from unittest.mock import patch
from datetime import datetime
from northy.saxo import Saxo, SaxoHelper
from northy.saxo_report import SaxoReport
from datetime import datetime

tz = ZoneInfo('US/Central')
saxo = Saxo()
saxo_helper = SaxoHelper()
logger = logging.getLogger(__name__)

def get_mock_data(filename):
    u = utils.Utils()
    dir = os.path.dirname(__file__)
    file_path = f"mock_data/saxo/{filename}"
    path = os.path.join(dir, file_path)
    return u.read_json(path)

def test_send_report():
    positions = get_mock_data("closed_pos.json")
    saxo_report = SaxoReport()
    saxo_report.send_report(positions=positions)

@patch('northy.saxo_report.datetime')
def test_close_report_sleep(mock_datetime):
    # Mock the current time
    dt = datetime(2023, 11, 10, 12, 59, 59, tzinfo=tz)
    mock_datetime.now.return_value = dt
    saxo_report = SaxoReport()
    saxo_report.close_report_sleep(hours=13)
