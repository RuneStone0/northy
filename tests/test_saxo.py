import os
from northy import signal2
from northy import utils
from northy.config import set_env
from northy.saxo import Saxo, SaxoConfig, SaxoHelper
from unittest.mock import patch, MagicMock
from datetime import datetime

u = utils.Utils()
t = signal2.Signal()

# Define mock_positions
mock_positions = MagicMock()

path = os.path.join(os.path.dirname(__file__), "mock_data/SaxoTrader_Saxo_positions.json")
mock_positions = u.read_json(path)

# Mock the SaxoTrader.Saxo.positions() method
saxo = Saxo()
saxo_config = SaxoConfig()

def test_positions():
    # Simple positions test
    pos = saxo.positions()
    found_data = True if "Data" in pos.keys() else False
    assert found_data == True
    assert isinstance(pos, dict) == True

def test_get_symbol_SL_POINTS():
    assert saxo_config.get_symbol_SL_POINTS("SPX") == 10
    assert saxo_config.get_symbol_SL_POINTS("RUT") == 10
    assert saxo_config.get_symbol_SL_POINTS("NDX") == 25
    assert saxo_config.get_symbol_SL_POINTS("DIJA") == 25
    assert saxo_config.get_symbol_SL_POINTS("AAAA") == 9

def test_positions_without_session_file():
    # delete temp/.saxo-session file
    path = os.path.join(os.path.dirname(__file__), "../temp/.saxo-session")
    if os.path.exists(path):
        print("Deleting temp/.saxo-session")
        os.remove(path)
    pos = saxo.positions()
    assert isinstance(pos, dict) == True
"""
@patch('northy.SaxoTrader.Saxo.positions')
def test_SaxoTrader_trade(mock_positions_method):
    # Define the return value of the positions() method
    mock_positions_method.return_value = mock_positions
    pos = saxo.positions()
    #print(pos)
    
    saxo.trade("SPX_FLAT")

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
"""

def test_SaxoTrader_trade_live():
    saxo.trade("SPX_FLAT")

def test_get_stoploss():
    assert saxo_config.get_stoploss("SPX") == 10
    assert saxo_config.get_stoploss("RUT") == 10
    assert saxo_config.get_stoploss("NDX") == 25
    assert saxo_config.get_stoploss("DIJA") == 25
    assert saxo_config.get_stoploss("INVALID") == 9

def test_pretty_print_position():
    positions = {'__count': 5, 'Data': [{'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': -20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': False, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': 'a5e5174e-b2e6-43b6-bdbd-e8d90c85ec3b', 'CorrelationTypes': [], 'ExecutionTimeClose': '2023-07-30T23:59:34.804356Z', 'ExecutionTimeOpen': '2023-08-15T00:35:30.328725Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4494.14, 'OpenPriceIncludingCosts': 4494.14, 'RelatedOpenOrders': [], 'RelatedPositionId': '5016310795', 'SourceOrderId': '5014636405', 'Status': 'Closed', 'Uic': 4913, 'ValueDate': '2023-08-15T00:00:00.000000Z'}, 'PositionId': '5016489308', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateClose': 0.91704, 'ConversionRateOpen': 0.91704, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'ExposureCurrency': 'USD', 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'ProfitLossOnTrade': -1856.8, 'ProfitLossOnTradeInBaseCurrency': -1702.76, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': 5.6}}, {'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': False, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': 'a5e5174e-b2e6-43b6-bdbd-e8d90c85ec3b', 'ExecutionTimeClose': '2023-08-15T00:35:30.328725Z', 'ExecutionTimeOpen': '2023-07-30T23:59:34.804356Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4586.98, 'OpenPriceIncludingCosts': 4586.98, 'RelatedOpenOrders': [], 'RelatedPositionId': '5016489308', 'SourceOrderId': '5014386349', 'Status': 'Closed', 'Uic': 4913, 'ValueDate': '2023-07-31T00:00:00.000000Z'}, 'PositionId': '5016310795', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateClose': 0.91704, 'ConversionRateOpen': 0.909335, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'ExposureCurrency': 'USD', 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'ProfitLossOnTrade': -1856.8, 'ProfitLossOnTradeInBaseCurrency': -1702.76, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': -1862.8}}, {'NetPositionId': '4912__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': -20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '448cee99-656a-4b85-977a-24401f1d2ee3', 'ExecutionTimeOpen': '2023-07-30T22:00:00.212193Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 15743.03, 'OpenPriceIncludingCosts': 15743.03, 'RelatedOpenOrders': [], 'SourceOrderId': '5014359516', 'Status': 'Open', 'Uic': 4912, 'ValueDate': '2023-07-31T00:00:00.000000Z'}, 'PositionId': '5016310271', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.91704, 'ConversionRateOpen': 0.909335, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': 10262.6, 'ProfitLossOnTradeInBaseCurrency': 9411.21, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': 10257.2}}, {'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': 'd692dec4-f69d-4978-adf1-7f5dcc9e532e', 'ExecutionTimeOpen': '2023-07-30T22:00:00.203192Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4584.23, 'OpenPriceIncludingCosts': 4584.23, 'RelatedOpenOrders': [], 'SourceOrderId': '5014385511', 'Status': 'Open', 'Uic': 4913, 'ValueDate': '2023-07-31T00:00:00.000000Z'}, 'PositionId': '5016310265', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.91704, 'ConversionRateOpen': 0.909335, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': -1826.0, 'ProfitLossOnTradeInBaseCurrency': -1674.52, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': -1812.8}}, {'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '50c4933f-3029-40a6-9105-2c5f927dfb57', 'ExecutionTimeOpen': '2023-07-30T22:00:00.199193Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4584.23, 'OpenPriceIncludingCosts': 4584.23, 'RelatedOpenOrders': [], 'SourceOrderId': '5014382816', 'Status': 'Open', 'Uic': 4913, 'ValueDate': '2023-07-31T00:00:00.000000Z'}, 'PositionId': '5016310263', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.91704, 'ConversionRateOpen': 0.909335, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': -1826.0, 'ProfitLossOnTradeInBaseCurrency': -1674.52, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': -1812.6}}]}
    for pos in positions["Data"]:
        saxo.pretty_print_position(position=pos)

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

def test_uic_lookup():
    tickers = saxo_config.config["tickers"]

    # Lookup valid symbols
    for ticker in tickers.keys():
        res = saxo.uic_lookup(symbol=ticker)
        assert isinstance(res, dict)
        assert isinstance(res["Uic"], int)

    # Lookup invalid symbol
    assert saxo.uic_lookup(symbol="INVALID") == None

    # Lookup valid uic
    for ticker in tickers.keys():
        uic = tickers[ticker]["Uic"]
        res = saxo.uic_lookup(uic=uic)
        assert isinstance(res, str)

    # Lookup invalid Uic
    assert saxo.uic_lookup(uic=0) == None

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
    u.write_json(data=invalid_jwt, filename=".saxo-session")

    Saxo()

def test_trade():
    signals = [
        "NDX_TRADE_SHORT_IN_13199_SL_25 ",
        "SPX_SCALEOUT_IN_3809_OUT_4153_POINTS_344",
        "SPX_FLAT",
        "SPX_FLATSTOP",
        "NDX_CLOSED",
        "SPX_LIMIT_LONG_IN_3749_OUT_3739_SL_10",
    ]
    for signal in signals:
        out = saxo.trade(signal=signal)
        print(out)

####################
#### SaxoHelper ####
####################
def test_saxo_helper_generate_closed_positions_report():
    saxo_helper = SaxoHelper()

    # A few closed positions
    # Expected output: {'total_profit_loss': -1856.8, 'count_closed_trades': 1, 'trades_profit_loss': [-1856.8], 'avg_profit_loss': -1856.8, 'date': '2023-08-15'}
    positions = {'__count': 5, 'Data': [{'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': -20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': False, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': 'a5e5174e-b2e6-43b6-bdbd-e8d90c85ec3b', 'CorrelationTypes': [], 'ExecutionTimeClose': '2023-07-30T23:59:34.804356Z', 'ExecutionTimeOpen': '2023-08-15T00:35:30.328725Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4494.14, 'OpenPriceIncludingCosts': 4494.14, 'RelatedOpenOrders': [], 'RelatedPositionId': '5016310795', 'SourceOrderId': '5014636405', 'Status': 'Closed', 'Uic': 4913, 'ValueDate': '2023-08-15T00:00:00.000000Z'}, 'PositionId': '5016489308', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateClose': 0.91704, 'ConversionRateOpen': 0.91704, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'ExposureCurrency': 'USD', 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'ProfitLossOnTrade': -1856.8, 'ProfitLossOnTradeInBaseCurrency': -1702.76, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': 5.6}}, {'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': False, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': 'a5e5174e-b2e6-43b6-bdbd-e8d90c85ec3b', 'ExecutionTimeClose': '2023-08-15T00:35:30.328725Z', 'ExecutionTimeOpen': '2023-07-30T23:59:34.804356Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4586.98, 'OpenPriceIncludingCosts': 4586.98, 'RelatedOpenOrders': [], 'RelatedPositionId': '5016489308', 'SourceOrderId': '5014386349', 'Status': 'Closed', 'Uic': 4913, 'ValueDate': '2023-07-31T00:00:00.000000Z'}, 'PositionId': '5016310795', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateClose': 0.91704, 'ConversionRateOpen': 0.909335, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'ExposureCurrency': 'USD', 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'ProfitLossOnTrade': -1856.8, 'ProfitLossOnTradeInBaseCurrency': -1702.76, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': -1862.8}}, {'NetPositionId': '4912__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': -20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '448cee99-656a-4b85-977a-24401f1d2ee3', 'ExecutionTimeOpen': '2023-07-30T22:00:00.212193Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 15743.03, 'OpenPriceIncludingCosts': 15743.03, 'RelatedOpenOrders': [], 'SourceOrderId': '5014359516', 'Status': 'Open', 'Uic': 4912, 'ValueDate': '2023-07-31T00:00:00.000000Z'}, 'PositionId': '5016310271', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.91704, 'ConversionRateOpen': 0.909335, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': 10262.6, 'ProfitLossOnTradeInBaseCurrency': 9411.21, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': 10257.2}}, {'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': 'd692dec4-f69d-4978-adf1-7f5dcc9e532e', 'ExecutionTimeOpen': '2023-07-30T22:00:00.203192Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4584.23, 'OpenPriceIncludingCosts': 4584.23, 'RelatedOpenOrders': [], 'SourceOrderId': '5014385511', 'Status': 'Open', 'Uic': 4913, 'ValueDate': '2023-07-31T00:00:00.000000Z'}, 'PositionId': '5016310265', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.91704, 'ConversionRateOpen': 0.909335, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': -1826.0, 'ProfitLossOnTradeInBaseCurrency': -1674.52, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': -1812.8}}, {'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '50c4933f-3029-40a6-9105-2c5f927dfb57', 'ExecutionTimeOpen': '2023-07-30T22:00:00.199193Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4584.23, 'OpenPriceIncludingCosts': 4584.23, 'RelatedOpenOrders': [], 'SourceOrderId': '5014382816', 'Status': 'Open', 'Uic': 4913, 'ValueDate': '2023-07-31T00:00:00.000000Z'}, 'PositionId': '5016310263', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.91704, 'ConversionRateOpen': 0.909335, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': -1826.0, 'ProfitLossOnTradeInBaseCurrency': -1674.52, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': -1812.6}}]}
    out = saxo_helper.generate_closed_positions_report(positions=positions)
    assert isinstance(out, dict)
    assert out["total_profit_loss"] == -1856.8
    assert out["count_closed_trades"] == 1
    assert out["trades_profit_loss"] == [-1856.8]
    assert out["avg_profit_loss"] == -1856.8
    assert out["date"] == "2023-08-15"

    # No closed positions
    # Expexted output: {'total_profit_loss': 0, 'count_closed_trades': 0, 'trades_profit_loss': [], 'avg_profit_loss': 'N/A', 'date': '2023-07-31'}
    positions = {'__count': 3, 'Data': [{'NetPositionId': '4912__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': -20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '448cee99-656a-4b85-977a-24401f1d2ee3', 'ExecutionTimeOpen': '2023-07-30T22:00:00.212193Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 15743.03, 'OpenPriceIncludingCosts': 15743.03, 'RelatedOpenOrders': [], 'SourceOrderId': '5014359516', 'Status': 'Open', 'Uic': 4912, 'ValueDate': '2023-07-31T00:00:00.000000Z'}, 'PositionId': '5016310271', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.91702, 'ConversionRateOpen': 0.909335, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': 13923.2, 'ProfitLossOnTradeInBaseCurrency': 12767.85, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': 13959.8}}, {'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': 'd692dec4-f69d-4978-adf1-7f5dcc9e532e', 'ExecutionTimeOpen': '2023-07-30T22:00:00.203192Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4584.23, 'OpenPriceIncludingCosts': 4584.23, 'RelatedOpenOrders': [], 'SourceOrderId': '5014385511', 'Status': 'Open', 'Uic': 4913, 'ValueDate': '2023-07-31T00:00:00.000000Z'}, 'PositionId': '5016310265', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.91702, 'ConversionRateOpen': 0.909335, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': -2949.0, 'ProfitLossOnTradeInBaseCurrency': -2704.29, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': -2943.2}}, {'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '50c4933f-3029-40a6-9105-2c5f927dfb57', 'ExecutionTimeOpen': '2023-07-30T22:00:00.199193Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4584.23, 'OpenPriceIncludingCosts': 4584.23, 'RelatedOpenOrders': [], 'SourceOrderId': '5014382816', 'Status': 'Open', 'Uic': 4913, 'ValueDate': '2023-07-31T00:00:00.000000Z'}, 'PositionId': '5016310263', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.91702, 'ConversionRateOpen': 0.909335, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': -2949.0, 'ProfitLossOnTradeInBaseCurrency': -2704.29, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': -2943.2}}]}
    out = saxo_helper.generate_closed_positions_report(positions=positions)
    assert isinstance(out, dict)
    assert out['total_profit_loss'] == 0
    assert out['count_closed_trades'] == 0
    assert out['trades_profit_loss'] == []
    assert out['avg_profit_loss'] == 'N/A'
    assert out['date'] == '2023-07-31'

def test_saxo_helper_job_generate_closed_positions_report():
    set_env()  # Set environment variables
    saxo_helper = SaxoHelper()
    saxo_helper.job_generate_closed_positions_report(skip=True)

@patch('northy.saxo.datetime')
def test_saxo_helper_job_generate_closed_positions_report_skip_false(mock_datetime):
    # Create a fixed datetime for testing
    fixed_datetime = datetime(2023, 8, 15, 16, 59, 55)
    mock_datetime.now.return_value = fixed_datetime

    # mocking of datetime is required
    saxo_helper = SaxoHelper()
    saxo_helper.job_generate_closed_positions_report(skip=False)
