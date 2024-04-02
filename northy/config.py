import logging
import os
from northy.secrets_manager import SecretsManager

# Decrypt secrets once, before loading them into the Config class
sm = SecretsManager()
sm.read()

class Config:
    """
        Config class to hold all the environment variables.
    """
    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.config = {}
        self.set_production()
        self.set_log_level()
        self.set_secrets()
        #self.logger.debug("Config: %s" % self.config)

    def set_production(self):
        """ Set PRODUCTION variable. """
        # Get PRODUCTION from environment
        # If not found, set default value
        production = os.getenv("PRODUCTION", "False")

        # Convert to boolean
        production = self.str2bool(production)

        # Save to config
        self.config["PRODUCTION"] = production

    def set_log_level(self):
        """ Set LOG_LEVEL variable. """
        DEFAULT_LOG_LEVEL = "INFO"
        
        # Get LOG_LEVEL from environment. If not found, set default value.
        LOG_LEVEL = os.getenv("LOG_LEVEL", DEFAULT_LOG_LEVEL)

        # Update environment variable regardless of whether it was found or not
        os.environ["LOG_LEVEL"] = LOG_LEVEL

        # Set LOG_LEVEL in config
        self.config["LOG_LEVEL"] = LOG_LEVEL

    def set_secrets(self):
        """ Set secrets from SecretsManager. """
        self.config.update(sm.get_dict())

    def str2bool(self, value):
        """
            Convert string to boolean.
        """
        v = str(value)
        true_values = ("yes", "true", "t", "1")
        false_values = ("no", "false", "f", "0")
        
        lower_v = v.lower()
        
        if lower_v in true_values:
            return True
        elif lower_v in false_values:
            return False
        else:
            raise ValueError("Invalid boolean string representation.")
