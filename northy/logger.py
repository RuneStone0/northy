import logging
from colorama import Fore, Style, init
from northy.config import config
init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    """
        Color Options:
            Black: Fore.BLACK
            Red: Fore.RED
            Green: Fore.GREEN
            Yellow: Fore.YELLOW
            Blue: Fore.BLUE
            Magenta: Fore.MAGENTA
            Cyan: Fore.CYAN
            White: Fore.WHITE
    """
    COLORS = {
        'DEFAULT': Style.RESET_ALL,       # Reset to default color
        'GREEN': Fore.GREEN,        # Green color for asctime
        'YELLOW': Fore.YELLOW,       # Yellow color for warning level
        'RED': Fore.RED,          # Red color for error and critical levels
        'CYAN': Fore.CYAN,         # Cyan color for debug level
        'MAGENTA': Fore.MAGENTA,
    }

    LEVEL_COLORS = {
        'DEBUG': COLORS['MAGENTA'],        # Default color for DEBUG level
        'INFO': Fore.BLUE,                 # Default color for INFO level
        'WARNING': COLORS['YELLOW'],       # Yellow color for WARNING level
        'ERROR': COLORS['RED'],            # Red color for ERROR level
        'CRITICAL': COLORS['RED'],         # Red color for CRITICAL level
    }

    def format(self, record):
        log_level = record.levelname
        log_msg = super().format(record)

        if log_level == 'WARNING':
            log_msg = self.COLORS['YELLOW'] + log_msg + self.COLORS['DEFAULT']
        elif log_level in ('ERROR', 'CRITICAL'):
            log_msg = self.COLORS['RED'] + log_msg + self.COLORS['DEFAULT']

        # Replace asctime with colored asctime
        formatted_time = record.asctime.split(",")[0]
        log_msg = log_msg.replace(record.asctime, self.COLORS['GREEN'] + formatted_time + self.COLORS['DEFAULT'])

        # Apply custom color to levelname
        log_msg = log_msg.replace(record.levelname, self.LEVEL_COLORS[log_level] + record.levelname + self.COLORS['DEFAULT'])

        return log_msg

def setup_logger():
    # Configure the root logger
    logging.basicConfig(
        level=config["LOG_LEVEL"],
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='northy.log',
        filemode='a',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Add a console handler for printing logs to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(config["LOG_LEVEL"])
    console_formatter = ColoredFormatter('%(asctime)s %(levelname)s %(message)s')
    console_handler.setFormatter(console_formatter)
    logging.getLogger('').addHandler(console_handler)
