import time
import click
import logging
from datetime import datetime
from northy.logger import setup_logger
from northy.saxo import Saxo
from northy.config import config, set_env
from northy.tweets import TweetsDB
from northy.email import Email

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
    def report_closed_positions():
        """ Report Closed Positions """
        # Set environment variables
        set_env()

        def generate_report():
            positions = saxo.positions(status_open=False, profit_only=False)

            # Report values
            total_profit_loss = 0
            trades_profit_loss = []
            count_closed_trades = 0

            # Loop over all positions
            for p in positions["Data"]:
                # Extract values
                base = p["PositionBase"]
                uic = base["Uic"]
                amount = base["Amount"]
                status = base["Status"]
                ProfitLossOnTrade = p["PositionView"]["ProfitLossOnTrade"]

                # only report closed positions
                if status == "Closed":
                    # filter away the parent positions
                    if "CorrelationTypes" not in base.keys():
                        logger.info(f"Uic:{uic} Amount:{amount} P&L:{ProfitLossOnTrade}")
                        total_profit_loss += ProfitLossOnTrade
                        trades_profit_loss.append(ProfitLossOnTrade)
                        count_closed_trades += 1

            # Convert "2023-07-31T00:00:00.000000Z" to "2023-07-31"
            date = positions["Data"][0]["PositionBase"]["ValueDate"].split("T")[0]

            avg_profit_loss = total_profit_loss / count_closed_trades
            sheet = ",".join(map(str, trades_profit_loss))
            summary = """
            <p>Trading Date: %s</p>
            <p>Total Profit/Loss: %s</p>
            <p>Total Number of Trades: %s</p>
            <p>Average P&L/Trade: %s</p>
            <p>Sheet: %s</p>
            """ % (date, total_profit_loss, count_closed_trades, avg_profit_loss, sheet)
            
            return {
                "summary": summary,
                "total_profit_loss": total_profit_loss,
                "count_closed_trades": count_closed_trades,
                "trades_profit_loss": trades_profit_loss,
                "date": date
            }

        # Loop Controller
        def loop_controller(skip=False):
            if datetime.now().weekday() < 5 and datetime.now().hour == 17 or skip:
                # Generate report for all positions
                report = generate_report()

                # Send report to Email
                email = Email()
                # TODO: remove hardcoded email
                email.send(to_email="rtk@rtk-cv.dk",
                        subject=f"Trading Report {report['date']}",
                        content=report["summary"])
                
                # Sleep for 1 hour
                logger.info("Sleeping for 1 hour")
                time.sleep(3600)

            else:
                # sleep until next full hour
                now = datetime.now()
                next_hour = now.replace(hour=(now.hour + 1) % 24, minute=0, second=0, microsecond=0)
                sleep_time = (next_hour - now).seconds
                if sleep_time == 0: sleep_time = 1
                logger.info(f"Sleeping for {sleep_time} seconds")
                time.sleep(sleep_time)

        while True:
            loop_controller()
        
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

    cli.add_command(report_closed_positions)
    cli.add_command(positions)
    cli.add_command(market)
    cli.add_command(limit)
    cli.add_command(orders)
    cli.add_command(trade)
    cli.add_command(watch)
    cli()
