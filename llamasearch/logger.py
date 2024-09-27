import logging
from colorlog import ColoredFormatter
from logging.handlers import TimedRotatingFileHandler
import os
from llamasearch.settings import config

# Define custom VERBOSE level
VERBOSE = 15
logging.addLevelName(VERBOSE, "VERBOSE")

class CustomLogger:
    """
    A custom logger class that configures log formatting, filtering based on the log level,
    and supports log file saving with rotation.
    """
    def __init__(self):
        logging.Logger.verbose = verbose

    @staticmethod
    def get_formatter(verbose=False) -> ColoredFormatter:
        """
        Defines and returns a ColoredFormatter with custom format and colors.
        """
        log_format = "%(asctime)s - %(log_color)s[%(levelname)s]%(reset)s - "
        if verbose:
            log_format += "%(filename)s:%(lineno)d - "
        log_format += "%(message_log_color)s%(message)s"
        log_colors = {
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
        message_log_colors = {
            'DEBUG': 'cyan',
            'INFO': 'white',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
        return ColoredFormatter(log_format, log_colors=log_colors, secondary_log_colors={'message': message_log_colors}, reset=True)

    def verbose(self, message, *args, **kwargs):
        if self.isEnabledFor(VERBOSE):
            self._log(VERBOSE, message, args, **kwargs)

    @classmethod
    def setup_logger(cls, name=None, level=None, save_to_disk=False, log_dir='./logs', log_name='app.log'):
        log_level_ = os.getenv('LOGLEVEL', 'INFO').upper()
        verbose = os.getenv('VERBOSE', 'false').lower() == 'true'
        debug = os.getenv('DEBUG', 'false').lower() == 'true'

        if debug:
            level = logging.DEBUG
        elif verbose:
            level = VERBOSE
        else:
            level = getattr(logging, log_level_, logging.INFO)

        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = False

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(CustomLogger.get_formatter(verbose))  # Use CustomLogger explicitly
        logger.addHandler(stream_handler)

        if save_to_disk:
            os.makedirs(log_dir, exist_ok=True)
            file_handler = TimedRotatingFileHandler(
                filename=os.path.join(log_dir, log_name),
                when='midnight',
                interval=1,
                backupCount=30
            )
            file_format = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s')
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)

        return logger


    class ContextFilter(logging.Filter):
        """
        A logging filter that dynamically adds file and line number information to certain logs.
        """
        def filter(self, record: logging.LogRecord) -> bool:
            # Adding filename and line number for DEBUG, ERROR, and WARNING levels
            if record.levelno in [logging.DEBUG, logging.ERROR, logging.WARNING]:
                record.dynamic_part = f"{record.filename}:line:{record.lineno} - "
            else:
                record.dynamic_part = ""
            return True

logger = CustomLogger.setup_logger("app_logger", save_to_disk=True, log_dir=config.application.get_log_dir(), log_name='app.log')

# Example usage
if __name__ == "__main__":
    logger = CustomLogger.setup_logger(__name__, save_to_disk=True, log_dir='./logs', log_name='app.log')
    logger.debug("This debug message includes the file and line number.")
    logger.info("This info message does not include the file and line number.")
    logger.warning("This is a warning message.")
    logger.error("This error message includes the file and line number.")
    logger.critical("This critical message includes the file and line number.")