from termcolor import colored
import re
from pymongo import MongoClient
from termcolor import colored
import sys
import json
from dotenv import dotenv_values
from tweepy import OAuthHandler, StreamingClient
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from termcolor import colored
from dotenv import dotenv_values

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
                FLATADJ     - adjust stop loss to break even
                FLATSTOP    - stop loss was triggered, this is just an observation, no action needed
                CLOSE       - close open position by buying/selling depending on the trade direction
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
        client = MongoClient(self.config["mongodb_conn"])
        self.db = client[database_name]
        self.tweets_collection = self.db[tweets_collection_name]

    def __unique(self, sequence):
        """
            Removes duplicates from list() while keeping the original order.
        """
        seen = set()
        return [x for x in sequence if not (x in seen or seen.add(x))]

    def __normalize_text(self, text):
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
        text = text["text"].replace("\n", " | ")
        text = text.replace("ALERT: ", "")
        text = text.upper() # normalize
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

        print(colored(f"Input:\t\t{text}", "yellow"))
        print(colored(f"Signals:\t{signal_text}", "green"))

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
        self.delete_action()
        query = {"tid": tid, "alert": True}
        signals = self.get(tid)
        newvalues = { "$set": { "signals": signals } }
        self.tweets_collection.update_one(query, newvalues)

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
            print("Updating tweet:", tweet["tid"])
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
            newvalues = { "$set": { "signal": signals } }
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

        # Get all symbols in signal
        symbols = re.findall(r'(\$\w*)', text)
        symbols = self.__unique(symbols)

        ACTIONS = []
        element = 0
        for symbol in symbols:
            symbol = symbol[1:]  # $SPX --> SPX
            ACTION_CODE = f"{symbol}"

            # Move to flat
            if "TO FLAT" in text:
                ACTION_CODE += "_FLAT"

            # Closing trades
            if "CLOSED" in text:
                # There are two types of CLOSE events
                #   *  CLOSED by Stop Loss
                #   *  CLOSED by Profit taking (scale out)

                # profit taking
                if "SCALE" in text:
                    IN = re.findall(r'(?:IN[\:|\s])(\d*)', text)[-1]
                    OUT = re.findall(r'(?:OUT[\:|\s])(\d*)', text)[-1]
                    POINTS = re.findall(r'(?:\+[\s]?)(\d*)', text)[-1]
                    ACTION_CODE += f"_CLOSE_SCALE_IN_{IN}_OUT_{OUT}_POINTS_{POINTS}"
                else:
                    ACTION_CODE += f"_CLOSE_STOPLOSS"

            # Re-entry
            if "RE-ENTRY" in text:
                # Find trade direction
                direction = "LONG" if "LONG" in text else "SHORT"
                ACTION_CODE += f"_TRADE_{direction}"

                # Find entry
                try:
                    entries = re.findall(r'(?:IN\s)(\d*)', text)
                    ACTION_CODE += f"_IN_{entries[element]}"
                except Exception as e:
                    # Sometimes parsing fail. We fall back to "UNKNOWN". We can later on decide, 
                    # if we want to ignore this and put a market order in or skip the trade.
                    ACTION_CODE += f"_IN_UNKNOWN"
            
                # Find stop loss
                # We don't care to parse the SL from the text. Its always the same anyway
                stoploss_settings = {
                    "SPX": 10,
                    "RUT": 10,
                    "NDX": 25,
                }
                ACTION_CODE += f"_SL_{stoploss_settings[symbol]}"

            element += 1

            ACTIONS.append(ACTION_CODE)

        # debugging
        """
        for a in ACTIONS:
            if "FLAT" in a:
                print(text)
                print(ACTIONS)
                print()
            if "CLOSE" in a:
                print(text)
                print(ACTIONS)
                print()
            if "TRADE" in a:
                print(text)
                print(ACTIONS)
                print()
        """
            
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
            
            #print(tweet)
            dynSignal = self.parse(tweet)
            text = self.__normalize_text(tweet)
            tid = tweet["tid"]
            #print(manSignals)
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
        
    def delete_action(self):
        # Delete action field from DB
        self.tweets_collection.update_many(
            {
                'alert': True
            },
            {
                '$unset': {
                    'action': ""
                }
            }
        )
