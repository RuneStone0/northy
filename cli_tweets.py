import time
import click
import logging
from northy.config import config
from northy.logger import setup_logger
from northy.tweets import Tweets, TweetsDB
from northy.prowl import Prowl
tweets = Tweets(config)

if __name__ == '__main__':
    setup_logger(filename='tweets.log')
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
        found_max_tweets = False

        while True:
            # only fetch tweets when needed
            tweets.tweet_throttle()

            # Attempt to fetch new tweets
            try:
                if not found_max_tweets:
                    # By default, we only fetch 5 tweets at a time
                    data = tweets.fetch(since_id=latest_twitter_id)["data"]
                else:
                    # If we found 5 tweets on previous run, we fetch more next time
                    data = tweets.fetch(since_id=latest_twitter_id, max_results=25)["data"]
                
                # Logic that decides if we should fetch more tweets next time
                if len(data) == 5:
                    logger.info(f"Found {len(data)} tweets. Bump next fetch to 25 tweets.")
                    found_max_tweets = True
            except Exception as e:
                logger.error(f"cli_tweets.py unexpected error", exc_info=True)
                prowl = Prowl(API_KEY=config["PROWL_API_KEY"])
                prowl.send(f"cli_tweets.py unexpected error")
                time.sleep(60)
                continue

            # Process and store the tweets
            for tweet in data:
                inserted = tweetsdb.add_tweet(tweet)
                tweets.pprint(tweet=tweet, inserted=inserted)

            # Update the latest_twitter_id to fetch from
            latest_twitter_id = tweetsdb.get_latest()['tid']

            tweets.rate_limit_handler() # Roughly 3 min. delay

    cli.add_command(me)
    cli.add_command(search)
    cli.add_command(watch)
    cli.add_command(fetch)
    cli.add_command(fetchall)
    cli()