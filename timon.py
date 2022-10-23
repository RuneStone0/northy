import sys
import time
import click
import tweepy #https://github.com/tweepy/tweepy
from tweepy import OAuthHandler, StreamingClient
from datetime import datetime
from pymongo import MongoClient, DESCENDING, ASCENDING
from pymongo.errors import DuplicateKeyError
from dotenv import dotenv_values
#import pandas_market_calendars as mcal
from colorama import init, Fore, Back, Style
from termcolor import colored

config = dotenv_values(".env")

class Timon:
    def __init__(self):
        # APIv1 - Authenticate as a user
        #auth = tweepy.AppAuthHandler(config["consumer_key"], config["consumer_secret"])
        auth = tweepy.OAuthHandler(config["consumer_key"],config["consumer_secret"])
        auth.set_access_token(config["access_key"],config["access_secret"])

        self.api = tweepy.API(auth, wait_on_rate_limit=True)
        #for tweet in tweepy.Cursor(self.api.search_tweets, q='NTLiveStream').items(10):
        #    print(tweet.text)
        """
        response = self.api.user_timeline(screen_name="NTLiveStream", count=10)
        for i in response:
            i = i._json
            is_str = i["id_str"]
            text = i["text"]
            print(is_str, text)

            print()
        """
        
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

    cli.add_command(readdb)
    cli.add_command(fetch)
    cli.add_command(watch)
    cli()
