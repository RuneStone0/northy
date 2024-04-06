import click
import logging
from northy.logger import setup_logger
from northy.secrets_manager import SecretsManager

if __name__ == '__main__':
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

    cli.add_command(secrets)
    cli()