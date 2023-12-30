import click
import logging
from northy.prowl import Prowl
from northy.config import config
from northy.signal2 import Signal
from northy.logger import setup_logger

if __name__ == '__main__':
    setup_logger(filename='signal.log')
    logger = logging.getLogger(__name__)

    @click.group()
    def cli():
        pass

    @click.command()
    @click.option('--tweet', default=None, type=str, help='Parse Twitter ID')
    def parse(tweet):
        # No input provided
        if tweet is None:
            logger.info("No tweet id provided")
            return

        signal = Signal()
        signal.parse(tid=tweet)

    @click.command()
    @click.option('--timeout', default=-1, type=float, 
                  help='Kill process after x min.')
    def watch(timeout):
        """ 
            Watch for new tweets and signals.

            Args:
                timeout: Timeout in minutes. Deault will run forever.
        """
        try:
            signal = Signal()
            signal.watch(timeout=timeout)
        except Exception as e:
            p = Prowl(API_KEY=config["PROWL_API_KEY"])
            p.send("Error: cli_signal.py crashed!!")
            logger.critical(e, exc_info=True)

    cli.add_command(parse)
    cli.add_command(watch)
    cli()