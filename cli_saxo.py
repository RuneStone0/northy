import os
import click
import inspect
import logging
from northy.prowl import Prowl
from northy.logger import setup_logger
from northy.saxo import Saxo, SaxoHelper
from northy.saxo_report import SaxoReport
from northy.config import Config
config = Config().config

setup_logger(filename='saxo.log')
logger = logging.getLogger(__name__)

@click.group()
@click.option('--prod', default=False, is_flag=True, type=bool, help='Enable production mode')
@click.option('--profile', required=False, default="default", type=str, help='Set Saxo Profile')
@click.pass_context
def cli(ctx, prod, profile):
    ctx.ensure_object(dict)
    profile = profile.lower() # TODO: Currently not impelemented
    os.environ["PRODUCTION"] = str(prod)

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
    """ Execute Trades """
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
@click.pass_context
@click.option('--list', required=False, is_flag=True, default=False, 
                type=bool, help='List all accounts')
@click.option('--rename', default=None, required=False, type=str, help='AccountKey to modify')
@click.option('--name', default=None, required=False, type=str, help='New Account Display Name')
def accounts(ctx, list, rename, name):
    """ List accounts """
    saxo = ctx.obj['SAXO']

    # List accounts
    if list:
        accounts = saxo.accounts()
        for acc in accounts["Data"]:
            displayName = acc["DisplayName"] if "DisplayName" in acc else ""
            accId = acc["AccountId"]
            accKey = acc["AccountKey"]
            accCurrency = acc["Currency"]
            accountName = displayName if len(displayName)>0 else accId
            out = f"{accCurrency} {accKey} {accountName}"
            logger.info(out)

    # Rename account
    elif rename:
        # Check if name is provided
        if not name:
            logger.error("--name is required to rename account")
            return
        
        # Update account name
        update = saxo.account_update(AccountKey=rename, DisplayName=name)
        logger.info("Updating account (%s) display name to '%s'" % (rename, name))
        logger.info(update)

    # Show help
    else:
        click.echo(ctx.get_help())

@cli.command()
@click.option('--signal', default=None, type=str, help='Trade signal (e.g. SPX_TRADE_LONG_IN_3609_SL_10)')
@click.option('--tweet', default=None, type=str, help='Execute trades for a specific tweet id')
def trade(signal, tweet):
    """ Execute trades based on a signal or tweet id """
    saxo = Saxo()

    # If signal is provided
    if signal is not None:
        saxo.trade(signal=signal)

    # If tweet is provided
    elif tweet is not None:
        from northy.db import Database
        db = Database()
        for doc in db.find({"tid": tweet}):
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
            p = Prowl()
            p.send(f"cli_saxo.py watch crashed \n{e}\nRestarting..")
            logger.error(e, exc_info=True)


if __name__ == '__main__':
    # Automatically add all commands to the group
    for name, obj in globals().copy().items():
        if inspect.isfunction(obj) and obj.__module__ == __name__:
            cli.add_command(obj)
    
    # Run the CLI
    cli()
