import os
import click
from northy.signal2 import Signal
from northy.logger import get_logger
from northy.utils import Utils
from northy.config import config
from northy.tweets import Tweets
from northy.autotrader import AutoTrader
from datetime import datetime
from northy.db import Database

u = Utils()
logger = get_logger("main", "main.log")
db = Database().db

if __name__ == '__main__':
    # set env var to PYTHONDONTWRITEBYTECODE=1
    # to prevent .pyc files from being created
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

    @click.group()
    def cli():
        pass

    @click.command()
    def backup():
        """ Backup DB """
        logger.info("Backing up DB..")

        database_name = "northy"
        tweets_collection_name = "tweets"

        mongodump = os.getcwd() + "\\backups\\mongodump"
        folder_name = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
        mongodb_conn = config["mongodb_conn"]
        cmd = f'{mongodump} --uri="{mongodb_conn}" --collection="{tweets_collection_name}" --db="{database_name}" --out="backups/{folder_name}"'
        os.system(cmd)
        logger.info("Backup complete!")

    @click.command()
    @click.option('--limit', default=200, help='Number of tweets to return')
    def fetch(limit):
        """
            Fetching the lastest 200 tweets from user and adds them into the DB.
            This is mainly used when DB is out of sync.
        """
        tw = Tweets(db=db)
        tw.fetch(limit=limit)

    @click.command()
    @click.option('--tweets', default=False, is_flag=True, help='Watch for new Tweets')
    @click.option('--alerts', default=False, is_flag=True, help='Watch for new Trading Alerts')
    def watch(tweets, alerts):
        """
            Watch for new Tweets or Alerts.
        """
        if tweets:
            tw = Tweets(db=db)
            tw.watcher()
        elif alerts:
            s = Signal()
            s.watcher()
        else:
            logger.info("Please specify --tweets or --alerts")

    @click.command()
    @click.option('--backtest', default=False, is_flag=True, help='Compare dynamicly parsed Tweets from DB against manually validated Tweets from backtest file')
    @click.option('--parse', default="", type=str, help='Dynamically parse raw Tweet text and update DB with signal')
    @click.option('--get', default="", type=str, help='Lookup signal by Tweet ID')
    @click.option('--getall', default=False, is_flag=True, help='Get all signals from DB')
    @click.option('--update', default="", type=str, help='Update signal in DB by Tweet ID')
    @click.option('--updateall', default=False, is_flag=True, help='Update all signals in DB')
    @click.option('--parseall', default=False, is_flag=True, help='Run --parse on entire DB')
    @click.option('--manual', default="", type=str, help='Manually review by ID')
    @click.option('--manualall', default=False, is_flag=True, help='Manually review all signals in DB')
    @click.option('--export', default=False, is_flag=True, help='Export all signals from DB to CSV file (signals.csv)')
    @click.pass_context
    def signal(ctx, parse, parseall, backtest, get, getall, update, updateall, manual, manualall, export):
        """ Manage Trading Signals """
        s = Signal()
        if parse != "":
            s.parse(parse)

        elif get:
            s.get(get)

        elif getall:
            s.getall()

        elif update:
            s.update(update)

        elif updateall:
            s.updateall()

        elif parseall:
            s.parseall()

        elif backtest:
            s.backtest()

        elif manualall:
            s.manualall()

        elif manual:
            s.manual(manual)

        elif export:
            s.export()

        else:
            click.echo(ctx.get_help())

    @click.command()
    @click.option('--tid', default="", type=str, help='Execute trades by Twitter ID')
    def trade(tid):
        """ SaxoTrader """
        print("Trade")
        s = Signal()
        signals = s.get(tid)
        print("Twitter ID: ", tid)
        print("Signals: ", signals)
        for signal in signals:
            from northy import saxo
            trader = saxo.Saxo()
            trader.trade(signal)
            print("Signal: ", signal)

    @click.command()
    def autotrader():
        """ AutoTrader """
        trader = AutoTrader(db=db)
        trader.run()

    @click.command()
    @click.option('--signal', default="", type=str, help='Manually trade signal')
    def trader(signal):
        """ AutoTrader """
        trader = AutoTrader(db=db)
        trader.process_signal(signal)

    @click.command()
    def tweets():
        """ AutoTrader """
        tweets = Tweets()
        trader.process_signal(signal)


    cli.add_command(backup)
    cli.add_command(fetch)
    cli.add_command(watch)
    cli.add_command(signal)
    cli.add_command(trade)
    cli.add_command(autotrader)
    cli.add_command(trader)
    cli()
