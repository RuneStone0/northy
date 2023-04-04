import re
import sys
import json
from dotenv import dotenv_values
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from termcolor import colored
from datetime import datetime

config = dotenv_values(".env")
database_name = "northy"
tweets_collection_name = "tweets"

class Signal:
    """
        Example:
            NDX_TRADE_LONG_IN_10450_SL_25
        
        Schema:
            {TICKER}_{ACTION}_{DIRECTION}_IN_{PRICE}_SL_{POINTS}
            TICKER_ACTION_DIRECTION_IN_PRICE_SL_POINTS

        Breakdown
            TICKER - the ticker code e.g. SPX
            ACTION - the action to take on a signal
                TRADE       - enter new trade, based on direction we either go long / short
                FLAT        - adjust stop loss to break even
                FLATSTOP    - stop loss was triggered, this is just an observation, no action needed
                CLOSE       - close recently opened position (100% of position)
                SCALEOUT    - scale out of position (25% of position)
                LIMIT       - set a limit order
                STOPLOSS    - set a stop loss order
            DIRECTION - define the position direction
                LONG        - go long a trade (buy)
                SHORT       - go short a trade (sell)
            PRICE - the price at which the signal was entered
            SL - the number of points from which to set the stop loss
    """
    def __init__(self):
        # Environment Variables
        self.config = dotenv_values(".env")

        # MongoDB
        client = MongoClient(self.config["mongodb_conn"], connect=False)
        self.db = client[database_name]
        self.tweets_collection = self.db[tweets_collection_name]

    def __unique(self, sequence):
        """
            Removes duplicates from list() while keeping the original order.
        """
        seen = set()
        return [x for x in sequence if not (x in seen or seen.add(x))]

    def __normalize_text(self, tweet):
        """
            Takes twitter text and cleans it up and normalize the format.

            Input:
                ALERT: stopped $SPX (add-on) Re-entry long IN: 3609 - 10 pt stop
                Weekly 200MA still holding. https://t.co/5rFaGhZuo8
            
            Output:
                ["SPX_TRADE_LONG_IN_3609_SL_10"]
                [""]
        """
        # Clean up string
        text = tweet["text"].replace("\n", " | ")
        text = text.replace("ALERT: ", "")
        text = text.upper() # normalize

        # Fix bug with `| LONG $SPX $NDX | IN 3580 - 10 PT STOP |IN 10900 - 25 PT STOP`   1576847187740266496
        if text.startswith("| "):
            text = text[2:]

        # Fix bug with ("FLAT STOPPED $RUT | RE-ENTRY LONG | IN: 1795 - 10 PT STOP") where "IN:" contains a colon, all other tweets doesn't
        text = text.replace(" IN: ", "IN ")
        return text

    def __pretty_print_signal(self, tweet):
        """
            Print signal in color.
        """
        text = self.__normalize_text(tweet)
        signals = self.text_to_signal(tweet)
        signal_text = ", ".join(signals)

        tid = tweet["tid"]
        tid_color = colored(tid, "blue")

        print(f"{tid_color}", "\t IN ", colored(f"{text}\n\t\t\t", "yellow"), "OUT", colored(f"{signal_text}", "green"))
        return signal_text

    def get(self, tid):
        """
            Get alert tweet by ID and return trading signal.
        """
        tweet = self.db["tweets"].find_one({"tid": tid, "alert": True})
        signals = self.text_to_signal(tweet)
        self.__pretty_print_signal(tweet)
        return signals

    def getall(self):
        """
            Get all tweets and return trading signal.
        """
        print("Getting all tweets from DB...")
        results = self.tweets_collection.aggregate([
            {
                # Filter out alerts
                '$match': {
                    'alert': True
                }
            },
            {
                # Sort, oldest first
                '$sort': {
                    'created_at': 1
                }
            }
        ])
        for tweet in results:
            signal = self.get(tweet["tid"])

    def update(self, tid):
        """
            Update trading signal for tweet by ID.
        """
        query = {"tid": tid, "alert": True}
        signals = self.get(tid)
        newvalues = { "$set": { "signals": signals } }
        self.tweets_collection.update_one(query, newvalues)
        return signals

    def updateall(self):
        """
            Update trading signal for all tweets.
        """
        print("Updating all tweets...")
        results = self.tweets_collection.aggregate([
            {
                # Filter out alerts
                '$match': {
                    'alert': True
                }
            },
            {
                # Sort, oldest first
                '$sort': {
                    'created_at': 1
                }
            }
        ])
        for tweet in results:
            self.update(tweet["tid"])

    def parse(self, tid, update_db=True):
        """ Parse Tweet data and return trading signal. """
        query = {"tid": tid}
        tweet = self.db["tweets"].find_one(query)
        signals = self.text_to_signal(tweet)
        text = self.__normalize_text(tweet)
        print(colored(f"Input:\t\t{text}", "yellow"))
        print(colored(f"Signals:", "green"))
        for s in signals: print(colored(f"\t\t{s}", "green"))

        if update_db:
            newvalues = { "$set": { "signals": signals } }
            self.tweets_collection.update_one(query, newvalues)

        return signals

    def parseall(self):
        print("Parsing all tweets...")
        results = self.tweets_collection.aggregate([
            {
                # Filter out alerts
                '$match': {
                    'alert': True
                }
            },
            {
                # Sort, oldest first
                '$sort': {
                    'created_at': 1
                }
            }
        ])
        for tweet in results:
            tid = tweet["tid"]
            self.parse(tid)
        
    def text_to_signal(self, tweet):
        """
            Parse raw tweet text to an array of trading signal.

            Input:
                `ALERT: stopped $SPX (add-on) Re-entry long IN: 3609 - 10 pt stop`

            Output:
                `["SPX_TRADE_LONG_IN_3609_SL_10"]`
        """
        # Filter out non-alerts
        if not self.is_trading_signal:
            return []
        
        text = self.__normalize_text(tweet)

        def find_SL_POINTS(text):
            """
                Find stop loss in points.

                Input:
                    `LIMIT ORDER $SPX LONG |IN 3673 - 10 PT STOP`
                    `LIMIT BUY $SPX |IN 4000 - 15 POINT STOP`
                    `SHORT $SPX  | IN 4160 - 10PT STOP`
                Output:
                    `10`
                    `15`
                    `10`
            """
            POINTS = re.findall(r'(\d*)(?:PT|\sPT|\sPOINT)', text)[-1]
            return POINTS

        def find_SCALE_POINTS(text):
            """
                Find scale in points.

                Input:
                    `CLOSED FINAL SCALE $NDX LONG |IN 11060 OUT 13250 +2190`
                    `CLOSED 1 SCALE $SPX SHORT |  |IN 4193 OUT 4045 +148`
                    1621173564325117955 `CLOSED 3RD SCALE $NDX ADD-ON | IN 11818 OUT 12760 + 942`
                Output:
                    `2190`
                    `148`
            """
            POINTS = re.findall(r'(\+\d*)', text)[0]
            POINTS = POINTS.replace("+", "")
            return POINTS
        
        def find_trade(text):
            __ACTION_CODE = ""
            # Find trade direction
            direction = "LONG" if "LONG" in text else "SHORT"
            __ACTION_CODE += f"_TRADE_{direction}"

            # Find entry
            try:
                entries = re.findall(r'(?:IN\s)(\d*)', text)
                __ACTION_CODE += f"_IN_{entries[element]}"
            except Exception as e:
                # Sometimes parsing fail. We fall back to "UNKNOWN". We can later on decide, 
                # if we want to ignore this and put a market order in or skip the trade.
                __ACTION_CODE += f"_IN_UNKNOWN"
        
            # Find stop loss
            # We don't care to parse the SL from the text. Its always the same anyway
            # TODO: Above is not true. 1641890973302116358 is an example where we have different SL
            POINTS = find_SL_POINTS(text)

            __ACTION_CODE += f"_SL_{POINTS}"
            return __ACTION_CODE

        # Get all symbols in signal
        symbols = re.findall(r'(\$\w*)', text)
        symbols = self.__unique(symbols)

        ACTIONS = []
        element = 0
        for symbol in symbols:
            symbol = symbol[1:]  # $SPX --> SPX
            ACTION_CODE = f"{symbol}"

            # Move to flat
            if "TO FLAT" in text or "TO FLT" in text:
                """
                    Examples:
                        1610655996531048453 `STOP ADJ TO FLT $NDX .`
                        1638976429521006630 `$SPX stop adjusted to flat.`
                    Output:
                        `NDX_FLAT`
                        `SPX_FLAT`
                """
                ACTION_CODE += "_FLAT"
                ACTIONS.append(ACTION_CODE)

            # Stopped out
            elif "FLAT STOP" in text or "STOPPED" in text:
                # Currently, we don't care about flat stops.
                # If we want to add it, we need to add a new action code.
                ACTIONS.append(f"{symbol}_FLATSTOP")
                if "RE-ENTRY" in text:
                    trade = find_trade(text)
                    ACTIONS.append(f"{symbol}{trade}")

            # Limit order
            elif text.startswith("LIMIT"):
                """
                    Limit Orders are usually very rare, and at this point, we don't care about them.
                    We try to parse, but we don't use them for trading.

                    Examples:
                        `$SPX LIMIT BUY 3609 - 10 pt stop`
                        `LIMIT BUY $SPX |IN 4000 - 15 POINT STOP`
                        
                    Output:
                        `SPX_LIMIT_BUY_IN_3609_SL_10`
                        `SPX_LIMIT_BUY_IN_4000_SL_15`
                """
                # Ignore tweets
                if tweet["tid"] in ["1560000766043119617"]:
                    # TODO: 1560000766043119617  `LIMIT SELL $SPX |  | IN 4318 STOP AT 4380. |  | *SEE DASHBOARD FOR RATIONALE.`
                    continue

                ACTION_CODE += f"_LIMIT"
                
                # Set order direction
                if "BUY" in text or "LONG" in text:
                    ACTION_CODE += f"_LONG"
                elif "SELL" in text or "SHORT" in text:
                    ACTION_CODE += f"_SHORT"
                else:
                    raise Exception("Unknown action")

                # Set entry price
                IN = re.findall(r'(?:IN[\:|\s])(\d*)', text)[-1]

                # Set stop loss
                POINTS = find_SL_POINTS(text)
                OUT = int(IN) - int(POINTS)

                ACTION_CODE += f"_{IN}_OUT_{OUT}_SL_{POINTS}"
                ACTIONS.append(ACTION_CODE)

            # Closing position
            elif "CLOSED" in text:
                # There are two types of CLOSE events
                #   *  CLOSED by Stop Loss
                #   *  CLOSED by Profit taking (scale out)
                #   *  CLOSED by taking loss (example: 1634265187472531457)

                # profit taking
                if "SCALE" in text:
                    IN = re.findall(r'(?:IN[\:|\s])(\d*)', text)[-1]
                    OUT = re.findall(r'(?:OUT[\:|\s])(\d*)', text)[-1]
                    POINTS = find_SCALE_POINTS(text)
                    ACTION_CODE += f"_SCALEOUT_IN_{IN}_OUT_{OUT}_POINTS_{POINTS}"
                    ACTIONS.append(ACTION_CODE)
                else:
                    ACTION_CODE += f"_CLOSED"
                    ACTIONS.append(ACTION_CODE)

            # Trade
            elif text.startswith("SHORT") or text.startswith("LONG"):
                """
                    Examples:
                        1550479656805081088 - ALERT: Short $SPX\nIN 4000 - 10 pt stop
                """
                trade = find_trade(text)
                ACTIONS.append(f"{symbol}{trade}")

            # Ignore tweets
            elif tweet["tid"] in ["1565311603251232768", "1565311603251232768"]:
                # TODO: 1565311603251232768  `MOVED $RUT STOP TO -10 AGAIN. | I'M HAVE TO STEP AWAY FROM THE DESK FOR A BIT, BUT GENERALLY KEEP AN EYE ON THINGS VIA MOBILE.`
                continue

            # Unknown Action
            else:
                raise Exception("Unknown action")
                
            element += 1
            
        return ACTIONS

    def is_trading_signal(self, text):
        """
            Returns true if the text is a trading signal.
        """
        # if string beings with ALERT
        if text.upper().startswith("ALERT"):
            is_trading_signal = True
        else:
            is_trading_signal = False
        return is_trading_signal

    def backtest(self, username="NTLiveStream"):
        """
            FOR VALIDATION PURPOSES ONLY

            This method will take tweets from the DB and parse the trading signals.
            Each signal parsed (programatically) is compared against a manually created known-good list.
        """
        result = self.tweets_collection.aggregate([
            {
                '$match': {
                    'alert': True
                }
            },
            {
                # Sort, oldest first
                '$sort': {
                    'created_at': 1
                }
            },
            { '$limit' : 10 }
        ])

        # Get signals backtesting file
        filename = "signals-backtest.json"
        f = open(filename)
        manSignals = json.load(f)
        def __get_tweet_from_dict(tid, dict):
            for i in dict:
                if tid == i["tid"]:
                    return i
        print(f"Backtesting {len(manSignals)} tweets..")

        missing_backtests = []
        for tweet in result:
            # The following tweet ID is causing parsing errors. Its a one-off, so we just ignore it. No need to solve for the 1% error rates.
            # FLAT STOPPED $SPX | RE-ENTRY SHORT | IN 4211 - 10 PT STOP. | ADJUSTED $NDX STOP TO -25. |  | TAKING THE STOP RISK OVERNIGHT
            # FLAT STOPPED $NDX $SPX STOPPED $RUT  | RE-ENTRY LONG |IN 3752 |IN 11475 - 25 PT STOP |IN 1129 - 10 PT STOP
            if tweet["tid"] in [1557516667357380608, 1572963969991692292]:
                continue
            
            dynSignal = self.parse(tweet)
            text = self.__normalize_text(tweet)
            tid = tweet["tid"]
            manSignal = __get_tweet_from_dict(tweet["tid"], manSignals)["action"]
            
            if manSignal[0] == "TICKER_ACTION_DIRECTION_IN_PRICE_SL_POINTS":
                print(f"{tid} not in backtest file")
                missing_backtests.append(tid)
            else:
                # Compare Manual Backtest Signal against Dynamic Signal
                match = True if set(dynSignal) == set(manSignal) else False
                color_tid = colored(tweet["tid"], "blue")
                if match:
                    print(color_tid + colored(f" {dynSignal}", "green"))
                else:
                    print(color_tid + colored(f" MATCH ERROR", "red"))
                    print(colored(f"   ManSignal  {manSignal}", "green"))
                    print(colored(f"   DynSignal  {dynSignal}", "red"))
                    sys.exit()

        print(f"{len(missing_backtests)} missing backtests:")
        #print(missing_backtests)
        for i in missing_backtests[:5]:
            print(colored(i, "red"))

    def generate_signals_file(self, username="NTLiveStream"):
        # Load backtest.json
        filename = "signals-backtest.json"
        original = dict()
        f = open(filename)
        original = json.load(f)

        # get alert tweets from DB
        result = self.tweets_collection.aggregate([
            {
                '$match': {
                    'username': username,
                    'alert': True
                }
            },
            {
                # Sort, oldest first
                '$sort': {
                    'created_at': 1
                }
            },
            {
                '$project': {
                    'username': 0,
                    '_id': 0
                }
            },
            #{ '$limit' : 10 }
        ])
        dbdata = []
        for i in result:
            dbdata.append({
                "tid": i["tid"],
                "text": i["text"],
                "action": ["TICKER_ACTION_DIRECTION_IN_PRICE_SL_POINTS"],
            })
        
        # helper to check if tid already exists in json file
        def is_in_dict(search, dict):
            for i in dict:
                if search == i["tid"]:
                    return True
            return False

        # function to add to JSON
        def write_json(new_data, filename=filename):
            with open(filename,'r+') as file:
                # First we load existing data into a dict.
                file_data = json.load(file)
                # Join new_data with file_data inside emp_details
                file_data.append(new_data)
                # Sets file's current position at offset.
                file.seek(0)
                # convert back to json.
                json.dump(file_data, file, indent = 4)
        
        # append tweets to backtest.json if it doesn't exist already
        for i in dbdata:
            tid = i["tid"]
            if is_in_dict(tid, original):
                print(f"{tid} already in {filename}")
            else:
                print(f"{tid} adding to {filename}")
                out = {
                    "tid": i["tid"],
                    "text": i["text"],
                    "action": i["action"],
                }
                write_json(out)

    def manual(self):
        results = self.tweets_collection.aggregate([
            {
                # Filter out alerts
                '$match': {
                    'alert': True
                }
            },
            {
                # Sort, latest first
                '$sort': {
                    'created_at': -1
                }
            }
        ])
        for tweet in results:
            tid = tweet["tid"]
            if tid in ["1565311603251232768"]:
                continue
            signals = tweet["signals"]

            # compare two lists
            try:
                if set(tweet["signals"]) == set(tweet["signals_manual"]):
                    print(tid, "Backtest", colored(f"OK", "green"))
                    continue
            except KeyError:
                # signals_manual doesn't exist yet
                print(tid, "Backtest", colored(f"FAILED", "red"), self.__normalize_text(tweet), "-->", colored(signals, "yellow"))

                # add prompt asking to confirm signals (c) or manually enter signals (m)
                print("Confirm generated signals (c) or manually enter signals (m) or skip (s)?")                
                user_input = input()
                if user_input == "c":
                    print("Confirmed signals:" + colored(f" {signals}", "green"))
                    newvalues = { "$set": { "signals_manual": signals } }
                    self.tweets_collection.update_one({"tid": tid}, newvalues)
                elif user_input == "m":
                    print("Enter signal(s) using a comma separated list (e.g. SPX_TRADE_LONG_IN_3848_SL_25,NDX_TRADE_LONG_IN_11795_SL_25)")
                    manual_signal = input()
                    signals = None
                    try:
                        signals = manual_signal.split(",")
                    except:
                        signals = [manual_signal]
                    print("Inserting manual signals:" + colored(f" {signals}", "green"))
                    newvalues = { "$set": { "signals_manual": signals } }
                    self.tweets_collection.update_one({"tid": tid}, newvalues)
                elif user_input == "s":
                    print("Skipping..")
                    continue
                else:
                    print("Invalid input. Exiting..")
                    sys.exit()

