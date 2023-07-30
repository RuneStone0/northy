import click
#from northy.config import config
from northy.logger_config import setup_logger
from northy.saxo import Saxo #, Trading, Helper
import json

def get_config():
    file_path = "saxo_config.json"
    with open(file_path, "r") as file:
        config = json.load(file)
    return config

if __name__ == '__main__':
    setup_logger()
    config = get_config()
    saxo = Saxo(config=config)

    @click.group()
    def cli():
        pass

    @click.command()
    def positions():
        positions = saxo.positions()
        print(positions)

    @click.command()
    def orders():
        orders = saxo.orders()
        for o in orders["Data"]:
            print(o["BuySell"], o["Uic"], o["Amount"], o["Status"])

    cli.add_command(positions)
    cli.add_command(orders)
    cli()
