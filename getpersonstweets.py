#!/usr/bin/env python
# encoding: utf-8

import tweepy #https://github.com/tweepy/tweepy
from tweepy import OAuthHandler, StreamingClient
from pymongo import MongoClient, DESCENDING
from pymongo.errors import DuplicateKeyError
from dotenv import dotenv_values
config = dotenv_values(".env")

myclient = MongoClient(config["mongodb_conn"])
db = myclient["northy"]
db_collection = db["data2"]

#authorize twitter, initialize tweepy
auth = tweepy.OAuthHandler(config["consumer_key"], config["consumer_secret"])
auth.set_access_token(config["access_key"], config["access_secret"])
api = tweepy.API(auth)

screen_name_cache = {}
def add_tweet_to_db(tweet):
	# Lookup account name from tweet and insert it into Mongo
	# To avoid a million loopups, we create a simple cache
	account_name = None
	_author_id = tweet.user.id
	if _author_id not in screen_name_cache.keys():
		user = api.get_user(user_id=_author_id)
		screen_name_cache[_author_id] = user.screen_name

	mydict = {
		"tid": tweet.id_str,
		"account_name": screen_name_cache[_author_id],
		"created_at":  tweet.created_at,
		"text": tweet.text 
	}
	try:
		db_collection.insert_one(mydict)
	except DuplicateKeyError:
		print("Duplicated Key")
		pass

def get_all_tweets(screen_name):
	#Twitter only allows access to a users most recent 3240 tweets with this method

	#initialize a list to hold all the tweepy Tweets
	alltweets = []  

	#make initial request for most recent tweets (200 is the maximum allowed count)
	new_tweets = api.user_timeline(screen_name = screen_name, count=200)

	#save most recent tweets
	alltweets.extend(new_tweets)

	#save the id of the oldest tweet less one
	oldest = alltweets[-1].id - 1

	#keep grabbing tweets until there are no tweets left to grab
	while len(new_tweets) > 0:
		print(f"getting tweets before {oldest}")
		
		#all subsiquent requests use the max_id param to prevent duplicates
		new_tweets = api.user_timeline(screen_name = screen_name, count=200, max_id=oldest)
		
		#save most recent tweets
		alltweets.extend(new_tweets)
		
		#update the id of the oldest tweet less one
		oldest = alltweets[-1].id - 1
		
		print(f"...{len(alltweets)} tweets downloaded so far")

	for tweet in alltweets:
		add_tweet_to_db(tweet)

def create_db_index():
	# Create an index for PLDs ensuring we only have unique PLds
	db_collection.create_index([("tid", DESCENDING)], background=True, unique=True)

def stream():
	class listener(StreamingClient):
		def on_status(self, status):
			print(status.text)
		
		def on_error(self, status_code):
			if status_code == 420:
				print(f"error {status_code}")
				return False
		
		def on_tweet(self, tweet):
			tid = tweet.id
			print(tid, tweet)
			add_tweet_to_db(tweet)

	stream = listener(config["bearer_token"])
	rule = "from:NTLiveStream OR from:52544B"
	print(f"+ Listener Rule: {rule}")
	stream.add_rules(tweepy.StreamRule(rule))

	# accounts with high tweeting frequency  ["everycolorbot", "tinycarebot", "dscovr_epic", "MagicRealismBot", "earthquakeBot", "MoMArobot", "poem_exe"]
	print(f"+ Starting listener. Waiting for tweets..")
	stream.filter() # , async=True
	
	# For testing purposes.  Streams about 1% of all Tweets in real-time
	#stream.sample()  

if __name__ == '__main__':
	create_db_index()
	#pass in the username of the account you want to download
	#get_all_tweets("NTLiveStream")
	#get_all_tweets("52544B")
	stream()
