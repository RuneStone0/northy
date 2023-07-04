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

        data = tweets.fetch(max_results=limit).data
        for tweet in data:
            db.add_tweet(tweet)

        # wait for rate limit
        helper.rate_limit_handler()

    @click.command()
    def fetchall():
        tweets = Tweets(config)
        tweets.fetchall()

    @click.command()
    def watch():
        """
            Watch for new tweets and add them into the DB.
        """
        tweets = Tweets(config)
        helper = Helper()

        tweetsdb = TweetsDB(config)
        latest_twitter_id = tweetsdb.get_latest()['tid']

        while True:
            # only fetch tweets during trading hours
            if helper.is_trading_hours():
                try:
                    data = tweets.fetch(since_id=latest_twitter_id).data
                except Exception as e:
                    logger.error(e)
                    time.sleep(60)
                    continue

                for tweet in data:
                    tweetsdb.add_tweet(tweet)

                latest_twitter_id = tweetsdb.get_latest()['tid']
                helper.rate_limit_handler()

    cli.add_command(me)
    cli.add_command(search)
    cli.add_command(watch)
    cli.add_command(fetch)
    cli.add_command(fetchall)
    cli()