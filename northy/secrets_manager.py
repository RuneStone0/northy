import os
import logging
from configparser_crypt import ConfigParserCrypt
from configparser_crypt.dict_convert import configparser_to_dict

class SecretsManager:
    def __init__(self) -> None:
        """
        SecretsManager class is used to encrypt and decrypt config files.
        """
        self.logger = logging.getLogger(__name__)
        self.conf = ConfigParserCrypt()

    def __write_file(self, filename, data) -> None:
        """ Write data to a file. """
        with open(filename, 'wb') as f:
            f.write(data)

    def __read_file(self, filename) -> bytes:
        """ Read data from a file. """
        with open(filename, 'rb') as f:
            return f.read()

    def encrypt(self, file_in='conf/secrets.ini', 
              file_out=None,
              aes_key='conf/.key') -> None:
        """
        Encrypt and write a config file.

        Args:
            file_in (str): The path to the unencrypted .ini file.
            file_out (str): The path to save the encrypted .ini file. If None, replace .ini with .encrypted.
            aes_key (str): The path to the AES key file.
        """
        # Check if file_in exists
        if not os.path.exists(file_in):
            raise FileNotFoundError(f"File not found: '{file_in}'")

        # Take 'file_in' and replace .ini with .encrypted
        if file_out is None:
            file_out = file_in.replace('.ini', '.encrypted')

        # Set AES key
        self.conf.aes_key = self.__read_file(aes_key)

        # Read unencrypted .ini file
        self.logger.debug(f"Reading unencrypted data from '{file_in}'..")
        self.conf.read(file_in)

        # Write encrypted config file
        with open(file_out, 'wb') as file:
            self.conf.write_encrypted(file)

        self.logger.debug(f"Saved encrypted data to '{file_out}'")

    def read(self, file = 'conf/secrets.encrypted', 
             aes_key = 'conf/.key') -> ConfigParserCrypt:
        """
        Read and decrypt a config file. 
        
        Args:
            file (str): The path to the encrypted .ini file.
            aes_key (str): The path to the AES key file.

        Returns:
            ConfigParserCrypt: The decrypted config object.
        """
        # Set AES key
        self.logger.debug(f"Reading AES key from '{aes_key}'..")
        self.conf.aes_key = self.__read_file(aes_key)

        # Read encrypted config file
        self.logger.debug(f"Reading encrypted data from '{file}'..")
        self.conf.read_encrypted(file)
        return self.conf

    def generate_key(self, filename='conf/.key') -> None:
        """ Generate a new AES key and save it to a file. """
        self.conf.generate_key()
        self.__write_file(filename=filename, data=self.conf.aes_key)
        self.logger.debug(f"AES key generated and saved to '{filename}'")

    def get_dict(self):
        """ Return the decrypted config as a dictionary. """
        return configparser_to_dict(self.conf)

"""
sm = SecretsManager()
#sm.generate_key()
sm.encrypt(file_in='conf/secrets.ini', file_out='conf/secrets.encrypted', aes_key='.key')
sm.read(file='conf/secrets.encrypted', aes_key='.key')
print(sm.get_dict())
"""