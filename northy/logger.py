import logging

class ColoredFormatter(logging.Formatter):
    """
        Color Options:
            Black: \033[30m
            Red: \033[31m
            Green: \033[32m
            Yellow: \033[33m
            Blue: \033[34m
            Magenta: \033[35m
            Cyan: \033[36m
            White: \033[37m
    """
    COLORS = {
        'DEFAULT': '\033[0m',       # Reset to default color
        'GREEN': '\033[32m',        # Green color for asctime
        'YELLOW': '\033[33m',       # Yellow color for warning level
        'RED': '\033[31m',          # Red color for error and critical levels
    }

    LEVEL_COLORS = {
        'DEBUG': COLORS['DEFAULT'],        # Default color for DEBUG level
        'INFO': '\033[36m',                 # Default color for INFO level
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
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s',
        filename='northy.log',
        filemode='a',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Add a console handler for printing logs to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = ColoredFormatter('%(asctime)s %(levelname)s %(message)s')
    console_handler.setFormatter(console_formatter)
    logging.getLogger('').addHandler(console_handler)
