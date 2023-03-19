import click
import time
from northy.timon import Timon
from northy.TradeSignal import Signal

if __name__ == '__main__':
    @click.group()
    def cli():
        pass

    @click.command()
    @click.option('--limit', default=10, help='Number of tweets to return')
    @click.option('--username', default=None, help='Filter by username')
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
        t.watch(username=username, limit=limit)

    @click.command()
    @click.option('--username', default="NTLiveStream", help='Filter by username')
    def watch(username):
        """ Watch for new Tweets by user """
        t = Timon()
        while True:
            try:
                t.watch(username=username)
                time.sleep(5)
            except Exception as e:
                print(f"Exception {e}")
                print(f"Going to sleep for 1 min.")
                time.sleep(60)

    @click.command()
    def pushalert():
        """ Send push notifications when new Tweets are added to DB  """
        t = Timon()
        t.pushalert()

    @click.command()
    @click.option('--generate', default=False, is_flag=True, help='Update backtest.json file with latest signals (without overriding manual checks)')
    @click.option('--backtest', default=False, is_flag=True, help='Compare dynamicly parsed Tweets from DB against manually validated Tweets from backtest file')
    @click.option('--parse', default="", type=str, help='Dynamically parse raw Tweet text and update DB with signal')
    @click.option('--parseall', default=False, is_flag=True, help='Run --parse on entire DB')
    @click.pass_context
    def signal(ctx, generate, parse, parseall, backtest):
        """ Update backtesting file """
        s = Signal()
        if generate:
            print(f"Updating backtest.json")
            s.generate_signals_file()

        elif parse != "":
            signal = s.parse(parse)

        elif parseall:
            s.parseall()

        elif backtest:
            s.backtest()

        else:
            click.echo(ctx.get_help())


    @click.command()
    def datafeed():
        """ Fetch data from TradingView """
        t = Timon()
        while True:
            try:
                t.datafeed()
                print(f"Going to sleep for 12 hour")
                time.sleep(60*60*12)  # 12 hours
            except Exception as e:
                print(f"Exception {e}")
                print(f"Going to sleep for 1 hour")
                time.sleep(60*60)


    cli.add_command(readdb)
    cli.add_command(fetch)
    cli.add_command(watch)
    cli.add_command(pushalert)
    cli.add_command(signal)
    cli.add_command(datafeed)
    cli()
