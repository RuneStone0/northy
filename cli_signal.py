import os
import click
import logging
from northy.config import Config
from northy.prowl import Prowl
from northy.signal2 import Signal
from northy.logger import setup_logger

if __name__ == '__main__':
    config = Config().config
    
    setup_logger(filename='signal.log')
    logger = logging.getLogger(__name__)

    @click.group()
    @click.option('--prod', default=False, is_flag=True, type=bool, help='Enable production mode')
    def cli(prod):
        # set environment variable
        os.environ["PRODUCTION"] = str(prod)
        pass

    @cli.command()
    @click.option('--tweet', default=None, type=str, help='Parse Twitter ID')
    def parse(tweet):
        # No input provided
        if tweet is None:
            logger.info("No tweet id provided")
            return

        signal = Signal()
        signal.parse(tid=tweet)

    @cli.command()
    def watch():
        """ 
            Watch for new tweets and signals.
        """
        try:
            signal = Signal()
            signal.watch()
        except Exception as e:
            p = Prowl()
            p.send("Error: cli_signal.py crashed!!")
            logger.critical(e, exc_info=True)

    cli.add_command(parse)
    cli.add_command(watch)
    cli()