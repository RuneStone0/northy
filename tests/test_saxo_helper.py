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

def test_symbol_to_uic2():
    # Valid Symbol
    assert saxo_helper.symbol_to_uic("SPX") == 4913
    assert saxo_helper.symbol_to_uic("NDX") == 4912

    # Invalid Symbol
    assert saxo_helper.symbol_to_uic("INVALID") == None

def test_uic_to_symbol():
    # Valid Uic
    assert saxo_helper.uic_to_symbol(4912) == "NDX"
    assert saxo_helper.uic_to_symbol(4913) == "SPX"
    assert isinstance(saxo_helper.uic_to_symbol(4913), str)

    # Invalid Uic
    assert saxo_helper.uic_to_symbol(0) == "N/A"
    invalid = saxo_helper.uic_to_symbol("000")
    assert invalid == "N/A"

def test_get_position_stop_details():
    positions = get_mock_data("positions.json")["Data"][0]
    details = saxo_helper.get_position_stop_details(positions)
    assert isinstance(details, dict)
    assert details["stop_price"] == 4148.49

def test_get_position_stop_details2():
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

def test_pprint_positions():
    positions = get_mock_data("positions.json")
    saxo_helper.pprint_positions(positions)

def test_filter_positions():
    positions = get_mock_data("positions.json")
    positions_filtered = saxo_helper.filter_positions(positions, cfd_only=True)
    assert positions_filtered["__count"] == 2

def test_filter_positions2():
    # Get and test mock data
    positions = get_mock_data("filter_pos.json")
    assert isinstance(positions, dict)
    assert positions["__count"] == 10

    # Preload filter_positions
    filter_positions = saxo_helper.filter_positions

    # No filter
    new_pos = filter_positions(positions, cfd_only=False, profit_only=False)
    assert isinstance(new_pos, dict)
    assert new_pos["__count"] == 9

    # Default filter options
    new_pos = filter_positions(positions)
    assert isinstance(new_pos, dict)
    assert new_pos["__count"] == 2

    # Filter by symbol
    new_pos = filter_positions(positions, symbol="SPX", profit_only=False)
    assert isinstance(new_pos, dict)
    assert new_pos["__count"] == 3

    # Filter by profit_only
    new_pos = filter_positions(positions, cfd_only=False, profit_only=True)
    assert isinstance(new_pos, dict)
    assert new_pos["__count"] == 2

    saxo_helper.pprint_positions(new_pos)
