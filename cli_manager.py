import click
import inspect
import logging
from northy.logger import setup_logger
from northy.secrets_manager import SecretsManager

setup_logger(filename='cli_manager.log')
logger = logging.getLogger(__name__)

@click.group()
def cli():
    pass

@cli.command()
@click.option('--keygen', required=False, default=False, is_flag=True, help='Generate new AES key')
@click.option('--encrypt', required=False, default=None, type=str, help='Encrypt file and save as .encrypted')
@click.pass_context
def secrets(ctx, keygen, encrypt):
    sm = SecretsManager()
    if keygen:
        sm.generate_key()
        logger.info("Generated new AES key")
        return

    if encrypt:
        sm.encrypt(file_in=encrypt)
        msg = f"Encrypted {encrypt} --> " + encrypt.replace('.ini', '.encrypted')
        logger.info(msg)
        return

    # No input provided
    print(secrets.get_help(ctx))

if __name__ == '__main__':
    # Automatically add all commands to the group
    for name, obj in globals().copy().items():
        if inspect.isfunction(obj) and obj.__module__ == __name__:
            cli.add_command(obj)
    
    cli()