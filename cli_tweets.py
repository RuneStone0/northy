import time
import click
import logging
from termcolor import colored
from northy.tweets import Tweets, TweetsDB, Helper
from northy.config import config
from datetime import datetime

# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
helper = Helper()

if __name__ == '__main__':
    @click.group()
    def cli():
        pass

    @click.command()
    def me():
        tweets = Tweets(config)
        tweets.me()

    @click.command()
    def search():
        tweets = Tweets(config)
        data = tweets.search(max_results=10)
        for tweet in data:
            helper.pprint(tweet)

    @click.command()
    @click.option('--limit', default=5, help='Number of tweets to return')
    def fetch(limit):
        """
            Fetching lastest tweets from user and adds them into the DB.
            This is mainly used when DB is out of sync.
        """
        tweets = Tweets(config)
        db = TweetsDB(config)

        data = tweets.fetch(limit=limit).data
        for tweet in data:
            db.add_tweet(tweet)

        # wait for rate limit
        helper.rate_limit_handler()

    @click.command()
    def fetchall():
        tweets = Tweets(config)
        tweets.all()

    @click.command()
    def watch():
        """
            Watch for new tweets and add them into the DB.
        """
        tweets = Tweets(config)
        while True:
            # if not weekday, sleep for 1 hour
            if datetime.today().weekday() >= 5:
                sleep_minutes = 60
                logger.info(f"It's weekend. Sleeping for {sleep_minutes} minutes..")
                time.sleep(sleep_minutes)
                continue

            # if time is not between 8:30 and 15:00 central time, sleep for 15 min
            now = datetime.now()
            if now.hour < 7 or now.hour > 15:
                sleep_minutes = 15
                logger.info(f"It's not trading hours. Sleeping for {sleep_minutes} min..")
                time.sleep(sleep_minutes*60)
                continue
            
            tweets.fetch(rate_limit=True)

    @click.command()
    def analyze():
        tweets = Tweets(config)
        tweets.all()

    cli.add_command(me)
    cli.add_command(search)
    cli.add_command(watch)
    cli.add_command(fetch)
    cli.add_command(fetchall)
    cli()