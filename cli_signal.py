import click
import logging
from northy.logger import setup_logger
from northy.signal2 import Signal

if __name__ == '__main__':
    setup_logger()
    logger = logging.getLogger(__name__)

    @click.group()
    def cli():
        pass

    @click.command()
    @click.option('--tweet', default=None, type=str, help='Twitter ID to lookup and parse')
    def parse(tweet):
        signal = Signal()
        print("Parsing tweet", tweet)
        sig = signal.parse(tid=tweet)
        print(sig)

    @click.command()
    def watch():
        logger.info("watch")
        signal = Signal()
        signal.watch()

    cli.add_command(parse)
    cli.add_command(watch)
    cli()