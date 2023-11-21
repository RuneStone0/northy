import time
import logging
from zoneinfo import ZoneInfo
from northy.email import Email
from datetime import datetime, timedelta

class SaxoReport:
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def __positions_to_report_data(self, positions) -> dict:
        """
            Parse data from positions object and generate a report data as dict.

            Args:
                positions (dict): Positions object

            Returns:
                dict: Report

            Example:
                >>> report = saxo.generate_closed_positions_report(positions)
                >>> print(report)
                >>> {
                >>>     "summary": "...",
                >>>     "date": "2023-07-31",
                >>>     "total_profit_loss": 725,
                >>>     "trades_profit_loss": "100,-12,678,-41",
                >>>     "count_closed_trades": 4
                >>> }
        """
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
                    self.logger.info(f"Uic:{uic} Amount:{amount} P&L:{ProfitLossOnTrade}")
                    total_profit_loss += ProfitLossOnTrade
                    trades_profit_loss.append(ProfitLossOnTrade)
                    count_closed_trades += 1

        # Convert "2023-07-31T00:00:00.000000Z" to "2023-07-31"
        date = positions["Data"][0]["PositionBase"]["ValueDate"].split("T")[0]

        # Handle cases where no closed positions were found
        try:
            avg_profit_loss = total_profit_loss / count_closed_trades
        except ZeroDivisionError:
            avg_profit_loss = "N/A"
        
        return {
            "total_profit_loss": total_profit_loss,
            "count_closed_trades": count_closed_trades,
            "trades_profit_loss": trades_profit_loss,
            "avg_profit_loss": avg_profit_loss,
            "date": date
        }

    def send_report(self, positions):
        """
            Generate a report of closed positions and send it via email.

            Args:
                positions (dict): Positions object
        """
        # Generate report data
        report = self.__positions_to_report_data(positions)

        # Create summary
        sheet = ",".join(map(str, report["trades_profit_loss"]))
        summary = """
        <p>Trading Date: %s</p>
        <p>Total Profit/Loss: %s</p>
        <p>Total Number of Trades: %s</p>
        <p>Average P&L/Trade: %s</p>
        <p>Sheet: %s</p>
        """ % (report["date"],
                report["total_profit_loss"],
                report["count_closed_trades"],
                report["avg_profit_loss"],
                sheet)

        # Send report to Email
        # TODO: remove hardcoded email
        email = Email()
        email.send(
                to="rtk@rtk-cv.dk",
                subject=f"Trading Report {report['date']}",
                content=summary)

    def close_report_sleep(self, hours=17, minutes=0, seconds=0):
        """
            Sleep until specified time on the next weekday.
        """
        now = datetime.now(ZoneInfo('US/Central'))
        if now.weekday() >= 5:  # If it's weekend
            self.logger.info("Its weekend. Sleeping until Monday at 17:00")
            days_till_monday = 7 - now.weekday()
            next_time = (now + timedelta(days=days_till_monday)).replace(
                hour=hours, minute=minutes, second=seconds)
        elif now.hour >= hours:  # If it's past the specified hour on a weekday
            self.logger.info("Its past 17:00. Sleeping until tomorrow at 17:00")
            next_time = (now + timedelta(days=1)).replace(
                hour=hours, minute=minutes, second=seconds)
        else:  # If it's before the specified hour on a weekday
            self.logger.info("Its before 17:00. Sleeping until 17:00")
            next_time = now.replace(hour=hours, minute=minutes, second=seconds)
        sleep_time = (next_time - now).total_seconds()
        self.logger.info(f"Sleeping for {sleep_time} seconds until {next_time}")
        time.sleep(sleep_time)
