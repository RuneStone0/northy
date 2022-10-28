import re
import sys
import time
import click
import json
import tweepy
from tweepy import OAuthHandler, StreamingClient
from datetime import datetime
from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.errors import DuplicateKeyError
from dotenv import dotenv_values
from colorama import init, Fore, Back, Style
from termcolor import colored

config = dotenv_values(".env")

# MongoDB
client = MongoClient(config["mongodb_conn"])
db = client["northy"]

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
        self.db = client["northy"]

    def __print_nice(self, tweet):
        """ 
            Takes Tweets from DB and prints them nicely
        """
        tid = colored(tweet["tid"], "green")
        username = colored(tweet["username"], "cyan")
        created_at = colored(tweet["created_at"], "red")
        text = tweet["text"].replace('\n', '')
        print(tid, created_at, username, text)

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
            self.db["data"].insert_one(data)
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

        for i in self.db["data"].aggregate(pipeline):
            self.__print_nice(i)

    def fetch_latest(self, username="NTLiveStream", limit=200):
        """
            Fetching the lastest 200 tweets from user and adds them into the DB.
            This is mainly used when DB is out of sync.
        """

        response = self.api.user_timeline(screen_name=username, count=limit)
        for tweet in response:
            data = {
                "tid": tweet.id,
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
        latest = [i for i in self.db["data"].find({}).sort("created_at", -1).limit(1)]
        latest_id = latest[0]["tid"]

        # fetch tweets
        response = self.api.user_timeline(screen_name=username, count=1)
        for tweet in response:
            data = {
                "tid": tweet.id,
                "username": tweet.user.screen_name,
                "created_at": tweet.created_at,
                "text": tweet.text
            }
            self.__print_nice(data)
            self.__add_tweet_to_db(data)

class ParseAlert:
    def __init__(self, db):
        ## MongoDB
        #client = MongoClient(config["mongodb_conn"])
        #self.db = client["northy"]
        self.db = db
        pass

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

    def text_to_signal(self, text):
        """
            This method will convert Northy Alert Tweets from its raw form (text) into a tradable signal.
        """
        text = self.__normalize_text(text)

        # Get all symbols in signal
        symbols = re.findall(r'(\$\w*)', text)
        symbols = self.__unique(symbols)

        ACTIONS = []
        element = 0
        for symbol in symbols:
            symbol = symbol[1:]  # $SPX --> SPX
            ACTION_CODE = f"{symbol}"

            # Adjust position to flat (break even)
            if "TO FLAT" in text:
                ACTION_CODE += "_FLATADJ"

            # Position was stopped out @ break even
            if "FLAT STOP" in text:
                ACTION_CODE += "_FLATSTOP"

            # Closing trade
            if "CLOSED" in text:
                # There are two types of CLOSE events
                #   *  CLOSED by Stop Loss
                #   *  CLOSED by Profit taking (scale out)

                # profit taking
                if "SCALE" in text:
                    ACTION_CODE += "_CLOSE_PROFIT"
                else:
                    ACTION_CODE += "_CLOSE_STOPLOSS"

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

        return ACTIONS

    def parse_backtest(self, username="NTLiveStream"):
        """
            FOR VALIDATION PURPOSES ONLY

            This method will take tweets from the DB and parse the trading signals.
            Each signal parsed (programatically) is compared against a manually created known-good list.
        """
        result = self.db["data"].aggregate([
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
            #{ '$limit' : 5 }
        ])

        for tweet in result:
            # The following tweet ID is causing parsing errors. Its a one-off, so we just ignore it. No need to solve for the 1% error rates.
            # FLAT STOPPED $SPX | RE-ENTRY SHORT | IN 4211 - 10 PT STOP. | ADJUSTED $NDX STOP TO -25. |  | TAKING THE STOP RISK OVERNIGHT
            # FLAT STOPPED $NDX $SPX STOPPED $RUT  | RE-ENTRY LONG |IN 3752 |IN 11475 - 25 PT STOP |IN 1129 - 10 PT STOP
            if tweet["tid"] in [1557516667357380608, 1572963969991692292]:
                continue
            signal = colored(self.text_to_signal(tweet), "red")
            text = self.__normalize_text(tweet)
            tid = colored(tweet["tid"], "green")
            if "FLAT" in text:
                print(tid, signal, text)

    def update_backtest_file(self, username="NTLiveStream"):
        # Load backtest.json
        filename = "backtest.json"
        original = dict()
        f = open(filename)
        original = json.load(f)

        # get alert tweets from DB
        result = self.db["data"].aggregate([
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
                "action": ["TICKER_ACTION_DIRECTION_IN_PRICE_SL_POINTS"]
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
                print(f"{tid} already in backtest.json")
            else:
                print(f"{tid} adding to backtest.json")
                out = {
                    "tid": i["tid"],
                    "text": i["text"],
                    "action": i["action"],
                }
                write_json(out)

    def backtest_parser(self):
        pass

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
            t.watch(username=username)
            time.sleep(5)

    @click.command()
    def backtest():
        p = ParseAlert(db)
        print(f"Updating backtest.json")
        p.update_backtest_file()

    cli.add_command(readdb)
    cli.add_command(fetch)
    cli.add_command(watch)
    cli.add_command(backtest)
    cli()
