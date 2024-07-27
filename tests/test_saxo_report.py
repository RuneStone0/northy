import os
import logging
from zoneinfo import ZoneInfo
from northy import utils
from unittest.mock import patch
from datetime import datetime
from northy.saxo import Saxo, SaxoHelper
from northy.saxo_report import SaxoReport
from functools import wraps
from datetime import datetime

tz = ZoneInfo('US/Central')
saxo = Saxo(profile_name="UT")
saxo_helper = SaxoHelper()
saxo_report = SaxoReport()
logger = logging.getLogger(__name__)

def mock_sleep(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        with patch('time.sleep') as mock_sleep:
            # Mock time.sleep to do nothing
            mock_sleep.side_effect = lambda _: None
            return func(*args, **kwargs)
    return wrapper

def get_mock_data(filename):
    u = utils.Utils()
    dir = os.path.dirname(__file__)
    file_path = f"mock_data/saxo/{filename}"
    path = os.path.join(dir, file_path)
    return u.read_json(path)

def test_send_report():
    positions = get_mock_data("closed_pos.json")
    saxo_report.send_report(positions=positions)

def test_send_report_no_positions():
    positions = get_mock_data("positions_empty.json")
    saxo_report.send_report(positions=positions)

def test_send_report_no_closed():
    positions = get_mock_data("positions.json")
    saxo_report.send_report(positions=positions)

@mock_sleep
@patch('northy.saxo_report.datetime')
def test_close_report_sleep_weekend(mock_datetime):
    # Mock the current time
    dt = datetime(2023, 11, 12, 12, 59, 59, tzinfo=tz) # Sunday
    mock_datetime.now.return_value = dt
    saxo_report.close_report_sleep()

@mock_sleep
@patch('northy.saxo_report.datetime')
def test_close_report_sleep_weekday_after_17(mock_datetime):
    # Mock the current time
    dt = datetime(2023, 11, 10, 18, 59, 59, tzinfo=tz) # Friday
    mock_datetime.now.return_value = dt
    saxo_report.close_report_sleep()

@mock_sleep
@patch('northy.saxo_report.datetime')
def test_close_report_sleep_weekday_before_17(mock_datetime):
    # Mock the current time
    dt = datetime(2023, 11, 10, 10, 59, 59, tzinfo=tz) # Friday
    mock_datetime.now.return_value = dt
    saxo_report.close_report_sleep()
