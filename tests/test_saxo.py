import os
from northy import utils
from northy.config import set_env
from northy.saxo import Saxo, SaxoConfig, SaxoHelper
from unittest.mock import patch, MagicMock
from datetime import datetime

u = utils.Utils()

# Define mock_positions
mock_positions = MagicMock()

path = os.path.join(os.path.dirname(__file__), "mock_data/SaxoTrader_Saxo_positions.json")
mock_positions = u.read_json(path)

# Mock the SaxoTrader.Saxo.positions() method
saxo = Saxo()
saxo_config = SaxoConfig()
saxo_helper = SaxoHelper()

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

def test_filter_positions():
    mock_positions = {'__count': 10, 'Data': [{'NetPositionId': '4912__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 10.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '05d350a0-59dd-4a3f-9e13-70f6c661dd10', 'ExecutionTimeOpen': '2023-08-28T01:20:01.443490Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 14969.68, 'OpenPriceIncludingCosts': 14969.68, 'RelatedOpenOrders': [], 'SourceOrderId': '5014822497', 'Status': 'Open', 'Uic': 4912, 'ValueDate': '2023-08-28T00:00:00.000000Z'}, 'PositionId': '5016641670', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.92502, 'ConversionRateOpen': 0.92502, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': -340.0, 'ProfitLossOnTradeInBaseCurrency': -314.51, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}, {'NetPositionId': '4912__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 10.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': False, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '05d350a0-59dd-4a3f-9e13-70f6c661dd10', 'CorrelationTypes': [], 'ExecutionTimeClose': '2023-08-28T00:17:01.025587Z', 'ExecutionTimeOpen': '2023-08-28T00:43:16.202366Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 14945.93, 'OpenPriceIncludingCosts': 14945.93, 'RelatedOpenOrders': [], 'RelatedPositionId': '5016641442', 'SourceOrderId': '5014821421', 'Status': 'Closed', 'Uic': 4912, 'ValueDate': '2023-08-28T00:00:00.000000Z'}, 'PositionId': '5016641494', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateClose': 0.92502, 'ConversionRateOpen': 0.92502, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'ExposureCurrency': 'USD', 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'ProfitLossOnTrade': -17.5, 'ProfitLossOnTradeInBaseCurrency': -16.19, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}, {'NetPositionId': '4912__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': -10.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': False, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '05d350a0-59dd-4a3f-9e13-70f6c661dd10', 'ExecutionTimeClose': '2023-08-28T00:43:16.202366Z', 'ExecutionTimeOpen': '2023-08-28T00:17:01.025587Z', 'IsForceOpen': False, 
'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 14944.18, 'OpenPriceIncludingCosts': 14944.18, 'RelatedOpenOrders': [], 'RelatedPositionId': '5016641494', 'SourceOrderId': '5014822496', 'Status': 'Closed', 'Uic': 4912, 'ValueDate': '2023-08-28T00:00:00.000000Z'}, 'PositionId': '5016641442', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateClose': 0.92502, 'ConversionRateOpen': 0.92502, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'ExposureCurrency': 'USD', 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'ProfitLossOnTrade': -17.5, 'ProfitLossOnTradeInBaseCurrency': -16.19, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}, {'NetPositionId': '4912__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': -10.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '840806ca-8d19-43a8-af26-87666c05d616', 'ExecutionTimeOpen': '2023-08-27T23:21:04.255830Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 14969.18, 'OpenPriceIncludingCosts': 14969.18, 'RelatedOpenOrders': [], 'SourceOrderId': '5014821343', 'Status': 'Open', 'Uic': 4912, 'ValueDate': '2023-08-28T00:00:00.000000Z'}, 'PositionId': '5016641034', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.92502, 'ConversionRateOpen': 0.92502, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': 320.0, 'ProfitLossOnTradeInBaseCurrency': 296.01, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}, {'NetPositionId': '31933__CfdOnShare', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 10.0, 'AssetType': 'CfdOnEtf', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': 'f0f5766b-47b1-428a-90c4-fd9ae169792c', 'ExecutionTimeOpen': '2023-08-23T19:55:33.469962Z', 'IsForceOpen': True, 'IsMarketOpen': False, 'LockedByBackOffice': False, 'OpenPrice': 185.55, 'OpenPriceIncludingCosts': 187.55, 'RelatedOpenOrders': [], 'SourceOrderId': '5014774358', 'Status': 'Open', 'Uic': 31933, 'ValueDate': '2023-08-23T00:00:00.000000Z'}, 'PositionId': '5016591112', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.0, 'ConversionRateOpen': 0.0, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 0, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Closed', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': 0.0, 'ProfitLossOnTradeInBaseCurrency': 0.0, 'TradeCostsTotal': -20.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}, {'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 65.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': 
'0308e234-1466-4640-822c-14f0c88e448f', 'ExecutionTimeOpen': '2023-08-23T16:30:18.391908Z', 'IsForceOpen': True, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4428.3, 'OpenPriceIncludingCosts': 4428.3, 'RelatedOpenOrders': [], 'SourceOrderId': '5014774367', 'Status': 'Open', 'Uic': 4913, 'ValueDate': '2023-08-23T00:00:00.000000Z'}, 'PositionId': '5016589400', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.92502, 'ConversionRateOpen': 0.92048, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': -1472.25, 'ProfitLossOnTradeInBaseCurrency': -1361.86, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}, {'NetPositionId': '4912__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': -5.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': 
'388bda32-9ac7-4ffb-8e1a-e8a2b23a8ae6', 'ExecutionTimeOpen': '2023-08-23T16:29:42.949596Z', 'IsForceOpen': True, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 15123.18, 'OpenPriceIncludingCosts': 15123.18, 'RelatedOpenOrders': [{'Amount': 5.0, 'Duration': {'DurationType': 'GoodTillCancel'}, 'OpenOrderType': 'StopIfTraded', 'OrderId': '5014822533', 'OrderPrice': 15123.18, 'Status': 'Working'}], 'SourceOrderId': '5014774363', 'Status': 'Open', 'Uic': 4912, 'ValueDate': '2023-08-23T00:00:00.000000Z'}, 
'PositionId': '5016589390', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.92502, 'ConversionRateOpen': 0.92048, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 
0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': 930.0, 'ProfitLossOnTradeInBaseCurrency': 860.27, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}, {'NetPositionId': '4912__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 10.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '387f1155-32db-4be2-ac34-c2c706e8e3d6', 'ExecutionTimeOpen': '2023-08-16T04:46:57.420175Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 15042.79, 'OpenPriceIncludingCosts': 15042.79, 'RelatedOpenOrders': [], 'SourceOrderId': '5014660386', 'Status': 'Open', 'Uic': 4912, 'ValueDate': '2023-08-16T00:00:00.000000Z'}, 
'PositionId': '5016504110', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.92502, 'ConversionRateOpen': 0.919175, 'CurrentPrice': 
0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': -1071.1, 'ProfitLossOnTradeInBaseCurrency': -990.79, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}, {'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': 'd692dec4-f69d-4978-adf1-7f5dcc9e532e', 'ExecutionTimeOpen': '2023-07-30T22:00:00.203192Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4584.23, 'OpenPriceIncludingCosts': 4584.23, 'RelatedOpenOrders': [], 'SourceOrderId': '5014385511', 'Status': 'Open', 'Uic': 4913, 'ValueDate': '2023-07-31T00:00:00.000000Z'}, 'PositionId': '5016310265', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.92502, 'ConversionRateOpen': 0.909335, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': -3571.6, 'ProfitLossOnTradeInBaseCurrency': -3303.8, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}, {'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 
'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '50c4933f-3029-40a6-9105-2c5f927dfb57', 'ExecutionTimeOpen': '2023-07-30T22:00:00.199193Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4584.23, 'OpenPriceIncludingCosts': 4584.23, 'RelatedOpenOrders': [], 'SourceOrderId': '5014382816', 'Status': 'Open', 'Uic': 4913, 'ValueDate': '2023-07-31T00:00:00.000000Z'}, 'PositionId': '5016310263', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.92502, 'ConversionRateOpen': 0.909335, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': -3571.6, 'ProfitLossOnTradeInBaseCurrency': -3303.8, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}]}

    # Preload filter_positions
    filter_positions = saxo_helper.filter_positions

    # No filter
    positions = filter_positions(mock_positions, cfd_only=False, profit_only=False, symbol=None, status_open=True)
    assert isinstance(positions, dict)
    assert positions["__count"] == 8

    # Filter by symbol
    positions = filter_positions(mock_positions, symbol="SPX", profit_only=False)
    assert isinstance(positions, dict)
    assert positions["__count"] == 3

    # Filter by profit_only
    positions = filter_positions(mock_positions, cfd_only=False, profit_only=True, status_open=False)
    assert isinstance(positions, dict)
    assert positions["__count"] == 2

    saxo_helper.pprint_positions(positions)

def test_positions_without_session_file():
    # delete temp/.saxo-session file
    path = os.path.join(os.path.dirname(__file__), "../temp/.saxo-session")
    if os.path.exists(path):
        print("Deleting temp/.saxo-session")
        os.remove(path)
    pos = saxo.positions()
    assert isinstance(pos, dict) == True

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

def test_pprint_position():
    mock_positions = {'__count': 5, 'Data': [{'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': -20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': False, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': 'a5e5174e-b2e6-43b6-bdbd-e8d90c85ec3b', 'CorrelationTypes': [], 'ExecutionTimeClose': '2023-07-30T23:59:34.804356Z', 'ExecutionTimeOpen': '2023-08-15T00:35:30.328725Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4494.14, 'OpenPriceIncludingCosts': 4494.14, 'RelatedOpenOrders': [], 'RelatedPositionId': '5016310795', 'SourceOrderId': '5014636405', 'Status': 'Closed', 'Uic': 4913, 'ValueDate': '2023-08-15T00:00:00.000000Z'}, 'PositionId': '5016489308', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateClose': 0.91704, 'ConversionRateOpen': 0.91704, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'ExposureCurrency': 'USD', 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'ProfitLossOnTrade': -1856.8, 'ProfitLossOnTradeInBaseCurrency': -1702.76, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': 5.6}}, {'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': False, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': 'a5e5174e-b2e6-43b6-bdbd-e8d90c85ec3b', 'ExecutionTimeClose': '2023-08-15T00:35:30.328725Z', 'ExecutionTimeOpen': '2023-07-30T23:59:34.804356Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4586.98, 'OpenPriceIncludingCosts': 4586.98, 'RelatedOpenOrders': [], 'RelatedPositionId': '5016489308', 'SourceOrderId': '5014386349', 'Status': 'Closed', 'Uic': 4913, 'ValueDate': '2023-07-31T00:00:00.000000Z'}, 'PositionId': '5016310795', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateClose': 0.91704, 'ConversionRateOpen': 0.909335, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'ExposureCurrency': 'USD', 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'ProfitLossOnTrade': -1856.8, 'ProfitLossOnTradeInBaseCurrency': -1702.76, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': -1862.8}}, {'NetPositionId': '4912__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': -20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '448cee99-656a-4b85-977a-24401f1d2ee3', 'ExecutionTimeOpen': '2023-07-30T22:00:00.212193Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 15743.03, 'OpenPriceIncludingCosts': 15743.03, 'RelatedOpenOrders': [], 'SourceOrderId': '5014359516', 'Status': 'Open', 'Uic': 4912, 'ValueDate': '2023-07-31T00:00:00.000000Z'}, 'PositionId': '5016310271', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.91704, 'ConversionRateOpen': 0.909335, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': 10262.6, 'ProfitLossOnTradeInBaseCurrency': 9411.21, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': 10257.2}}, {'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': 'd692dec4-f69d-4978-adf1-7f5dcc9e532e', 'ExecutionTimeOpen': '2023-07-30T22:00:00.203192Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4584.23, 'OpenPriceIncludingCosts': 4584.23, 'RelatedOpenOrders': [], 'SourceOrderId': '5014385511', 'Status': 'Open', 'Uic': 4913, 'ValueDate': '2023-07-31T00:00:00.000000Z'}, 'PositionId': '5016310265', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.91704, 'ConversionRateOpen': 0.909335, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': -1826.0, 'ProfitLossOnTradeInBaseCurrency': -1674.52, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': -1812.8}}, {'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '50c4933f-3029-40a6-9105-2c5f927dfb57', 'ExecutionTimeOpen': '2023-07-30T22:00:00.199193Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4584.23, 'OpenPriceIncludingCosts': 4584.23, 'RelatedOpenOrders': [], 'SourceOrderId': '5014382816', 'Status': 'Open', 'Uic': 4913, 'ValueDate': '2023-07-31T00:00:00.000000Z'}, 'PositionId': '5016310263', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.91704, 'ConversionRateOpen': 0.909335, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': -1826.0, 'ProfitLossOnTradeInBaseCurrency': -1674.52, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0, 'ProfitLossOnTradeAdjusted': -1812.6}}]}
    saxo_helper.pprint_positions(mock_positions["Data"])

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

def test_cancel_order():
    # Invalid Order
    out = saxo.cancel_order(orders="123456789")
    assert out.status_code == 404

    # Valid Order
    # TODO

def test_close():
    # Possible responses:
    # Closed position: Response(status_code=200, json={'Orders': [{'OrderId': '5014821421'}]})
    # Invalid Position: Response(status_code=400, json={'Orders': [{'ErrorInfo': {'ErrorCode': 'OrderRelatedPositionNotFound', 'Message': 'Related position not found'}}]})
    # Already Closed: Response(status_code=400, json={'Orders': [{'ErrorInfo': {'ErrorCode': 'OrderRelatedPositionIsClosed', 'Message': 'Related position already closed'}}]}) 

    # Already Closed
    mock_position = {'NetPositionId': '4912__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': -10.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '05d350a0-59dd-4a3f-9e13-70f6c661dd10', 'ExecutionTimeOpen': '2023-08-28T00:17:01.025587Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 14944.18, 'OpenPriceIncludingCosts': 14944.18, 'RelatedOpenOrders': [], 'SourceOrderId': '5014822496', 'Status': 'Open', 'Uic': 4912, 'ValueDate': '2023-08-28T00:00:00.000000Z'}, 'PositionId': '5016641442', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.925885, 'ConversionRateOpen': 0.925885, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': 10.7, 'ProfitLossOnTradeInBaseCurrency': 9.91, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}
    out = saxo.close(position=mock_position)
    assert isinstance(out.json, dict)
    assert out.status_code == 400

    # Invalid Position
    mock_position = {'NetPositionId': '4912__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': -10.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '05d350a0-59dd-4a3f-9e13-70f6c661dd10', 'ExecutionTimeOpen': '2023-08-28T00:17:01.025587Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 14944.18, 'OpenPriceIncludingCosts': 14944.18, 'RelatedOpenOrders': [], 'SourceOrderId': '5014822496', 'Status': 'Open', 'Uic': 4912, 'ValueDate': '2023-08-28T00:00:00.000000Z'}, 'PositionId': '5016641000', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.925885, 'ConversionRateOpen': 0.925885, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': 10.7, 'ProfitLossOnTradeInBaseCurrency': 9.91, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}
    out = saxo.close(position=mock_position)
    assert isinstance(out.json, dict)
    assert out.status_code == 400
    print(out)

def test_uic_to_symbol():
    # Valid Uic
    assert saxo_helper.uic_to_symbol(4912) == "NDX"

    # Invalid Uic
    assert saxo_helper.uic_to_symbol(0) == None

def test_symbol_to_uic():
    saxo_helper = SaxoHelper()
    # Valid Symbol
    assert saxo_helper.symbol_to_uic("SPX") == 4913
    assert saxo_helper.symbol_to_uic("NDX") == 4912

    # Invalid Symbol
    assert saxo_helper.symbol_to_uic("INVALID") == None

def test_helper_pretty_print_position():
    # Mock position
    # NDX, Amount:10, Profit:
    positions = [{'NetPositionId':'4912__CfdOnIndex','PositionBase':{'AccountId':'17470793','AccountKey':'wlgQxI5-JzdhnV4s6BsDiA==','Amount':10.0,'AssetType':'CfdOnIndex','CanBeClosed':True,'ClientId':'17470793','CloseConversionRateSettled':False,'CorrelationKey':'05d350a0-59dd-4a3f-9e13-70f6c661dd10','ExecutionTimeOpen':'2023-08-28T01:20:01.443490Z','IsForceOpen':False,'IsMarketOpen':True,'LockedByBackOffice':False,'OpenPrice':14969.68,'OpenPriceIncludingCosts':14969.68,'RelatedOpenOrders':[],'SourceOrderId':'5014822497','Status':'Open','Uic':4912,'ValueDate':'2023-08-28T00:00:00.000000Z'},'PositionId':'5016641670','PositionView':{'CalculationReliability':'ApproximatedPrice','ConversionRateCurrent':0.925235,'ConversionRateOpen':0.925235,'CurrentPrice':0.0,'CurrentPriceDelayMinutes':15,'CurrentPriceType':'None','Exposure':0.0,'ExposureCurrency':'USD','ExposureInBaseCurrency':0.0,'InstrumentPriceDayPercentChange':0.0,'MarketState':'Open','MarketValue':0.0,'MarketValueInBaseCurrency':0.0,'ProfitLossOnTrade':-182.9,'ProfitLossOnTradeInBaseCurrency':-169.23,'TradeCostsTotal':0.0,'TradeCostsTotalInBaseCurrency':0.0,'UnderlyingCurrentPrice':0.0}}]
    saxo_helper.pprint_positions(positions)

    mock_positions = [{'NetPositionId': '4912__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 10.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '05d350a0-59dd-4a3f-9e13-70f6c661dd10', 'ExecutionTimeOpen': '2023-08-28T01:20:01.443490Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 14969.68, 'OpenPriceIncludingCosts': 14969.68, 'RelatedOpenOrders': [], 'SourceOrderId': '5014822497', 'Status': 'Open', 'Uic': 4912, 'ValueDate': '2023-08-28T00:00:00.000000Z'}, 'PositionId': '5016641670', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.925235, 'ConversionRateOpen': 0.925235, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': -182.9, 'ProfitLossOnTradeInBaseCurrency': -169.23, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}, {'NetPositionId': '4912__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 10.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': False, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '05d350a0-59dd-4a3f-9e13-70f6c661dd10', 'CorrelationTypes': [], 'ExecutionTimeClose': '2023-08-28T00:17:01.025587Z', 'ExecutionTimeOpen': '2023-08-28T00:43:16.202366Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 14945.93, 'OpenPriceIncludingCosts': 14945.93, 'RelatedOpenOrders': [], 'RelatedPositionId': '5016641442', 'SourceOrderId': '5014821421', 'Status': 'Closed', 'Uic': 4912, 'ValueDate': '2023-08-28T00:00:00.000000Z'}, 'PositionId': '5016641494', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateClose': 0.925235, 'ConversionRateOpen': 0.925235, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'ExposureCurrency': 'USD', 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'ProfitLossOnTrade': -17.5, 'ProfitLossOnTradeInBaseCurrency': -16.19, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}, {'NetPositionId': '4912__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': -10.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': False, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '05d350a0-59dd-4a3f-9e13-70f6c661dd10', 'ExecutionTimeClose': '2023-08-28T00:43:16.202366Z', 'ExecutionTimeOpen': '2023-08-28T00:17:01.025587Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 14944.18, 'OpenPriceIncludingCosts': 14944.18, 'RelatedOpenOrders': [], 'RelatedPositionId': '5016641494', 'SourceOrderId': '5014822496', 'Status': 'Closed', 'Uic': 4912, 'ValueDate': '2023-08-28T00:00:00.000000Z'}, 'PositionId': '5016641442', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateClose': 0.925235, 'ConversionRateOpen': 0.925235, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 
'ExposureCurrency': 'USD', 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'ProfitLossOnTrade': -17.5, 'ProfitLossOnTradeInBaseCurrency': -16.19, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}, {'NetPositionId': '4912__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': -10.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '840806ca-8d19-43a8-af26-87666c05d616', 'ExecutionTimeOpen': '2023-08-27T23:21:04.255830Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 14969.18, 'OpenPriceIncludingCosts': 14969.18, 'RelatedOpenOrders': [], 'SourceOrderId': '5014821343', 'Status': 'Open', 'Uic': 4912, 'ValueDate': '2023-08-28T00:00:00.000000Z'}, 'PositionId': '5016641034', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.925235, 'ConversionRateOpen': 0.925235, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': 165.4, 'ProfitLossOnTradeInBaseCurrency': 153.03, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}, {'NetPositionId': '31933__CfdOnShare', 'PositionBase': {'AccountId': 
'17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 10.0, 'AssetType': 'CfdOnEtf', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': 'f0f5766b-47b1-428a-90c4-fd9ae169792c', 'ExecutionTimeOpen': '2023-08-23T19:55:33.469962Z', 'IsForceOpen': True, 'IsMarketOpen': False, 'LockedByBackOffice': False, 'OpenPrice': 185.55, 'OpenPriceIncludingCosts': 187.55, 'RelatedOpenOrders': [], 'SourceOrderId': '5014774358', 'Status': 'Open', 'Uic': 31933, 'ValueDate': '2023-08-23T00:00:00.000000Z'}, 'PositionId': '5016591112', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.0, 'ConversionRateOpen': 0.0, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 0, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Closed', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': 0.0, 'ProfitLossOnTradeInBaseCurrency': 0.0, 'TradeCostsTotal': -20.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}, {'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 65.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '0308e234-1466-4640-822c-14f0c88e448f', 'ExecutionTimeOpen': '2023-08-23T16:30:18.391908Z', 'IsForceOpen': True, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4428.3, 'OpenPriceIncludingCosts': 4428.3, 'RelatedOpenOrders': [], 'SourceOrderId': '5014774367', 'Status': 'Open', 'Uic': 4913, 'ValueDate': '2023-08-23T00:00:00.000000Z'}, 'PositionId': '5016589400', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.925235, 'ConversionRateOpen': 0.92048, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': -1279.85, 'ProfitLossOnTradeInBaseCurrency': -1184.16, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}, {'NetPositionId': '4912__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': -5.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '388bda32-9ac7-4ffb-8e1a-e8a2b23a8ae6', 'ExecutionTimeOpen': '2023-08-23T16:29:42.949596Z', 'IsForceOpen': True, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 15123.18, 'OpenPriceIncludingCosts': 15123.18, 'RelatedOpenOrders': [{'Amount': 5.0, 'Duration': {'DurationType': 'GoodTillCancel'}, 'OpenOrderType': 'StopIfTraded', 'OrderId': '5014822533', 'OrderPrice': 15123.18, 'Status': 'Working'}], 'SourceOrderId': '5014774363', 'Status': 'Open', 'Uic': 4912, 'ValueDate': '2023-08-23T00:00:00.000000Z'}, 'PositionId': '5016589390', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.925235, 'ConversionRateOpen': 0.92048, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': 852.7, 'ProfitLossOnTradeInBaseCurrency': 788.95, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}, {'NetPositionId': '4912__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 10.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '387f1155-32db-4be2-ac34-c2c706e8e3d6', 'ExecutionTimeOpen': '2023-08-16T04:46:57.420175Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 15042.79, 'OpenPriceIncludingCosts': 15042.79, 'RelatedOpenOrders': [], 'SourceOrderId': '5014660386', 'Status': 'Open', 'Uic': 4912, 'ValueDate': '2023-08-16T00:00:00.000000Z'}, 'PositionId': '5016504110', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.925235, 'ConversionRateOpen': 0.919175, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': -914.0, 'ProfitLossOnTradeInBaseCurrency': -845.66, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}, {'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': 'd692dec4-f69d-4978-adf1-7f5dcc9e532e', 'ExecutionTimeOpen': '2023-07-30T22:00:00.203192Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4584.23, 'OpenPriceIncludingCosts': 4584.23, 'RelatedOpenOrders': [], 'SourceOrderId': '5014385511', 'Status': 'Open', 'Uic': 4913, 'ValueDate': '2023-07-31T00:00:00.000000Z'}, 'PositionId': '5016310265', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.925235, 'ConversionRateOpen': 0.909335, 'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': -3512.4, 'ProfitLossOnTradeInBaseCurrency': -3249.8, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}, {'NetPositionId': '4913__CfdOnIndex', 'PositionBase': {'AccountId': '17470793', 'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==', 'Amount': 20.0, 'AssetType': 'CfdOnIndex', 'CanBeClosed': True, 'ClientId': '17470793', 'CloseConversionRateSettled': False, 'CorrelationKey': '50c4933f-3029-40a6-9105-2c5f927dfb57', 'ExecutionTimeOpen': '2023-07-30T22:00:00.199193Z', 'IsForceOpen': False, 'IsMarketOpen': True, 'LockedByBackOffice': False, 'OpenPrice': 4584.23, 'OpenPriceIncludingCosts': 4584.23, 'RelatedOpenOrders': [], 'SourceOrderId': '5014382816', 'Status': 'Open', 'Uic': 4913, 'ValueDate': '2023-07-31T00:00:00.000000Z'}, 'PositionId': '5016310263', 'PositionView': {'CalculationReliability': 'ApproximatedPrice', 'ConversionRateCurrent': 0.925235, 'ConversionRateOpen': 0.909335, 
'CurrentPrice': 0.0, 'CurrentPriceDelayMinutes': 15, 'CurrentPriceType': 'None', 'Exposure': 0.0, 'ExposureCurrency': 'USD', 'ExposureInBaseCurrency': 0.0, 'InstrumentPriceDayPercentChange': 0.0, 'MarketState': 'Open', 'MarketValue': 0.0, 'MarketValueInBaseCurrency': 0.0, 'ProfitLossOnTrade': -3512.4, 'ProfitLossOnTradeInBaseCurrency': -3249.8, 'TradeCostsTotal': 0.0, 'TradeCostsTotalInBaseCurrency': 0.0, 'UnderlyingCurrentPrice': 0.0}}]
    
    saxo_helper.pprint_positions(mock_positions)

def test_price():
    # Valid symbol
    _id = saxo_helper.symbol_to_uic("NDX")
    assert isinstance(saxo.price(_id), dict)

    # Invalid symbol
    out = saxo.price(123)
    assert out["ErrorCode"] == "IllegalInstrumentId"

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

####################
#### SaxoHelper ####
####################
def test_saxo_helper_generate_closed_positions_report():
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
