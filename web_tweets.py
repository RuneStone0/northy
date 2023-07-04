import sys
from flask import Flask, request
from northy.tweets import Tweets, TweetsDB, Helper
from northy.config import config

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World!"

@app.route('/fetch', methods=['POST'])
def fetch():
    tweets = Tweets(config)
    db = TweetsDB(config)
    data = request.json
    mock_data = {
        "anapp": "Twitter",
        "anbigicon": "%anbigicon",
        "anbutton1action": "d9ba37b0-ff59-43f9-940a-f1bf11312ada",
        "anbutton1icon": "file:///storage/emulated/0/Download/AutoNotification/icons/com.twitter.android_-1803146057",
        "anbutton1text": "Reply",
        "anbutton2action": "5eded131-4984-444b-b2a9-8afe37d18857",
        "anbutton2icon": "file:///storage/emulated/0/Download/AutoNotification/icons/com.twitter.android_-1802222536",
        "anbutton2text": "Retweet",
        "anbutton3action": "d8f5e041-ea22-48a5-b18a-1355ef08af59",
        "anbutton3icon": "file:///storage/emulated/0/Download/AutoNotification/icons/com.twitter.android_-1801299015",
        "anbutton3text": "Like",
        "ancategoryid": "246817629-tweet_notifications_silent",
        "ancolor": "#1D9BF0",
        "andismissaction": "d18cda9c-03bc-4697-9d7e-e91911d03b24",
        "ankey": "0|com.twitter.android|34|notification://com.twitter.android?user_id=246817629|10073",
        "anreplyaction": "ebac6193-3c74-4375-9275-ba46a1420cf2",
        "anstatus": "Created",
        "anstatusbaricon": "file:///storage/emulated/0/Download/AutoNotification/icons/com.twitter.android_3226745",
        "antag": "notification://com.twitter.android?user_id=246817629",
        "antext": "Another tweet",
        "anticker": "Another tweet",
        "antitle": "RuneStone",
        "antouchaction": "d59607cb-5edf-4fab-8aa9-8634a22df00e",
        "anwhentime": "1688498748786"
    }

    antag = data["antag"]  # URL to Twitter App, opening User ID
    antext = data["antext"]  # Tweet text
    antitle = data["antitle"]  # Tweet Nickname

    response = {}
    # Handle NTLiveStream Tweet
    if "897502744298258432" in antag:
        print(f"Tweet from {antitle}: {antext}")
        # Initialize fetch of tweets
        # TODO: Only fetch if its ALERT tweet
        for tweet in tweets.fetch(max_results=5).data: db.add_tweet(tweet)
        response["status"] = "success"
        response["title"] = antitle
        response["text"] = antext
        
    # Handle RuneStone Tweet (for debugging purposes)
    elif "246817629" in antag:
        print(f"Tweet from {antitle}: {antext}")
        response["status"] = "success"
        response["title"] = antitle
        response["text"] = antext
    
    # Any other tweet, we ignore
    else:
        response["status"] = "skip"

    return response

if __name__ == '__main__':
    host = '0.0.0.0' if '--live' in sys.argv else '127.0.0.1'
    app.run(debug=True, port=4444, host=host)

