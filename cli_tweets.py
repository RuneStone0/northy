import time
import click
import logging
from northy.config import config
from northy.logger import setup_logger
from northy.tweets import Tweets, TweetsDB
tweets = Tweets(config)

if __name__ == '__main__':
    setup_logger()
    logger = logging.getLogger(__name__)

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
            tweets.pprint(tweet)

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
        tweets.rate_limit_handler()

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

        tweetsdb = TweetsDB(config)
        latest_twitter_id = tweetsdb.get_latest()['tid']

        while True:
            # only fetch tweets during trading hours
            if tweets.is_trading_hours():
                try:
                    data = tweets.fetch(since_id=latest_twitter_id).data
                except Exception as e:
                    logger.error(e)
                    time.sleep(60)
                    continue

                for tweet in data:
                    inserted = tweetsdb.add_tweet(tweet)
                    tweets.pprint(tweet=tweet, inserted=inserted)

                latest_twitter_id = tweetsdb.get_latest()['tid']
                tweets.rate_limit_handler()

    cli.add_command(me)
    cli.add_command(search)
    cli.add_command(watch)
    cli.add_command(fetch)
    cli.add_command(fetchall)
    cli()