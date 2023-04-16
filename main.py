import os
import click
import time
from northy.timon import Timon
from northy.TradeSignal import Signal
from northy.logger import get_logger
from northy.utils import Utils
import os
from datetime import datetime

u = Utils()
logger = get_logger("main", "main.log")

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

        config = u.get_config()
        database_name = "northy"
        tweets_collection_name = "tweets"

        mongodump = os.getcwd() + "\\backups\\mongodump"
        folder_name = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"
        mongodb_conn = config["mongodb_conn"]
        cmd = f'{mongodump} --uri="{mongodb_conn}" --collection="{tweets_collection_name}" --db="{database_name}" --out="backups/{folder_name}"'
        os.system(cmd)
        logger.info("Backup complete!")

    @click.command()
    @click.option('--limit', default=10, help='Number of tweets to return')
    @click.option('--username', default="NTLiveStream", help='Filter by username')
    def readdb(username, limit):
        """ Read Tweets from DB """
        t = Timon()
        t.readdb(username=username, limit=limit)
    
    @click.command()
    @click.option('--limit', default=200, help='Number of tweets to return')
    @click.option('--username', default="NTLiveStream", help='Filter by username')
    def fetch(username, limit):
        """
            Fetching the lastest 200 tweets from user and adds them into the DB.
            This is mainly used when DB is out of sync.
        """
        t = Timon()
        t.fetch(username=username, limit=limit)

    @click.command()
    @click.option('--username', default="NTLiveStream", help='Filter by username')
    def watch(username):
        """ Watch for new Tweets by user """
        logger.info("Watching for new Tweets..")
        t = Timon()
        t.watch()

    @click.command()
    def watch2():
        """ Watch2 """
        t = Timon()
        t.watch2()

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
    def datafeed():
        """ Fetch data from TradingView """
        t = Timon()
        while True:
            try:
                t.datafeed()
                logger.info(f"Going to sleep for 12 hour")
                time.sleep(60*60*12)  # 12 hours
            except Exception as e:
                logger.error(f"Exception {e}")
                logger.info(f"Going to sleep for 1 hour")
                time.sleep(60*60)

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
            from northy import SaxoTrader
            trader = SaxoTrader.Saxo()
            trader.trade(signal)
            print("Signal: ", signal)

    cli.add_command(backup)
    cli.add_command(readdb)
    cli.add_command(fetch)
    cli.add_command(watch)
    cli.add_command(watch2)
    cli.add_command(signal)
    cli.add_command(trade)
    cli.add_command(datafeed)
    cli()
