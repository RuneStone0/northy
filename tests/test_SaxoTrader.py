import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from northy import TradeSignal

from northy.database import Tweets
from northy import utils
from unittest.mock import patch, MagicMock

u = utils.Utils()
t = TradeSignal.Signal()
db_tweets = Tweets().get()

# Define mock_positions
mock_positions = MagicMock()

path = os.path.join(os.path.dirname(__file__), "mock_data/SaxoTrader_Saxo_positions.json")
mock_positions = u.read_json(path)

# Mock the SaxoTrader.Saxo.positions() method
from northy import SaxoTrader
trader = SaxoTrader.Saxo()

def test_connect():
    # Simple connection test
    trader._connect()

    # TODO: Make another where we remove .saxo-session and test that it reconnects


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

test_SaxoTrader_trade_live()