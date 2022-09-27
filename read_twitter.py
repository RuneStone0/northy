#!/usr/bin/env python
# encoding: utf-8

import tweepy #https://github.com/tweepy/tweepy
import pymongo
import csv

#Twitter API credentials
consumer_key = "On22KdCVqmBAgIwQSmOL1o2Vb"
consumer_secret = "xXjb6CYqUquwIe6DE9nZK9qXRI5DrNCxVIXuVI4JPKZgZB8NPm"
access_key = "246817629-Z9u8ckPBtyW5I4Oeyi6I6aw3mTQgRQnGvZwggU5Y"
access_secret = "Qoelk3g2hiDt1id6m3oWbIcHegTiNVPH84NE2zjmOQVDZ"

consumer_key = "b2Qw7nJybnlq6BQLKYT4wyIAw"
consumer_secret = "1rdFkXpFNBBMGCn6KPLsgu7614qjXAputpCR9NV1AbWGtTNpx4"
access_key = "135063402-3Ioj0qJS5AYpiU3TGKnByGQuocs875k9ByqgZS3E"
access_secret = "Nq09B0MU73PloD0uzwOteBWl8CcwlRuYnR5s2PmGaVlTt"

myclient = pymongo.MongoClient("mongodb://northy:IOnABlbDpAnTOTmeLUceveLYTUnbu@btc.brilliantr.com:27017")
mydb = myclient["northy"]

def get_all_tweets(screen_name):
    #Twitter only allows access to a users most recent 3240 tweets with this method
    
    #authorize twitter, initialize tweepy
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth)
    
    #initialize a list to hold all the tweepy Tweets
    alltweets = []  
    
    #make initial request for most recent tweets (200 is the maximum allowed count)
    new_tweets = api.user_timeline(screen_name = screen_name,count=200)
    
    #save most recent tweets
    alltweets.extend(new_tweets)
    
    #save the id of the oldest tweet less one
    oldest = alltweets[-1].id - 1   
    
    #keep grabbing tweets until there are no tweets left to grab
    while len(new_tweets) > 0:
        print(f"getting tweets before {oldest}")
        
        #all subsiquent requests use the max_id param to prevent duplicates
        new_tweets = api.user_timeline(screen_name = screen_name,count=200,max_id=oldest)
        
        #save most recent tweets
        alltweets.extend(new_tweets)
        
        #update the id of the oldest tweet less one
        oldest = alltweets[-1].id - 1
        
        print(f"...{len(alltweets)} tweets downloaded so far")
    
    mycol = mydb["data"]

    for tweet in alltweets:
        mydict = {"id_str": tweet.id_str, "created_at":  tweet.created_at, "text": tweet.text }
        try:
            mycol.insert_one(mydict)            
        except pymongo.errors.DuplicateKeyError:
            pass
        


    exit(0)
    #transform the tweepy tweets into a 2D array that will populate the csv 
    outtweets = [[tweet.id_str, tweet.created_at, tweet.text] for tweet in alltweets]


    #write the csv  
    with open(f'new_{screen_name}_tweets.csv', 'w',  encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id","created_at","text"])
        writer.writerows(outtweets)
    
    pass
    

if __name__ == '__main__':
	#pass in the username of the account you want to download
	#get_all_tweets("NTLiveStream")
    get_all_tweets("52544B")
    
     