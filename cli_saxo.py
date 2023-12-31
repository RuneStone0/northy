import os
import click
import logging
from northy.prowl import Prowl
from northy.config import config
from northy.tweets import TweetsDB
from northy.logger import setup_logger
from northy.saxo import Saxo, SaxoHelper

if __name__ == '__main__':
    setup_logger(filename='saxo.log')
    logger = logging.getLogger(__name__)

    @click.group()
    @click.option('--profile', required=False, default="default", type=str, help='Set Saxo Profile')
    @click.pass_context
    def cli(ctx, profile):
        ctx.ensure_object(dict)
        os.environ["SAXO_PROFILE"] = profile

    @cli.command()
    def positions():
        """ List positions """
        saxo = Saxo()
        positions = saxo.positions(cfd_only=False, profit_only=False)
        saxo_helper = SaxoHelper()
        saxo_helper.pprint_positions(positions)

    @cli.command()
    @click.option('--id', required=True, type=str, help='Position ID')
    def close_position(id):
        """ Close position """
        saxo = Saxo()
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

    @cli.command()
    @click.option('--job', required=False, is_flag=True, default=False, 
                  type=bool, help='Run as background job')
    def report_closed_positions(job):
        """ 
            Report Closed Positions 

            This will generate a report of closed positions and send it by email.
            By default, the report will only be sent if there are new closed positions.
            If the --force option is used, the report will be sent regardless of whether
            there are new closed positions or not.

            The report will be sent daily at a specific (hardcoded) time.
        """
        from northy.saxo_report import SaxoReport
        saxo = Saxo()
        saxo_report = SaxoReport()

        # Run once
        if not job:
            logger.info("Running once")
            positions = saxo.positions(status=["Closed"], profit_only=False, show=True)
            saxo_report.send_report(positions)
            return

        # Run as background job
        while True:
            logger.info("Running as background job")
            saxo_report.close_report_sleep()
            positions = saxo.positions(status=["Closed"], profit_only=False)
            saxo_report.send_report(positions=positions)
        
    @cli.command()
    def orders():
        """ List orders """
        saxo = Saxo()
        orders = saxo.orders()
        for o in orders["Data"]:
            logger.info(o["BuySell"], o["Uic"], o["Amount"], o["Status"])

    @cli.command()
    @click.option('--orders', required=True, type=str, help='Comma separated list of Order IDs')
    def cancel_orders(orders):
        """ Cancel Orders """
        saxo = Saxo()
        saxo.cancel_order(orders)

    @click.command()
    @click.option('--symbol', required=True, type=str, help='Symbol to trade')
    @click.option('--amount', required=True, type=str, help='Amount to trade')
    @click.option('--buy', default=True, type=bool, help='Buy (default) or Sell (False)')
    @click.option('--points', default=None, type=int, help='Stop Loss points')
    def market(symbol, amount, buy, points):
        """ Execute rades """
        saxo = Saxo()
        order = saxo.market(symbol=symbol, amount=amount, buy=buy, stoploss_points=points)
        logger.info(order)

    @cli.command()
    @click.option('--symbol', required=True, type=str, help='Symbol to trade')
    @click.option('--amount', required=True, type=str, help='Amount to trade')
    @click.option('--price', required=True, type=int, help='Limit price')
    @click.option('--buy', default=True, type=bool, help='Buy (default) or Sell (False)')
    @click.option('--stoploss_price', default=None, type=int, help='Stop Loss price')
    @click.option('--points', default=None, type=int, help='Stop Loss points')
    def limit(symbol, amount, buy, price, stoploss_price, points):
        """ Execute rades """
        saxo = Saxo()
        order = saxo.limit(symbol=symbol,
            amount=amount,
            limit=price, 
            buy=buy,
            stoploss_price=stoploss_price,
            stoploss_points=points)
        logger.info(order)

    @cli.command()
    @click.option('--signal', default=None, type=str, help='Trade signal (e.g. SPX_TRADE_LONG_IN_3609_SL_10)')
    @click.option('--tweet', default=None, type=str, help='Execute trades for a specific tweet id')
    @click.pass_context
    def trade(ctx, signal, tweet):
        """ Execute trades based on a signal or tweet id """
        # No input provided
        if ctx.args == []:
            print(trade.get_help(ctx))

        saxo = Saxo()
        # If signal is provided
        if signal is not None:
            saxo.trade(signal=signal)

        # If tweet is provided
        elif tweet is not None:
            tdb = TweetsDB(config)
            doc = tdb.get_tweet(tweet)
            for signal in doc["signals"]:
                saxo.trade(signal=signal)
        
        else:
            logger.error("Something is not right..")

    @cli.command()
    def watch():
        """
            Watch for alerts and execute trades
        """
        while True:
            try:
                saxo = Saxo()
                saxo.watch()
            except Exception as e:
                p = Prowl(API_KEY=config["PROWL_API_KEY"])
                p.send("cli_saxo.py watch crashed!! Restarting..")
                logger.error(e, exc_info=True)

    cli.add_command(report_closed_positions)
    cli.add_command(positions)
    cli.add_command(close_position)
    cli.add_command(market)
    cli.add_command(limit)
    cli.add_command(orders)
    cli.add_command(trade)
    cli.add_command(watch)
    cli()
