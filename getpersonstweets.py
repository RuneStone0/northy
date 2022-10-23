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
api = tweepy.API(auth, wait_on_rate_limit=True)

# You can authenticate as your app with just your bearer token
client = tweepy.Client(bearer_token=config["bearer_token"])

# You can provide the consumer key and secret with the access token and access
# token secret to authenticate as a user
client = tweepy.Client(
    consumer_key=consumer_key, consumer_secret=consumer_secret,
    access_token=access_token, access_token_secret=access_token_secret
)



screen_name_cache = {}
def add_tweet_to_db(tweet):
	"""
	# Lookup account name from tweet and insert it into Mongo
	# To avoid a million loopups, we create a simple cache
	account_name = None
	print(tweet.data)
	print()
	_author_id = tweet.user.id
	if _author_id not in screen_name_cache.keys():
		user = api.get_user(user_id=_author_id)
		screen_name_cache[_author_id] = user.screen_name
	"""
	mydict = {
		"tid": tweet.id_str,
		#"username": screen_name_cache[_author_id],
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
			print(tweet.data)
			print(tweet.includes)
			tid = tweet.id
			print(tid, tweet)
			#print(tweet.user_id)
			#add_tweet_to_db(tweet)
			sys.exit()

	stream = listener(config["bearer_token"])
	rule = "from:NTLiveStream OR from:52544B"
	print(f"+ Listener Rule: {rule}")
	stream.add_rules(tweepy.StreamRule(rule))

	# accounts with high tweeting frequency  ["everycolorbot", "tinycarebot", "dscovr_epic", "MagicRealismBot", "earthquakeBot", "MoMArobot", "poem_exe"]
	print(f"+ Starting listener. Waiting for tweets..")
	#stream.filter() # , async=True
	
	# For testing purposes.  Streams about 1% of all Tweets in real-time
	stream.sample()  


def unit_testing():
	#tweets = api.search_recent_tweets('Artificial Intelligence', count=1)
	response = client.search_recent_tweets("AI", max_results=10, expansions=["author_id"], user_fields=['username'])
	includes = response.includes
	tweets = response.data
	def _get_username(user_id):
		for user in includes["users"]:
			if user_id == user.id:
				return user.username

	for tweet in tweets:
		print(tweet)
		print(tweet.id, tweet.text)
		print(tweet.author_id)
		#print(tweet.username)
		#add_tweet_to_db(tweets)
		#username = _get_username(tweet.author_id)
		#print(f"Username: {username}")


def tweet_id_to_username(tweet_id=1578956182341185536):
	tweet_ids = [tweet_id]

	# By default, only the ID and text fields of each Tweet will be returned
	# Additional fields can be retrieved using the tweet_fields parameter
	response = client.get_tweets(tweet_ids, tweet_fields=["created_at"], expansions=["author_id"], user_fields=['username'])
	includes = response.includes
	for tweet in response:
		#print(tweet)
		print(includes)

		username = includes["users"][0]
		return username

def unittest_tweet_id_to_username():
	for tweet_id in [1578956182341185536,1579114131155623936,1578482250647502848]:
		username = tweet_id_to_username(tweet_id)
		print(username)

if __name__ == '__main__':
	#create_db_index()
	#pass in the username of the account you want to download
	#get_all_tweets("NTLiveStream")
	#get_all_tweets("52544B")
	unittest_tweet_id_to_username()
	tweet_id_to_username("1579114131155623936")
	#stream()

	#unit_testing()