from flask import Flask
from northy.tweets import Tweets, TweetsDB, Helper
from northy.config import config

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World!"

@app.route('/fetch')
def fetch():
    tweets = Tweets(config)
    db = TweetsDB(config)

    # TODO: Implement HTTP Request Header key to prevent abuse
    data = tweets.fetch(max_results=5).data
    for tweet in data:
        db.add_tweet(tweet)

    # wait for rate limit
    response = { 'status': 'success' }
    return response

if __name__ == '__main__':
    app.run(debug=True, port=4444)

