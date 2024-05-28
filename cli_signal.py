import os
import click
import inspect
import logging
from northy.config import Config
from northy.prowl import Prowl
from northy.signal2 import Signal
from northy.logger import setup_logger

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
@click.option('--tid', default=None, type=str, help='Parse Twitter ID')
@click.pass_context
def parse(ctx, tid):
    # Parse the tweet
    if tid:
        signal = Signal()
        res = signal.parse(tid=tid)
        logger.info(f"{tid} --> {res}")
    
    # No input provided
    else:
        click.echo(ctx.get_help())

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

if __name__ == '__main__':
    # Automatically add all commands to the group
    for name, obj in globals().copy().items():
        if inspect.isfunction(obj) and obj.__module__ == __name__:
            cli.add_command(obj)
    
    cli()