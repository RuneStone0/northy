import click
import logging
from northy.logger import setup_logger
from northy.saxo import Saxo
from northy.config import config
from northy.tweets import TweetsDB

if __name__ == '__main__':
    setup_logger()
    logger = logging.getLogger(__name__)

    saxo = Saxo()

    @click.group()
    def cli():
        pass

    @click.command()
    def positions():
        """ List positions """
        positions = saxo.positions()
        print(positions)

    @click.command()
    def orders():
        """ List orders """
        orders = saxo.orders()
        for o in orders["Data"]:
            print(o["BuySell"], o["Uic"], o["Amount"], o["Status"])

    @click.command()
    @click.option('--symbol', required=True, type=str, help='Symbol to trade')
    @click.option('--amount', required=True, type=str, help='Amount to trade')
    @click.option('--buy', default=True, type=bool, help='Buy (default) or Sell (False)')
    @click.option('--points', default=None, type=int, help='Stop Loss points')
    def market(symbol, amount, buy, points):
        """ Execute rades """
        order = saxo.market(symbol=symbol, amount=amount, buy=buy, stoploss_points=points)
        print(order)

    @click.command()
    @click.option('--symbol', required=True, type=str, help='Symbol to trade')
    @click.option('--amount', required=True, type=str, help='Amount to trade')
    @click.option('--price', required=True, type=int, help='Limit price')
    @click.option('--buy', default=True, type=bool, help='Buy (default) or Sell (False)')
    @click.option('--stoploss_price', default=None, type=int, help='Stop Loss price')
    @click.option('--points', default=None, type=int, help='Stop Loss points')
    def limit(symbol, amount, buy, price, stoploss_price, points):
        """ Execute rades """
        order = saxo.limit(symbol=symbol,
            amount=amount,
            limit=price, 
            buy=buy,
            stoploss_price=stoploss_price,
            stoploss_points=points)
        print(order)

    @click.command()
    @click.option('--signal', default=None, type=str, help='Trade signal (e.g. SPX_TRADE_LONG_IN_3609_SL_10)')
    @click.option('--tweet', default=None, type=str, help='Execute trades for a specific tweet id')
    def trade(signal, tweet):
        """ Execute trade(s) based on a signal or tweet id """
        if signal is not None:
            saxo.trade(signal=signal)
        elif tweet is not None:
            print(tweet)
            tdb = TweetsDB(config)
            doc = tdb.get_tweet(tweet)
            for signal in doc["signals"]:
                saxo.trade(signal=signal)
        else:
            print("Something is not right..")

    @click.command()
    @click.pass_context
    def watch(ctx):
        """
            Watch for new signals
        """
        from northy.db import Database
        db = Database().db

        logger.info("Starting change stream...")
        while True:
            # Watch for new documents (tweets) where "alert" is not set
            pipeline = [
                { "$match": { "operationType": { "$in": ["update"] } } }, # 'insert', 'update', 'replace', 'delete'
            ]

            # Only process tweets younger than 5 minutes
            #now = datetime.now()
            #pipeline.append({ "$match": { "createdAt": { "$lt": now - datetime.timedelta(minutes=5) } } })

            # Create a change stream
            change_stream = db["tweets"].watch(pipeline, full_document='updateLookup')

            # Iterate over the change stream
            for change in change_stream:
                doc = change["fullDocument"]
                tid = doc["tid"]
                logger.info("Detected change for %s", tid)

                # Make sure its an alert
                # TODO: Move this check to pipeline
                if not doc["alert"]:
                    logger.info("No alert found. Skipping..")
                    continue
                else:
                    # Initiate trade for signals
                    logger.info("Initiating trade for %s", tid)
                    #ctx.invoke(trade, tweet=tid)


    cli.add_command(positions)
    cli.add_command(market)
    cli.add_command(limit)
    cli.add_command(orders)
    cli.add_command(trade)
    cli.add_command(watch)
    cli()
