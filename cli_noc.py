import time
import click
import logging
from northy.noc import Noc
from northy.logger import setup_logger

if __name__ == '__main__':
    setup_logger(filename='noc.log')
    logger = logging.getLogger(__name__)

    @click.group()
    def cli():
        pass

    @click.command()
    def watch():
        """
        """
        noc = Noc()
        noc.watch()

    cli.add_command(watch)
    cli()