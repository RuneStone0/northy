import os
import click
import inspect
import sqlite3
import logging
from northy.noc import Noc
from northy.logger import setup_logger

setup_logger(filename='noc.log')
logger = logging.getLogger(__name__)

@click.group()
@click.option('--prod', default=False, is_flag=True, type=bool, help='Enable production mode')
def cli(prod):
    # set environment variable
    os.environ["PRODUCTION"] = str(prod)
    pass

@cli.command()
@click.option('--path', required=False, default=None, type=str, help='Path to wpndatabase')
def watch(path):
    """
    Watch for notifications and insert into DB
    """
    noc = Noc(wpndatabase_path=path)
    noc.watch()

@cli.command()
@click.option('--path', required=False, default=None, type=str, help='Path to wpndatabase')
def read(path):
    """
    Read notifications from DB (used for debugging)
    """
    database_path = path
    if database_path is None:
        database_path = 'AppData\\Local\\Microsoft\\Windows\\Notifications\\wpndatabase.db'
        database_path = os.path.join(os.getenv('USERPROFILE'), database_path)

    logger.info("Reading from %s" % database_path)
    
    def list_tables(database_path):
        # Connect to the SQLite database
        connection = sqlite3.connect(database_path)
        cursor = connection.cursor()

        # Use the cursor to execute a query to retrieve table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        # Print or process the table names
        for table in tables:
            print(table[0])

        # Close the connection
        connection.close()

    def read_data_from_db(database_path):
        # Connect to the SQLite database (this will also handle the WAL file)
        connection = sqlite3.connect(database_path)
        cursor = connection.cursor()

        # Execute a query to retrieve data
        cursor.execute("SELECT * FROM Notification")
        rows = cursor.fetchall()

        # Print or process the retrieved data
        for row in rows:
            print(row)

        # Close the connection
        connection.close()

    # Replace 'your_database.db' with the path to your SQLite database file
    list_tables(database_path)
    read_data_from_db(database_path)

@cli.command()
@click.option('--path', required=False, default=None, type=str, help='Path to wpndatabase')
def process(path):
    """
    Process notifications from DB
    """
    from northy.db import Database
    db = Database()
    noc = Noc(wpndatabase_path=path)
    noc.process_notification(db=db)

if __name__ == '__main__':
    # Automatically add all commands to the group
    for name, obj in globals().copy().items():
        if inspect.isfunction(obj) and obj.__module__ == __name__:
            cli.add_command(obj)
    
    cli()