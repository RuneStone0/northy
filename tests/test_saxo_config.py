import os
from northy import utils
from northy.config import set_env
from northy.saxo import SaxoHelper
from datetime import datetime
from unittest.mock import patch, MagicMock

saxo_helper = SaxoHelper()
u = utils.Utils()

def get_mock_data(filename):
    dir = os.path.dirname(__file__)
    file_path = f"mock_data/saxo_config/{filename}"
    path = os.path.join(dir, file_path)
    return u.read_json(path)

def test_pprint_positions():
    positions = get_mock_data("positions.json")
    saxo_helper.pprint_positions(positions)

def test_get_position_stop_details():
    # Test #0 - long position, no stops set
    position = {'NetPositionId': '4912__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': -5.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '388bda32-9ac7-4ffb-8e1a-e8a2b23a8ae6', 'ExecutionTimeOpen': '2023-08-23T16:29:42.949596Z', 'IsForceOpen': True, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 15123.18, 'OpenPriceIncludingCosts': 15123.18, 'SourceOrderId': '5014774363', 'Status': 'Open', 'Uic': 4912, 'ValueDate': '2023-08-23T00:00:00.000000Z'}, 'PositionId': '5016589390', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.923035, 'ConversionRateOpen': 0.92048, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': 314.65, 'ProfitLossOnTradeInBaseCurrency': 290.43, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': 287.25}}
    expected_output = {'stop': False, 'stop_price': 0, 'stop_points': 0}
    out = saxo_helper.get_position_stop_details(position)
    assert isinstance(out, dict)
    assert out == expected_output

    # Test #1 - long position, only stop set
    position = {'NetPositionId': '4912__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': -5.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '388bda32-9ac7-4ffb-8e1a-e8a2b23a8ae6', 'ExecutionTimeOpen': '2023-08-23T16:29:42.949596Z', 'IsForceOpen': True, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 15123.18, 'OpenPriceIncludingCosts': 15123.18, 'RelatedOpenOrders': [{'Amount': 5.0, 'Duration': {'DurationType': 'GoodTillCancel'}, 'OpenOrderType': 'StopIfTraded', 'OrderId': '5014822533', 'OrderPrice': 15123.18, 'Status': 'Working'}], 'SourceOrderId': '5014774363', 'Status': 'Open', 'Uic': 4912, 'ValueDate': '2023-08-23T00:00:00.000000Z'}, 'PositionId': '5016589390', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.923035, 'ConversionRateOpen': 0.92048, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': 314.65, 'ProfitLossOnTradeInBaseCurrency': 290.43, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': 287.25}}
    expected_output = {'stop': True, 'stop_price': 15123.18, 'stop_points': 0.0}
    out = saxo_helper.get_position_stop_details(position)
    assert isinstance(out, dict)
    assert out == expected_output

    # Test #2 - long position, stop and limit set
    position = {'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 65.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '0308e234-1466-4640-822c-14f0c88e448f', 'ExecutionTimeOpen': '2023-08-23T16:30:18.391908Z', 'IsForceOpen': True, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4428.3, 'OpenPriceIncludingCosts': 4428.3, 'RelatedOpenOrders': [{'Amount': 65.0, 'Duration': {'DurationType': 'GoodTillCancel'}, 'OpenOrderType': 'StopIfTraded', 'OrderId': '5014839916', 'OrderPrice': 4428.3, 'Status': 'Working'}, {'Amount': 65.0, 'Duration': {'DurationType': 'GoodTillCancel'}, 'OpenOrderType': 'Limit', 'OrderId': '5014841606', 'OrderPrice': 4526.17, 'Status': 'Working'}], 'SourceOrderId': '5014774367', 'Status': 'Open', 'Uic': 4913, 'ValueDate': '2023-08-23T00:00:00.000000Z'}, 'PositionId': '5016589400', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.923025, 'ConversionRateOpen': 0.92048, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': 388.7, 'ProfitLossOnTradeInBaseCurrency': 358.78, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': 574.6}}
    expected_output = {'stop': True, 'stop_price': 4428.3, 'stop_points': 0.0}
    out = saxo_helper.get_position_stop_details(position)
    assert isinstance(out, dict)
    assert out == expected_output

    # Test #3 - long position, stop 25 points away
    position = {'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 65.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '0308e234-1466-4640-822c-14f0c88e448f', 'ExecutionTimeOpen': '2023-08-23T16:30:18.391908Z', 'IsForceOpen': True, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4428.3, 'OpenPriceIncludingCosts': 4428.3, 'RelatedOpenOrders': [{'Amount': 65.0, 'Duration': {'DurationType': 'GoodTillCancel'}, 'OpenOrderType': 'StopIfTraded', 'OrderId': '5014839916', 'OrderPrice': 4428.3, 'Status': 'Working'}, {'Amount': 65.0, 'Duration': {'DurationType': 'GoodTillCancel'}, 'OpenOrderType': 'Limit', 'OrderId': '5014841606', 'OrderPrice': 4526.17, 'Status': 'Working'}], 'SourceOrderId': '5014774367', 'Status': 'Open', 'Uic': 4913, 'ValueDate': '2023-08-23T00:00:00.000000Z'}, 'PositionId': '5016589400', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.923025, 'ConversionRateOpen': 0.92048, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': 388.7, 'ProfitLossOnTradeInBaseCurrency': 358.78, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': 574.6}}
    position["PositionBase"]["OpenPrice"] -= 25
    expected_output = {'stop': True, 'stop_price': 4428.3, 'stop_points': -25.0}
    out = saxo_helper.get_position_stop_details(position)
    assert isinstance(out, dict)
    assert out == expected_output

def test_filter_positions():
    # Get and test mock data
    positions = get_mock_data("filter_pos.json")
    assert isinstance(positions, dict)
    assert positions["__count"] == 10

    # Preload filter_positions
    filter_positions = saxo_helper.filter_positions

    # No filter
    new_pos = filter_positions(positions, cfd_only=False, profit_only=False)
    assert isinstance(new_pos, dict)
    assert new_pos["__count"] == 8

    # Default filter options
    new_pos = filter_positions(positions)
    assert isinstance(new_pos, dict)
    assert new_pos["__count"] == 2

    # Filter by symbol
    new_pos = filter_positions(positions, symbol="SPX", profit_only=False)
    assert isinstance(new_pos, dict)
    assert new_pos["__count"] == 3

    # Filter by profit_only
    new_pos = filter_positions(positions, cfd_only=False, status_open=False)
    assert isinstance(new_pos, dict)
    assert new_pos["__count"] == 2

    saxo_helper.pprint_positions(new_pos)

def test_uic_to_symbol():
    # Valid Uic
    assert saxo_helper.uic_to_symbol(4912) == "NDX"

    # Invalid Uic
    assert saxo_helper.uic_to_symbol(0) == "N/A"

def test_symbol_to_uic():
    saxo_helper = SaxoHelper()
    # Valid Symbol
    assert saxo_helper.symbol_to_uic("SPX") == 4913
    assert saxo_helper.symbol_to_uic("NDX") == 4912

    # Invalid Symbol
    assert saxo_helper.symbol_to_uic("INVALID") == None

def test_generate_closed_positions_report():
    # A few closed positions
    # Expected output: {
    #   'total_profit_loss': -1856.8, 'count_closed_trades': 1,
    #   'trades_profit_loss': [-1856.8], 'avg_profit_loss': -1856.8, 
    #   'date': '2023-08-15'
    # }
    positions = get_mock_data("few_pos_closed.json")
    out = saxo_helper.generate_closed_positions_report(positions=positions)
    assert isinstance(out, dict)
    assert out["total_profit_loss"] == -1856.8
    assert out["count_closed_trades"] == 1
    assert out["trades_profit_loss"] == [-1856.8]
    assert out["avg_profit_loss"] == -1856.8
    assert out["date"] == "2023-08-15"

    # No closed positions
    # Expexted output: {
    #   'total_profit_loss': 0, 'count_closed_trades': 0, 
    #   'trades_profit_loss': [], 'avg_profit_loss': 'N/A', 
    #   'date': '2023-07-31'
    # }
    positions = get_mock_data("no_closed_pos.json")
    out = saxo_helper.generate_closed_positions_report(positions=positions)
    assert isinstance(out, dict)
    assert out['total_profit_loss'] == 0
    assert out['count_closed_trades'] == 0
    assert out['trades_profit_loss'] == []
    assert out['avg_profit_loss'] == 'N/A'
    assert out['date'] == '2023-07-31'

def test_job_generate_closed_positions_report():
    set_env()  # Set environment variables
    positions = get_mock_data("positions.json")
    saxo_helper.job_generate_closed_positions_report(positions, skip=True)

@patch('northy.saxo.datetime')
def test_job_generate_closed_positions_report_skip_false(mock_datetime):
    # Create a fixed datetime for testing
    mock_datetime.now.return_value = datetime(2023, 8, 15, 16, 59, 55)

    # mocking of datetime is required
    positions = get_mock_data("SaxoTrader_Saxo_positions.json")
    saxo_helper.job_generate_closed_positions_report(positions, skip=False)
