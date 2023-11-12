import os
import logging
from northy import utils
from unittest.mock import patch
from datetime import datetime, timezone, timedelta
from northy.saxo import Saxo, SaxoConfig, SaxoHelper
saxo = Saxo()
saxo_config = SaxoConfig()
saxo_helper = SaxoHelper()
logger = logging.getLogger(__name__)

def get_mock_data(filename):
    u = utils.Utils()
    dir = os.path.dirname(__file__)
    file_path = f"mock_data/saxo/{filename}"
    path = os.path.join(dir, file_path)
    return u.read_json(path)

def test_get():
    # Trigger HTTP 401 error (Unauthorized)
    __saxo = Saxo()
    import requests
    __saxo.s = requests.session()  # ensure no existing session exists
    __saxo.get(f"/port/v1/positions/me").json()

def test_positions():
    # Simple positions test
    assert isinstance(saxo.positions(), dict)

    # Filter by symbol
    pos = saxo.positions(symbol="SPX")
    assert isinstance(pos, dict)

def test_positions_without_session_file():
    # delete temp/.saxo-session file
    path = os.path.join(os.path.dirname(__file__), "../temp/.saxo-session")
    if os.path.exists(path):
        print("Deleting temp/.saxo-session")
        os.remove(path)
    pos = saxo.positions()
    assert isinstance(pos, dict) == True

def test_refresh_token():
    assert isinstance(saxo.refresh_token(), dict)
    # test if first two chars are "ey"
    assert saxo.refresh_token()["access_token"][0:2] == "ey"

def test_valid_token():
    token = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjEwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMCJ9.eyJpc3MiOiJodHRwczovL2F1dGgubm9ydGh5LmNvbSIsInN1YiI6...Oi8vYXBpLm5vcnRoeS5jb20iXSwiaWF0IjoxNjI5MjU0NjQ0LCJleHAiOjE2MjkzNDEwNDQsImF6cCI6IjE3NDcwNzkzIiwic2NvcGUiOiJvcGVuaWQgcH"
    assert saxo.valid_token(token) == False

def test_get_stoploss():
    assert saxo_config.get_stoploss("SPX") == 10
    assert saxo_config.get_stoploss("RUT") == 10
    assert saxo_config.get_stoploss("NDX") == 25
    assert saxo_config.get_stoploss("DJIA") == 25
    assert saxo_config.get_stoploss("INVALID") == 9

def test_signal_to_tuple():
    signals = [
        "NDX_TRADE_SHORT_IN_13199_SL_25 ",
        "SPX_SCALEOUT_IN_3809_OUT_4153_POINTS_344",
        "SPX_FLAT",
        "SPX_FLATSTOP",
        "NDX_CLOSED",
        "SPX_LIMIT_LONG_IN_3749_OUT_3739_SL_10",
    ]
    for signal in signals:
        out = saxo.signal_to_tuple(signal=signal)
        assert isinstance(out, tuple)
        assert isinstance(out.raw, str)
        assert isinstance(out.action, str)

def test_auth_no_file():
    # Test auth where .saxo-session does not exist
    if os.path.exists(".saxo-session"):
        os.remove(".saxo-session")
        saxo = Saxo()
        saxo.positions()

def test_auth_invalid_file():
    # Test auth where .saxo-session exists, but is invalid

    # Ensure .saxo-session does not exist
    try:
        os.remove(".saxo-session")
    except:
        pass

    # Create invalid .saxo-session
    invalid_jwt = { "base_uri": None }
    u = utils.Utils()
    u.write_json(data=invalid_jwt, filename=".saxo-session")
    Saxo()

def test_cancel_order():
    # Invalid Order
    out = saxo.cancel_order(orders="123456789")
    assert out.status_code == 404

    # Valid Order
    # TODO

def test_close():
    # Possible responses:
    # Closed position: 
    #   Response(status_code=200, json={'Orders': [{'OrderId': '5014821421'}]})
    # Invalid Position: 
    #   Response(status_code=400, json={'Orders': [{'ErrorInfo': 
    #   {'ErrorCode': 'OrderRelatedPositionNotFound', 
    #   'Message': 'Related position not found'}}]})
    # Already Closed: 
    #   Response(status_code=400, json={'Orders': [{'ErrorInfo': 
    #   {'ErrorCode': 'OrderRelatedPositionIsClosed', 'Message': 
    #   'Related position already closed'}}]}) 
    # TODO: Mock HTTP requests/responses to speed up the tests

    # Already Closed
    positions = get_mock_data("already_closed_pos.json")
    out = saxo.close(positions)
    from requests import Response
    assert isinstance(out, Response)
    assert out.status_code == 400

    # Invalid Position
    positions = get_mock_data("invalid_pos.json")
    out = saxo.close(positions)
    assert isinstance(out, Response)
    assert out.status_code == 400

def test_price():
    # Valid symbol
    _id = saxo_helper.symbol_to_uic("NDX")
    assert isinstance(saxo.price(_id), dict)

    # Invalid symbol
    assert saxo.price(123) == None

def test_doc_older_than():
    # Test with created_at older than max_age
    time_in_past = datetime.now(timezone.utc) + timedelta(minutes = -16)
    doc = { 'tid': '1697257335847289249', 'created_at': time_in_past }
    out = saxo_helper.doc_older_than(document=doc, max_age=15)
    assert out == True

    # Test with created_at younger than max_age
    time_in_past = datetime.now(timezone.utc) + timedelta(minutes = -5)
    doc = { 'tid': '1697257335847289249', 'created_at': time_in_past }
    out = saxo_helper.doc_older_than(document=doc, max_age=15)
    assert out == False

def test_trade():
    signals = [
        "NDX_TRADE_SHORT_IN_13199_SL_25 ",
        "SPX_SCALEOUT_IN_3809_OUT_4153_POINTS_344",
        "SPX_FLAT",
        "SPX_FLATSTOP",
        "NDX_CLOSED",
        "SPX_LIMIT_LONG_IN_3749_OUT_3739_SL_10",
    ]
    # Test SHORT, valid signals
    price = saxo.price(saxo_helper.symbol_to_uic("NDX"))["Quote"]["Mid"]
    price = int(price) + 5
    signal = f"NDX_TRADE_SHORT_IN_{price}_SL_25"
    order = saxo.trade(signal=signal).json()
    
    # Delete order (note: this is only possible if the order is still open)
    try:
        order_id = order["OrderId"]
        saxo.cancel_order(orders=order_id)
    except:
        logger.warning("Could not delete order")
        pass

def test_trade_buysell_all():
    """
    Test all possible combinations of symbols and trade directions
    Attempts to create an order and then deletes it (if possible)
    """
    symbols = saxo_config.config["tickers"].keys()
    direction = ["LONG", "SHORT"]
    for symbol in symbols:
        for dir in direction:
            signal = f"{symbol}_TRADE_{dir}_IN_13199_SL_25"
            logger.info(f"Testing {signal}")
            rsp = saxo.trade(signal)
            order = rsp.json()
            assert rsp.status_code == 200
            assert isinstance(order, dict)

            # Delete order (note: only possible if the order is still open)
            try:
                saxo.cancel_order(orders=order["OrderId"])
            except:
                logger.warning("Could not delete order")
                pass

def test_trade_flat():
    saxo.trade("SPX_FLAT")
