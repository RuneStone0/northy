import sys
import time
from termcolor import colored
from flask import Flask, request
from northy.tweets import Tweets, TweetsDB
from northy.config import config
from datetime import datetime
import logging
import pytz
import json, ast

def setup_logging():
    # Create a formatter with the desired log format
    base_log = colored('%(asctime)s [%(levelname)s]', "blue")
    log_format = f"{base_log} %(message)s"
    formatter = logging.Formatter(log_format, datefmt='%Y-%m-%d %H:%M:%S')

    # Create a handler and set the formatter
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    # Create a logger and add the handler
    log = logging.getLogger(__name__)
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)
    return log
log = setup_logging()

app = Flask(__name__)
config['x_northy'] = '18dc651a-983b-41d8-9220-eb7c93142afc'
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
non_alert_tweets = None

# Function to set the global variable
def set_non_alert_tweets():
    global non_alert_tweets
    non_alert_tweets = 0
    return non_alert_tweets

def increment_non_alert_tweets():
    global non_alert_tweets
    non_alert_tweets += 1
    return non_alert_tweets

def reset_non_alert_tweets():
    global non_alert_tweets
    non_alert_tweets = 0
    return non_alert_tweets

def get_non_alert_tweets():
    global non_alert_tweets
    return non_alert_tweets

# Register the function to be executed before the first request
@app.before_request
def before_request():
    global non_alert_tweets
    if non_alert_tweets is None:
        set_non_alert_tweets()

def debug():
    try:
        body = request.get_json()
    except:
        body = "[Empty]"
    print("------------ DEBUG ------------")
    print(colored('Received request:', "yellow"), request.method, request.path)
    print(colored('Request headers:', "yellow"), request.headers)
    print(colored('Request body:', "yellow"), body)
    print("------------ DEBUG ------------")

def parse_body(data):
    """
        Parse the body of the request.

        Tasker sometimes passes a string and sometimes passes bytes. This function will handle both cases.
    """
    if type(data) == str:
        return ast.literal_eval(data)
    elif type(data) == bytes:
        data = data.decode("utf-8")
        data = data.replace("\t", " ")
        data = data.replace("\n", " ")
        return json.loads(data)
    else:
        return data

@app.route('/')
def hello():
    debug()

    val = get_non_alert_tweets()
    msg = f"Hello, World! {val}"
    log.info(msg)
    increment_non_alert_tweets()
    return msg

@app.route('/fetch', methods=['POST'])
def fetch():
    debug()

    # Validate X-Northy header
    x_northy_header = request.headers.get('X-Northy')
    if x_northy_header != config['x_northy']:
        return 'Invalid X-Northy header', 401
    
    # Validate JSON data
    try:
        data = parse_body(request.data)
    except:
        print(f"Invalid JSON data: {request.data}", file=sys.stderr)
        return 'Invalid JSON data', 415

    # Get data from AutoNotification
    antext = data["antext"]  # Tweet text
    antitle = data["antitle"]  # Tweet Nickname

    # Prepare response
    response = {
        "status": "success",
        "title": antitle,
        "text": antext
    }

    # Process request
    log.info(f"Tweet from {antitle}: {antext}")
    if "Northy" in antitle:
        def fetch():
            # Fetch tweets
            tweets = Tweets(config)
            db = TweetsDB(config)

            """
                Insert delay, to make sure Twitter User Timeline is updated
                Push notifications are sent real-time to devices, while the 
                Twitter User Timeline takes a few seconds before its updated.
                If we attempt to fetch the timeline immedeatly, it will not 
                have latest Tweets.
            """
            sleep_time = 10
            log.info(f"Sleeping for {sleep_time} second before fetching..")
            time.sleep(sleep_time)

            log.info(colored(f"Fetching tweets from NTLiveStream", "green"))
            for tweet in tweets.fetch(max_results=5).data: db.add_tweet(tweet)

        log.info(f"non_alert_tweets counter: {non_alert_tweets}")
        if "ALERT" not in antext.upper():
            # Handle non-alert tweet
            increment_non_alert_tweets()
            log.info(f"ALERT not found in tweet, incrementing non_alert_tweets to {non_alert_tweets}")

            # Store non-alert tweets
            if non_alert_tweets >= 3:
                reset_non_alert_tweets()
                fetch()
        else:
            # Handle alert tweet
            reset_non_alert_tweets()
            log.info(f"ALERT found in tweet, resetting non_alert_tweets to {non_alert_tweets}")
            fetch()
        
        return response, 200
    
    elif "RuneStone" in antitle:
        # Handle RuneStone Tweet (for debugging purposes)
        pass
    
    else:
        # Any other tweet, we ignore
        log.info(colored(f"Ignoring Tweet from {antitle}: {antext}", "yellow"))
        response["status"] = "skip"

    return response, 200

if __name__ == '__main__':
    host = '0.0.0.0' if '--live' in sys.argv else '127.0.0.1'
    app.run(debug=True, port=4444, host=host)
