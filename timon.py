import re
import sys
import time
import json
import click
import tweepy
import pyprowl
from tweepy import OAuthHandler, StreamingClient
from datetime import datetime
from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.errors import DuplicateKeyError
from dotenv import dotenv_values
from colorama import init, Fore, Back, Style
from termcolor import colored

config = dotenv_values(".env")
database_name = "northy"
tweets_collection_name = "tweets"

# SIGNAL CODE
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

class Timon:
    def __init__(self):
        # APIv1 - Authenticate as a user
        auth = tweepy.OAuthHandler(config["consumer_key"],config["consumer_secret"])
        auth.set_access_token(config["access_key"],config["access_secret"])

        self.api = tweepy.API(auth, wait_on_rate_limit=True)
        
        # MongoDB
        client = MongoClient(config["mongodb_conn"])
        self.db = client[database_name]
        self.tweets_collection = self.db[tweets_collection_name]

        # Prepare DB
        self.db[tweets_collection_name].create_index('tid', unique=True)

    def __print_nice(self, tweet):
        """ 
            Takes Tweets from DB and prints them nicely
        """
        now = colored(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "yellow")
        tid = colored(tweet["tid"], "green")
        username = colored(tweet["username"], "cyan")
        created_at = colored(tweet["created_at"], "red")
        text = tweet["text"].replace('\n', '')
        print(now, tid, created_at, username, text)

    def __add_tweet_to_db(self, data):
        """
            DB Schema
            {
                tid,
                username,
                created_at,
                text
            }
        """
        try:
            self.tweets_collection.insert_one(data)
            tid =  data["tid"]
            #print(f"Addeing {tid}")
        except DuplicateKeyError:
            #print("Duplicated Key")
            pass

    def readdb(self, username=None, limit=10):
        pipeline = []

        # Get latest tweets
        pipeline.append({"$sort": { "created_at": -1 }})  
        
        # Filter by username
        if username != None:
            pipeline.append({"$match": { "username": username }})
        
        # Limit output
        pipeline.append({"$limit": limit})
        
        # Reverse output order so oldest -> latest
        pipeline.append({"$sort": { "created_at": 1 }})

        for i in self.tweets_collection.aggregate(pipeline):
            self.__print_nice(i)

    def fetch_latest(self, username="NTLiveStream", limit=200):
        """
            Fetching the lastest 200 tweets from user and adds them into the DB.
            This is mainly used when DB is out of sync.
        """

        response = self.api.user_timeline(screen_name=username, count=limit)
        for tweet in response:
            data = {
                "tid": str(tweet.id),
                "username": tweet.user.screen_name,
                "created_at": tweet.created_at,
                "text": tweet.text
            }
            self.__print_nice(data)
            self.__add_tweet_to_db(data)

    def watch(self, username="NTLiveStream"):
        #print(f"+ Updating database. Fetching the latest 200 tweets..")
        #self.fetch_latest(username=username)
        #print(f"+ Dabase is up-to-date")

        # Get latest tweet ID
        latest = [i for i in self.tweets_collection.find({}).sort("created_at", -1).limit(1)]
        latest_id = latest[0]["tid"]

        # fetch tweets
        response = self.api.user_timeline(screen_name=username, count=1)
        for tweet in response:
            data = {
                "tid": str(tweet.id),
                "username": tweet.user.screen_name,
                "created_at": tweet.created_at,
                "text": tweet.text
            }
            self.__print_nice(data)
            self.__add_tweet_to_db(data)

    def prowl(self, message):
        p = pyprowl.Prowl(config["prowl_api_key"])

        try:
            p.verify_key()
            #print("Prowl API key successfully verified!")
        except Exception as e:
            #print("Error verifying Prowl API key: {}".format(e))
            exit()

        try:
            p.notify(event="Alert", description=message, priority=0, url='http://www.example.com', appName='Northy')
            print("Notification successfully sent to Prowl!")
        except Exception as e:
            print("Error sending notification to Prowl: {}".format(e))

    def pushalert(self):
        """
            This will watch for new ALERT Tweets and notify through Prowl
        """
        latest_id = None
        while True:
            # Get latest tweet ID
            tweet = [i for i in self.tweets_collection.find({}).sort("created_at", -1).limit(1)][0]
            self.__print_nice(tweet)

            # New Tweet detected
            if latest_id != tweet["tid"]:
                # Update last seen Tweet ID
                latest_id = tweet["tid"]

                # Send push notification if Alert
                if "ALERT" in tweet["text"]:
                    self.prowl(tweet["text"])
            time.sleep(1)

    def datafeed(self):
        from tvDatafeed import TvDatafeed, Interval
        #tv = TvDatafeed(config["TW_USER"], config["TW_PASS"])
        tv = TvDatafeed()

        tickers = [
            {"symbol": "NDX", "exchange": "NASDAQ"},
            {"symbol": "SPX", "exchange": "SP"},
            {"symbol": "US100", "exchange": "CAPITALCOM"},
            {"symbol": "US500", "exchange": "CAPITALCOM"},
            {"symbol": "RUT", "exchange": "TVC"},
        ]
        for ticker in tickers:
            _symbol = ticker["symbol"]
            _exchange = ticker["exchange"]
            collection = f"twfeed-{_exchange}-{_symbol}"
            self.db[collection].create_index('dt', unique=True)

            minutes_in_day = 1440
            minutes_in_day = 100
            df = tv.get_hist(symbol=_symbol, exchange=_exchange, interval=Interval.in_1_minute, n_bars=minutes_in_day*2, extended_session=True)
            for date, row in df.T.items():
                d = { "dt": date, "h": row["high"], "l": row["low"], "o": row["open"], "c": row["close"] }
                try:
                    self.db[collection].insert_one(d)
                    print(f"+ Inserting {_exchange}:{_symbol} {d}")
                except DuplicateKeyError:
                    print(f"+ Already exist {_exchange}:{_symbol} {d}")
                    pass


class Signal:
    def __init__(self):
        # MongoDB
        client = MongoClient(config["mongodb_conn"])
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
        """
        # Clean up string
        text = text["text"].replace("\n", " | ")
        text = text.replace("ALERT: ", "")
        text = text.upper() # normalize
        # Fix bug with ("FLAT STOPPED $RUT | RE-ENTRY LONG | IN: 1795 - 10 PT STOP") where "IN:" contains a colon, all other tweets doesn't
        text = text.replace(" IN: ", "IN ")
        return text

    def lookup(self, tid):
        res = [i for i in self.tweets_collection.find({"tid": tid}).limit(1)]
        tweet = res[0]
        signal = self.parse(tweet)
        text = self.__normalize_text(tweet)
        print(colored(f"Input:\n        {text}\n", "yellow"))
        print(colored(f"Signals:", "green"))
        for i in signal:
            print(colored(f"        {i}", "green"))
        return signal

    def parse(self, tweet):
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
                    'text': { '$regex': re.compile(r"alert:", re.IGNORECASE) }
                }
            },
            {
                # Sort, oldest first
                '$sort': {
                    'created_at': 1
                }
            },
            #{ '$limit' : 25 }
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
                #print(f"{tid} not in backtest file")
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
                    'text': {
                        '$regex': re.compile(r"alert:", re.IGNORECASE)
                    }
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
        

if __name__ == '__main__':
    @click.group()
    def cli():
        pass

    @click.command()
    @click.option('--limit', default=10, help='Number of tweets to return')
    @click.option('--username', default=None, help='Filter by username')
    def readdb(username, limit):
        """ Read Tweets from DB """
        t = Timon()
        t.readdb(username=username, limit=limit)
    
    @click.command()
    @click.option('--limit', default=10, help='Number of tweets to return')
    @click.option('--username', default="NTLiveStream", help='Filter by username')
    def fetch(username, limit):
        """ Fetch Tweets from user and store them in DB """
        t = Timon()
        t.fetch_latest(username=username, limit=limit)

    @click.command()
    @click.option('--username', default="NTLiveStream", help='Filter by username')
    def watch(username):
        """ Watch for new Tweets by user """
        t = Timon()
        while True:
            try:
                t.watch(username=username)
                time.sleep(5)
            except Exception as e:
                print(f"Exception {e}")
                print(f"Going to sleep for 1 min.")
                time.sleep(60)

    @click.command()
    def pushalert():
        """ Send push notifications when new Tweets are added to DB  """
        t = Timon()
        t.pushalert()

    @click.command()
    @click.option('--generate', default=False, flag_value='generate', help='Update backtest.json file with latest signals (without overriding manual checks)')
    @click.option('--backtest', default=True, flag_value='backtest', help='Compare dynamicly parsed Tweets from DB against manually validated Tweets from backtest file')
    @click.option('--lookup', type=int, help='Parse Tweet text and return signal')
    def signal(generate, lookup, backtest):
        """ Update backtesting file """
        s = Signal()

        if generate:
            print(f"Updating backtest.json")
            s.generate_signals_file()

        if lookup:
            s.lookup(lookup)

        if backtest:
            s.backtest()

    @click.command()
    def datafeed():
        """ Fetch data from TradingView """
        t = Timon()
        while True:
            try:
                t.datafeed()
                print(f"Going to sleep for 12 hour")
                time.sleep(60*60*12)  # 12 hours
            except Exception as e:
                print(f"Exception {e}")
                print(f"Going to sleep for 1 hour")
                time.sleep(60*60)


    cli.add_command(readdb)
    cli.add_command(fetch)
    cli.add_command(watch)
    cli.add_command(pushalert)
    cli.add_command(signal)
    cli.add_command(datafeed)
    cli()
