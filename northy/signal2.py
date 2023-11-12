import re
import sys
import json
import time
from termcolor import colored
from .db import Database
from datetime import datetime
from .prowl import Prowl
from .config import config
from .saxo import SaxoConfig
import logging

ignore_tweets = [
    "1557516667357380608", # FLAT STOPPED $SPX | RE-ENTRY SHORT | IN 4211 - 10 PT STOP. | ADJUSTED $NDX STOP TO -25. |  | TAKING THE STOP RISK OVERNIGHT
    "1565311603251232768", # Moved $RUT stop to -10 again.\nI'm have to step away from the desk for a bit, but generally keep an eye on things via mobile.
    "1611317586708561920", # FLAT STOPPED $NDX (ADD-ON) | RE-ENTRY LONG |IN 1070 - 25 PT STOP  <-- type in entry price
    "1633926383146618880", # stopped add-on $SPX &amp; flat stopped remainder original $SPX | Long $SPX | IN: 3908 - 10 pt stop
    "1641890973302116358", # ALERT: Limit buy $SPX | IN: 4000 - 15 point stop
    "1645367498823352320", # REMOVED $SPX 4000 LIMIT BUY ORDER. |  | #HOUSEKEEPING |  | NARRATOR: HA HA HTTPS://T.CO/ZR5COSFEX9
    "1639263064758312965", # ALERT: Flat stopped $SPX (add-on)\n\nRe-entry long\nIN 397 - 10 pt stop
    "1660904073049038848",
]

class Signal:
    """
        Trading signal class.

        See documentation for more info: [signal.md](docs/signal.md)
    """
    def __init__(self, production=None):
        # Create a logger instance for the class
        self.logger = logging.getLogger(__name__)
        
        self.prowl = Prowl(API_KEY=config["PROWL_API_KEY"])

        # MongoDB
        self.production = config["PRODUCTION"] if production is None else production
        self.db = Database(production=self.production)
        self.db_tweets = self.db.tweets

        # SaxoConfig
        self.saxo_config = SaxoConfig()
        self.signal_helper = SignalHelper()

    def __unique(self, sequence):
        """
            Removes duplicates from list() while keeping the original order.
        """
        seen = set()
        return [x for x in sequence if not (x in seen or seen.add(x))]

    def __pretty_print_signal(self, tweet):
        """
            Print signal in color.
        """
        text = self.signal_helper.normalize_text(tweet["text"])
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
        tweet = self.db_tweets.find_one({"tid": tid, "alert": True})
        if tweet is None:
            self.logger.error(f"Failed getting Tweet by ID '{tid}'.")
            return None
        
        signals = self.text_to_signal(tweet)
        self.__pretty_print_signal(tweet)
        return signals

    def getall(self) -> None:
        """
            Get all tweets and return trading signal.
        """
        self.logger.info("Getting all tweets from DB...")
        results = self.db_tweets.aggregate([
            { '$match': { 'alert': True } }, # Filter out alerts
            { '$sort': { 'created_at': 1 } } # Sort, oldest first
        ])
        for tweet in results:
            self.get(tweet["tid"])

    def update(self, tid):
        """
            Updates auto-generated trading signal by tweet ID.
        """
        query = {"tid": tid, "alert": True}
        signals = self.get(tid)
        newvalues = { "$set": { "signals": signals } }
        self.db_tweets.update_one(query, newvalues)
        return signals

    def updateall(self):
        """
            Update trading signal for all tweets.
        """
        print("Updating all tweets...")
        results = self.db_tweets.aggregate([
            { '$match': { 'alert': True } },  # Filter out alerts
            { '$sort': { 'created_at': 1 } }  # Sort, oldest first
        ])
        for tweet in results:
            self.update(tweet["tid"])

    def parse(self, tid:str, update_db=True) -> dict:
        """
            Parse Tweet ID and return trading signal.

            If `update_db` is `True`, the signal will be updated in the DB.

            Input:
                tid: 1550479656805081088
                update_db: True

            Output:
                {
                    "alert": true,
                    "signals": [
                        "SPX_TRADE_LONG_IN_3609_SL_10"
                    ]
                }

        """
        query = {"tid": tid}
        tweet = self.db.tweets.find_one(query)
        self.logger.info(f"Parsing tweet {tid}")
        if tweet is None:
            self.logger.error(f"Failed getting Tweet by ID '{tid}'.")
            return None
        
        data = {}

        # Check if tweet is an alert
        data["alert"] = True if self.is_trading_signal(tweet["text"]) else False
        
        # Parse trading signal
        if data["alert"]:
            # Parse trading signal
            signals = self.text_to_signal(tweet)
            data["signals"] = signals

        # Only for console output
        #text = self.signal_helper.normalize_text(tweet["text"])
        #print(colored(f"Input:\t\t{text}", "yellow"))
        #print(colored("Signals:", "green"))
        #[print(colored(f"\t\t{s}", "green")) for s in signals]  # Using list comprehension

        # Update DB if enabled
        if update_db:
            newvalues = { "$set": data }
            self.db_tweets.update_one(query, newvalues)

        return data

    def parseall(self):
        """
            Parse all tweets and update DB.
        """
        batch_size = 100
        curser = self.db_tweets.find({"alert": True}).sort("created_at", 1).batch_size(batch_size)
        for tweet in curser:
            tid = tweet["tid"]
            self.parse(tid)

    def text_to_signal(self, tweet:dict) -> list:
        """
            Parse raw tweet to an array of trading signal.

            Input:
                Tweet JSON object

            Output:
                `["SPX_TRADE_LONG_IN_3609_SL_10"]`
        """
        signal_helper = SignalHelper()

        #### INPUT VALIDATION ####
        if not isinstance(tweet, dict):
            self.logger.error("Tweet input is not dict")
            return []
        
        if "tid" not in tweet:
            self.logger.error("Tweet input is missing 'tid'")
            return []
        
        # Filter out non-alerts
        if not self.is_trading_signal(tweet["text"]):
            self.logger.debug("No trading signal found")
            return []
        
        # Filter out ignored tweets
        if tweet["tid"] in ignore_tweets:
            self.logger.debug(f"Skipping. Tweet '{tweet['tid']}' is on ignore list.")
            return []
        #############################

        text = self.signal_helper.normalize_text(tweet["text"])
        
        def find_trade(text, symbol):
            __ACTION_CODE = ""
            # Find trade direction
            direction = "LONG" if "LONG" in text else "SHORT"
            __ACTION_CODE += f"_TRADE_{direction}"

            # Find entry
            __IN = signal_helper.get_closest_symbols(signal_helper.find_INOUT(text, "IN"))[symbol]
            __ACTION_CODE += f"_IN_{__IN}"
        
            # Find stop loss
            # We don't care to parse the SL from the text. Its always the same anyway
            # TODO: Above is not true. 1641890973302116358 is an example where we have different SL
            # TODO: Parse the signal itself and get the SL from there
            POINTS = self.saxo_config.get_stoploss(symbol)
            self.logger.warning("Setting SL based on SaxoConfig and not the signal")

            __ACTION_CODE += f"_SL_{POINTS}"
            return __ACTION_CODE

        # Get all symbols in signal
        symbols = re.findall(r'(\$\w*)', text)
        symbols = self.__unique(symbols)

        ACTIONS = []
        element = 0
        # sort symbols alphabetically
        symbols.sort()
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
                    trade = find_trade(text, symbol)
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
                ACTION_CODE += f"_LIMIT"
                
                # Set order direction
                if "BUY" in text or "LONG" in text:
                    ACTION_CODE += f"_LONG"
                elif "SELL" in text or "SHORT" in text:
                    ACTION_CODE += f"_SHORT"
                else:
                    raise Exception("Unknown action")

                # Set entry price
                IN = signal_helper.get_closest_symbols(signal_helper.find_INOUT(text, "IN"))[symbol]

                # Set stop loss
                POINTS = self.saxo_config.get_stoploss(symbol)
                CALC_OUT = int(IN) - int(POINTS)

                ACTION_CODE += f"_IN_{IN}_OUT_{CALC_OUT}_SL_{POINTS}"
                ACTIONS.append(ACTION_CODE)

            # Closing position
            elif "CLOSED" in text:
                """
                    There are two types of CLOSE events: CLOSE and SCALEOUT.

                    1. CLOSE: Closing a position (usually because its not working out). Example:
                        `CLOSED $SPX SHORT -1`
                    
                    2. SCALEOUT: Closing a position because we reached our profit target. Example:
                        `CLOSED FINAL $SPX SHORT (GOD HELP ME) |  | IN 4193 OUT 3955 +238`
                        `CLOSED FINAL SCALE $SPX ADD-ON | IN 3722 OUT 3983 +261`
                """

                # SCALEOUT
                if "OUT" in text:
                    IN = signal_helper.get_closest_symbols(signal_helper.find_INOUT(text, "IN"))[symbol]
                    OUT = signal_helper.get_closest_symbols(signal_helper.find_INOUT(text, "OUT"))[symbol]
                    POINTS = str(signal_helper.find_SCALE_POINTS(text))
                    ACTION_CODE += f"_SCALEOUT_IN_{IN}_OUT_{OUT}_POINTS_{POINTS}"
                    ACTIONS.append(ACTION_CODE)
                else:
                    ACTION_CODE += f"_CLOSED"
                    ACTIONS.append(ACTION_CODE)

            # Trade
            elif text.startswith("SHORT") or text.startswith("LONG"):
                """
                    Examples:
                        1550479656805081088 - `ALERT: Short $SPX\nIN 4000 - 10 pt stop`
                        1557347316465651712 - `FLAT STOPPED $NDX  | RE-ENTRY SHORT $NDX SHORT $SPX | IN 13340 - 25 PT STOP | IN 4198 - 10 PT STOP`
                """
                trade = find_trade(text, symbol)
                ACTIONS.append(f"{symbol}{trade}")

            # Unknown Action
            else:
                tid = tweet["tid"]
                msg = f"Unknown action when parsing tweet {tid}"
                self.logger.error(msg)
                if self.production:
                    # TODO: Move prowl notifications to logger logic
                    self.prowl.send(message=msg, priority=1)
                
            element += 1
            
        return ACTIONS

    def is_trading_signal(self, text:str) -> bool:
        """
            Returns true if the text is a trading signal.
        """
        # if string beings with ALERT
        is_trading_signal = True if text.upper().startswith("ALERT") else False
        return is_trading_signal

    def export(self, filename="signals", format="json"):
        """
            Export all signals to JSON file.
        """
        # create filepath to temp/ folder
        filename = f"temp/{filename}.{format}"

        self.logger.info(f"Exporting signals to {filename}")
        
        # Get all signals
        result = self.db_tweets.aggregate([
            { '$match': { 'alert': True } },
            { '$sort': { 'created_at': 1 } },
            {
                "$project": {
                    "_id": 0,
                    "tid": 1,
                    "created_at": 1,
                    "text": 1,
                    "signals": 1,
                    "signals_manual": 1
                }
            },
            #{ '$limit' : 10 }
        ])
        
        def serialize_datetime(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()

        if format == "json":
            # Export to JSON
            with open(filename, 'w') as outfile:
                json.dump(list(result), outfile, indent=4, default=serialize_datetime)
        elif format == "csv":
            # Export to CSV

            with open(filename, 'w') as outfile:
                header = "tid;created_at;text;signals;signals_manual\n"
                outfile.write(header)

                for t in result:
                    #print(t)
                    tid = t["tid"]
                    dt = t["created_at"]
                    text = self.signal_helper.normalize_text(t["text"])
                    try:
                        sig = ','.join(t["signals"])
                    except KeyError:
                        sig = ""
                    except Exception as e:
                        self.logger.error("Unknown error", e)

                    try:
                        sig_man = ','.join(t["signals_manual"])
                    except KeyError:
                        sig_man = ""
                    except Exception as e:
                        self.logger.error("Unknown error", e)


                    line = f"{tid};{dt};{text};{sig};{sig_man}\n"
                    outfile.writelines(line)

    def backtest(self, manual_review=True):
        """
            FOR VALIDATION PURPOSES ONLY

            This method will take tweets from the DB and parse the trading signals.
            Each signal parsed (programatically) is compared against a manually created known-good list.
        """
        result = self.db_tweets.aggregate([
            { "$match": { "alert": True } },
            { "$sort": { "created_at": 1 } }
        ])

        count_success = list()
        count_failed = list()
        for tweet in result:
            tid = tweet["tid"]
            text = self.signal_helper.normalize_text(tweet["text"])
            try:
                signals = tweet["signals"]
            except KeyError:
                self.logger.error(f"{tid} missing signals. Try running signal --updateall")
                continue

            if tid in ignore_tweets:
                print(tid, "Backtest", colored(f"IGNORED", "yellow"), 
                      self.signal_helper.normalize_text(tweet["text"]))
                continue

            try:
                signals_manual = tweet["signals_manual"]
            except KeyError:
                self.logger.info(colored(f"{tid} missing signals_manual", "red"))
                continue

            # compare two lists
            signals_match = self.compare_lists(tweet["signals"], tweet["signals_manual"])
            if signals_match:
                #print(colored(f"{tid} OK", "green"))
                count_success.append(tid)
            else:
                diff = list(set(sorted(signals)) - set(sorted(signals_manual)))
                print(colored(f"{tid} FAILED", "red"), text, "difference:", 
                      colored(diff, "yellow"))
                count_failed.append(tid)
                #print("Signal\t\t", signals)
                #print("Expected\t", signals_manual)
        
        print(colored(f"Success: {len(count_success)}", "green"))
        print(colored(f"Ignored: {len(ignore_tweets)}", "yellow"))
        print(colored(f"Failed: {len(count_failed)}", "red"))
        if manual_review:
            for i in count_failed:
                self.manual(i)

    def compare_lists(self, list1, list2):
        if len(list1) != len(list2):
            return False
        sorted_list1 = sorted(list1)
        sorted_list2 = sorted(list2)
        for i in range(len(sorted_list1)):
            if sorted_list1[i] != sorted_list2[i]:
                return False
        return True

    def manual(self, tid) -> None:
        """
            Prompt for manually reviewing signals and confirm them.
        """
        # Get tweet by ID
        tweet = self.db.tweets.find_one({"tid": tid})

        # Check if tweet exists
        if tweet is None:
            self.logger.error(f"Failed getting Tweet by ID '{tid}'.")
            return None

        # Check if tweet is on ignore list
        if tid in ignore_tweets:
            ignored = colored(f"IGNORED", "yellow")
            text = self.signal_helper.normalize_text(tweet["text"])
            msg = f"{tid} Backtest {ignored} {text}"
            self.logger.warning(msg)
            return None

        # Check if signals and signals_manual exist
        if "signals" not in tweet and "signals_manual" not in tweet:
            msg = f"{tid} Backtest {colored(f'FAILED', 'red')} signals or " \
                  f"signals_manual doesn't exist"
            self.logger.warning(msg)
            return None

        # Check if signals and signals_manual are the same
        signals_match = self.compare_lists(tweet["signals"], 
                                           tweet["signals_manual"])

        # If signals mismatch, prompt user to confirm or manually enter signals
        if not signals_match:
            # signals_manual doesn't exist yet
            # generate signals from text and suggest to use it
            generated_signal = self.text_to_signal(tweet)
            self.logger.info(tid, "Backtest", colored(f"FAILED", "red"),
                  self.signal_helper.normalize_text(tweet["text"]),
                  colored("new suggested value:", "green"),
                  colored(generated_signal, "yellow"))

            # add prompt asking to confirm signals (c) or manually enter signals (m)
            print("Confirm generated signals (c) or manually enter signals (m) or skip (s)?")                
            user_input = input()
            if user_input == "c":
                print("Confirmed signals:" + colored(f" {generated_signal}", "green"))
                newvalues = { "$set": { "signals_manual": generated_signal } }
                self.db_tweets.update_one({"tid": tid}, newvalues)
            elif user_input == "m":
                print("Enter signal(s) using a comma separated list (e.g. SPX_TRADE_LONG_IN_3848_SL_25,NDX_TRADE_LONG_IN_11795_SL_25)")
                manual_signal = input()
                signals = None

                try:
                    signals = manual_signal.split(",")
                except Exception as e:
                    self.logger.debug("Failed splitting manual_signal:", manual_signal)
                    signals = [manual_signal]
                    self.logger.debug("Setting signal to:", signals)

                print("Inserting manual signals:" + colored(f" {signals}", "green"))
                newvalues = { "$set": { "signals_manual": signals } }
                self.db_tweets.update_one({"tid": tid}, newvalues)
            elif user_input == "s":
                print("Skipping..")
                return
            else:
                self.logger.debug("Invalid input. Exiting..")
                sys.exit()

    def manualall(self):
        results = self.db_tweets.aggregate([
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
            self.manual(tweet["tid"])
        
    def watch_log(self, doc, data, prowl_notification=True) -> None:
        """
            Log watch results to console.

            Input:
                doc: MongoDB document
                data: Trading signal data

            Output:
                1550479656805081088 	 IN  ALERT: SHORT $SPX | IN 4000 - 10 PT STOP
        """
        tid = doc["tid"]
        text = doc["text"].strip()
        if data["alert"]:
            self.logger.info(f"Found trading signal in {tid} - {text}")
            url = f"https://twitter.com/NTLiveStream/statuses/{tid}"  # NOTE: Hardcoded Twitter handle

            # When running refresh_backlog(), we don't want to send alerts
            if prowl_notification:
                self.prowl.send(text, url)
        else:
            self.logger.debug(f"No trading signal found in {tid} - {text}")

    def refresh_backlog(self, limit=1000):
        """
            Parse old tweets and make sure alert flag is setRefresh 
            backlog to make sure we're up-to-date before starting change stream.

            TODO: This could be optimized by storing Tweet ID in DB and only refresh since $tid
            TODO: If above is implemented, .limit(1000) below can be removed
        """
        self.logger.info("Refreshing backlog...")
        query = {"alert": {"$exists": False}}
        
        # Performance optimization, only return data needed
        projection = {"tid": 1, "text": 1}

        # Performance optimization, sort by tid and limit to 1000
        cursor = self.db.tweets.find(query, projection).sort("tid", -1).limit(limit)
        documents = [doc for doc in cursor]

        # Preload the signal helper function for better performance
        parse = self.parse
        watch_log = self.watch_log

        for doc in documents:
            data = parse(tid=doc["tid"], update_db=True)
            watch_log(doc, data, prowl_notification=False)

    def watch_stream(self):
        # Watch for new documents (tweets) where "alert" is not set
        pipeline = [
            { "$match": { "operationType": { "$in": ["insert"] } } }, # 'insert', 'update', 'replace', 'delete'
            { "$match": { "alert": { "$exists": False } } }, # Get tweets where "alerts" it not set (yet)
        ]
        # Create a change stream
        change_stream = self.db_tweets.watch(pipeline)

        # Iterate over the change stream
        for change in change_stream:
            doc = change["fullDocument"]
            data = self.parse(doc["tid"], update_db=True)
            self.watch_log(doc, data)

    def watch(self):
        """
            Watch for new tweets and parse them.

            If a trading signal is found, we add it to the DB.
        """
        self.refresh_backlog()
        while True:
            try:
                self.logger.info("Starting change stream...")
                self.watch_stream()
            except Exception as e:
                self.logger.critical(f"An error occurred: {e}")
                # Pause for 60 seconds before resuming
                time.sleep(60)

class SignalHelper:
    def __init__(self) -> None:
        self.ticker_config = SaxoConfig().config["tickers"]
        pass

    def normalize_text(self, tweet_text:str) -> str:
        """
            Takes twitter text and cleans it up and normalize the format.

            Input:
                ALERT: Closed 2nd scale $NDX add-on\n\nIN 11818 OUT 12360 +542
            
            Output:
                Closed 2nd scale $NDX add-on | IN 11818 OUT 12360 +542
        """
        # print(repr(tweet_text))

        # Clean up string
        text = tweet_text
        text = text.replace("\n", " | ")
        text = text.replace("ALERT: ", "")
        text = re.sub(r'\s+', ' ', text)
        text = text.upper()

        # Fix bug with `| LONG $SPX $NDX | IN 3580 - 10 PT STOP |IN 10900 - 25 PT STOP`   1576847187740266496
        if text.startswith("| "):
            text = text[2:]

        # Fix bug with ("FLAT STOPPED $RUT | RE-ENTRY LONG | IN: 1795 - 10 PT STOP") where "IN:" contains a colon, all other tweets doesn't
        text = text.replace(" IN: ", "IN ")

        # Prettify
        text = text.replace("|IN", "| IN")

        return text

    def find_INOUT(self, text, inout="IN"):
        """
            Find entry/exit price in text.

            Input:
                `CLOSED FINAL SCALE $NDX LONG |IN 11060 OUT 13250 +2190`
                `CLOSED 1 SCALE $SPX SHORT |  |IN 4193 OUT 4045 +148`
                `CLOSED 3RD SCALE $NDX ADD-ON | IN 11818 OUT 12760 + 942`
                `LONG $NDX $SPX  $RUT |  |IN 3713 - 10 PT STOP |IN 11348 - 25 PT STOP |IN 1703 - 10 PT STOP`
                `Closed 1 scale $SPX add-on\n\nIN 3722 OUT OUT 3824 +102`
                `CLOSED 2ND SCALE $NDX | IN 13720 OUT: 12484 +1236 NDX`

            Output:
                [11060, 13250]
                [4193, 4045]
                [11818, 12760]
        """
        # get all IN numbers from text
        text = self.normalize_text(text)
        text = text.replace(":", " ") # replace : with space
        text = text.replace("  ", " ") #remove double spaces

        out = re.findall(f'({inout}[\s|:])(\d+)', text) # --> IN:1234
        out = [int(i[1]) for i in out] # --> [1234]
        return out

    def find_SCALE_POINTS(self, text) -> int:
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
        # Make sure text is normalized
        text = self.normalize_text(text)

        # Find points
        POINTS = re.findall(r'\+\s?(\d+)', text)[0]
        POINTS = POINTS.replace("+", "")
        POINTS = POINTS.replace("", "")

        return int(POINTS)

    def get_closest_symbols(self, numbers:list) -> dict:
        """
            Given a list of numbers, return a dictionary of the closest symbols to the average price.
            If there is a tie, return the symbols in alphabetical order.

            This function is needed to handle this:
                1. find_INOUT() analyze e.g.: `flat stopped $NDX stopped $RUT Re-entry long IN: 14885 - 25 pt stop IN 1880 - 10pt stop` and return: `[14885,1880]`
                2. get_closest_symbols() will guess the symbol based on the numbers and returned by find_INOUT()
                3. get_closest_symbols() will return a dictionary of the closest symbols to the average price.

            Example:
                numbers = [3713, 11348, 1703]
                get_closest_symbols(numbers) -> {"NDX": 11348, "SPX": 3713, "RUT": 1703}

                numbers = [3713]
                get_closest_symbols(numbers) -> {"SPX": 3713}
        """
        
        # 200ma for each symbol
        ndx = self.ticker_config["NDX"]["200ma"]
        spx = self.ticker_config["SPX"]["200ma"]
        rut = self.ticker_config["RUT"]["200ma"]
        djia = self.ticker_config["DJIA"]["200ma"]

        avg_price = (ndx + spx + rut) / 3
        symbols = [key for key in self.ticker_config]

        # Handle a list of multiple numbers
        if len(numbers) > 1:
            closest_numbers = {symbol: 0 for symbol in symbols}  # initialize with default value
            for num in numbers:
                if abs(num - djia) <= abs(num - ndx) and abs(num - djia) <= abs(num - rut):
                    closest_numbers["DJIA"] = num
                elif abs(num - ndx) <= abs(num - spx) and abs(num - ndx) <= abs(num - rut):
                    closest_numbers["NDX"] = num
                elif abs(num - spx) <= abs(num - ndx) and abs(num - spx) <= abs(num - rut):
                    closest_numbers["SPX"] = num
                else:
                    closest_numbers["RUT"] = num
            
            sorted_symbols = sorted(symbols, key=lambda x: abs(closest_numbers[x] - avg_price))
            return {symbol: closest_numbers[symbol] for symbol in sorted_symbols}
        
        # Handle a single number
        else:
            num = numbers[0]
            if abs(num - djia) <= abs(num - ndx) and abs(num - djia) <= abs(num - rut):
                return {"DJIA": num}
            elif abs(num - ndx) <= abs(num - spx) and abs(num - ndx) <= abs(num - rut):
                return {"NDX": num}
            elif abs(num - spx) <= abs(num - ndx) and abs(num - spx) <= abs(num - rut):
                return {"SPX": num}
            else:
                return {"RUT": num}
