import click
import logging
from northy.logger import setup_logger
from northy.saxo import Saxo, SaxoHelper
from northy.config import config, set_env
from northy.tweets import TweetsDB
from northy.prowl import Prowl

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
        positions = saxo.positions(cfd_only=False, profit_only=False)
        saxo_helper = SaxoHelper()
        saxo_helper.pprint_positions(positions)

    @click.command()
    @click.option('--id', required=True, type=str, help='Position ID')
    def close_position(id):
        """ Close position """

        # Find position object by looping through all positions
        positions = saxo.positions(cfd_only=False, profit_only=False)
        for position in positions["Data"]:
            pos_id = position["PositionId"]
            if pos_id == id:
                # Close position
                logger.info("Closing position %s" % pos_id)
                saxo.close(position)
                return

        logger.info("Position not found")

    @click.command()
    def report_closed_positions():
        """ Report Closed Positions """
        # Set environment variables
        set_env()

        saxo_helper = SaxoHelper()
        while True:
            positions = saxo.positions(status_open=False, profit_only=False)
            saxo_helper.job_generate_closed_positions_report(positions=positions)
        
    @click.command()
    def orders():
        """ List orders """
        orders = saxo.orders()
        for o in orders["Data"]:
            print(o["BuySell"], o["Uic"], o["Amount"], o["Status"])

    @click.command()
    @click.option('--orders', required=True, type=str, help='Comma separated list of Order IDs')
    def cancel_orders(orders):
        """ Cancel Orders """
        saxo.cancel_order(orders)

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
    def watch():
        """
            Watch for alerts and execute trades
        """
        try:
            saxo.watch()
        except Exception as e:
            p = Prowl(API_KEY=config["PROWL_API_KEY"])
            p.send("Error: cli_saxo.py crashed!!")
            logger.error(e)

    cli.add_command(report_closed_positions)
    cli.add_command(positions)
    cli.add_command(close_position)
    cli.add_command(market)
    cli.add_command(limit)
    cli.add_command(orders)
    cli.add_command(trade)
    cli.add_command(watch)
    cli()
