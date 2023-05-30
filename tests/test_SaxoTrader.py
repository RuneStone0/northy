import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from northy import signal

from northy.database import Tweets
from northy import utils
from unittest.mock import patch, MagicMock

u = utils.Utils()
t = signal.Signal()
db_tweets = Tweets().get()

# Define mock_positions
mock_positions = MagicMock()

path = os.path.join(os.path.dirname(__file__), "mock_data/SaxoTrader_Saxo_positions.json")
mock_positions = u.read_json(path)

# Mock the SaxoTrader.Saxo.positions() method
from northy import SaxoTrader
trader = SaxoTrader.Saxo()

def test_positions():
    # Simple positions test
    pos = trader.positions()
    found_data = True if "Data" in pos.keys() else False
    assert found_data == True
    assert isinstance(pos, dict) == True

def test_positions_without_session_file():
    # delete temp/.saxo-session file
    path = os.path.join(os.path.dirname(__file__), "../temp/.saxo-session")
    if os.path.exists(path):
        print("Deleting temp/.saxo-session")
        os.remove(path)
    pos = trader.positions()
    assert isinstance(pos, dict) == True

@patch('northy.SaxoTrader.Saxo.positions')
def test_SaxoTrader_trade(mock_positions_method):
    # Define the return value of the positions() method
    mock_positions_method.return_value = mock_positions
    pos = trader.positions()
    #print(pos)
    
    trader.trade("SPX_FLAT")

    #mock_positions.assert_called_once_with()
    import sys
    sys.exit()

    # Valid input
    pipe = [
        {"$match": {"alert": True}},
        {"$sample": {"size": 5}}
    ]

    for i in db_tweets.aggregate(pipe):
        for signal in i["signals"]:
            print(signal)
            assert isinstance(trader.trade(signal), list)
#test_SaxoTrader_trade()

def test_SaxoTrader_trade_live():
    trader.trade("SPX_FLAT")
#test_SaxoTrader_trade_live()

def test_trade():
    saxo = SaxoTrader.Saxo()
    #saxo.trade2("SPX_FLAT")
    saxo.trade2("SPX_TRADE_LONG_IN_4128_SL_10")

test_trade()

