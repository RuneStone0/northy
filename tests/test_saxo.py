import os
from northy import utils
from northy.saxo import Saxo, SaxoConfig, SaxoHelper

saxo = Saxo()
saxo_config = SaxoConfig()
saxo_helper = SaxoHelper()

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
    __saxo.get(f"/port/v1/positions/me").json

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
    assert saxo_config.get_stoploss("DIJA") == 25
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
    positions = get_mock_data("alread_closed_pos.json")
    out = saxo.close(positions)
    assert isinstance(out.json, dict)
    assert out.status_code == 400

    # Invalid Position
    positions = get_mock_data("invalid_pos.json")
    out = saxo.close(positions)
    assert isinstance(out.json, dict)
    assert out.status_code == 400

def test_price():
    # Valid symbol
    _id = saxo_helper.symbol_to_uic("NDX")
    assert isinstance(saxo.price(_id), dict)

    # Invalid symbol
    assert saxo.price(123) == None

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
    order = saxo.trade(signal="NDX_TRADE_SHORT_IN_13199_SL_25")
    assert isinstance(order, dict)
    
    # Delete order (note: this is only possible if the order is still open)
    order_id = order["OrderId"]
    saxo.cancel_order(orders=order_id)

def test_trade_flat():
    saxo.trade("SPX_FLAT")

