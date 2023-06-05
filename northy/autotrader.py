import time
import logging
from collections import namedtuple
from saxo import Trading, Saxo, Helper
from datetime import datetime
import dateutil.parser
import pytz

# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
trading = Trading()
saxo = Saxo()
helper = Helper()

class AutoTrader:
    def __init__(self, db=None) -> None:
        self.db = db
        self.profil = {
            # Saxo Demo Account
            'AccountId': '17470793',
            'AccountKey': 'wlgQxI5-JzdhnV4s6BsDiA==',

            # Set stake size (aka. 100%) for each instrument
            # Scales will be 25% of the stake size defined
            'TradeSize': {
                'NDX': 20.0,
                'SPX': 65.0,
                'RUT': 140.0,
            },

            # Set preferred order type
            # Market, will be executed immediately
            # Limit, will be executed when price is reached (you might risk missing the trade)
            'OrderType': 'Market',
        }

    def __signal_tuple(self, signal):
        """ 
            Convert signal into a namedtuple

            Example signal:
                SPX_TRADE_SHORT_IN_4162_SL_10
                NDX_FLATSTOP
        """
        s = signal.split("_")
        __action = s[1]

        if __action == "TRADE":
            # NDX_TRADE_SHORT_IN_13199_SL_25
            _entry, _sl = float(s[4]), float(s[6])
            return namedtuple("signal", ["symbol", "action", "direction", "entry", "stoploss", "raw"])(s[0], s[1], s[2], _entry, _sl, signal)
        
        if __action == "SCALEOUT":
            # SPX_SCALEOUT_IN_3809_OUT_4153_POINTS_344
            return namedtuple("signal", ["symbol", "action", "entry", "exit", "points", "raw"])(s[0], s[1], s[3], s[5], s[7], signal)

        if __action == "FLAT":
            # SPX_FLAT
            return namedtuple("signal", ["symbol", "action", "raw"])(s[0], s[1], signal)
        
        if __action == "CLOSED":
            # NDX_CLOSED
            return namedtuple("signal", ["symbol", "action", "raw"])(s[0], s[1], signal)
        
        if __action == "LIMIT":
            # SPX_LIMIT_LONG_IN_3749_OUT_3739_SL_10
            _entry, _exit, _sl = float(s[4]), float(s[6]), float(s[8])
            return namedtuple("signal", ["symbol", "action", "direction", "entry", "exit", "stoploss", "raw"])(s[0], s[1], s[2], _entry, _exit, _sl, signal)

    def flat(self):
        """
            Set all profitable positions to flat
        """
        positions = saxo.positions(cfd_only=True, profit_only=True)
        for i in positions["Data"]:
            trading.set_stoploss(position=i, points=0)

    def closed(self):
        """
            Close latest positions that are not flat
        """
        positions = saxo.positions(cfd_only=True, profit_only=False)
        def __position_age(position):
            """
                Return the age of a position in minutes
            """
            p = position
            TZ = pytz.timezone('America/Chicago')
            now = datetime.now().astimezone(TZ)

            ExecutionTimeOpen = p["PositionBase"]["ExecutionTimeOpen"]
            ExecutionTimeOpen = dateutil.parser.parse(ExecutionTimeOpen).astimezone(TZ)
            delta = now - ExecutionTimeOpen
            delta_in_minutes = delta.total_seconds() // 60
            return delta_in_minutes
        
        for p in positions["Data"]:
            helper.pretty_print_position(p)

            # Don't close positions without stoploss
            # Northy positions always have a stoploss, so this should be OK to skip
            if len(p["PositionBase"]["RelatedOpenOrders"]) == 0:
                print("Position does not have a stoploss. Skipping..")
                continue

            # skip if older than 1 hour
            # TODO: Analyze all northy close signals and see if they are all closed within 1 hour
            if __position_age(p) > 60:
                print("Position is older than 1 hour. Skipping..")
                continue

            trading.close(position=p)

    def trade(self, signal_tuple):

        s = signal_tuple
        amount = self.profil["TradeSize"][s.symbol]
        logger.info(f"TRADE: {s.symbol} {s.direction} {amount} @ MARKET PRICE (~{s.entry}) with SL {s.stoploss}")
        buy = True if s.direction == "LONG" else False
        trading.market(symbol=s.symbol, amount=amount, buy=buy, stoploss_points=s.stoploss)

    def process_signal(self, signal):
        """
            Execute trades based on signals
        """
        logger.info(f"Processing signal: {signal}")
        print(signal)
        s = self.__signal_tuple(signal)
        print(s)
        print("====")

        # Determine order action
        if s.action == "TRADE":
            self.trade(signal_tuple=s)
        if s.action == "FLAT":
            self.flat()
        if s.action == "SCALEOUT":
            # TODO
            pass
        if s.action == "CLOSED":
            self.closed()
        if s.action == "FLATSTOP":
            # TODO
            pass
        if s.action == "LIMIT":
            # TODO
            pass
        
        time.sleep(1)  # Max 1 request per second (https://www.developer.saxo/openapi/learn/rate-limiting?phrase=Rate+Limit)

    def watch(self):
        """
            Watch for new signals
        """
        # Start change stream
        logger.info("Starting change stream...")
        while True:
            try:
                # Watch for new documents (tweets) where "alert" is not set
                pipeline = [
                    { "$match": { "operationType": { "$in": ["update"] } } }, # 'insert', 'update', 'replace', 'delete'
                ]
                # Create a change stream
                change_stream = self.db["tweets"].watch(pipeline, full_document='updateLookup')

                # Iterate over the change stream
                for change in change_stream:
                    doc = change["fullDocument"]
                    signals = doc["signals"]
                    tid = doc["tid"]
                    text = doc["text"]
                    logger.info("Detected change for %s", tid)
                    
                    # check if created_at is within the last 5 minutes
                    if doc["created_at"] < (time.time() - 300):
                        logger.info("Tweet is older than 5 minutes. Skipping..")
                        continue

                    # Make sure its an alert
                    # TODO: Move this check to pipeline
                    if not doc["alert"]:
                        logger.info("No alert found. Skipping..")

                    # Initiate trade for signals
                    logger.info(f"Executing trades for {tid}: {text}")
                    for signal in signals:
                        self.process_signal(signal)

            except Exception as e:
                print(f"An error occurred: {e}")

                # Pause for 60 seconds before resuming
                time.sleep(60)

    def run(self):
        self.watch()

if __name__ == "__main__":
    autotrader = AutoTrader()
    
    # Trade
    #autotrader.trade("SPX_TRADE_SHORT_IN_4162_SL_10")
    #autotrader.trade("SPX_TRADE_LONG_IN_4162_SL_10")

    # FLAT
    #autotrader.trade("NDX_FLAT")

    # CLOSE
    autotrader.process_signal("SPX_CLOSED")

