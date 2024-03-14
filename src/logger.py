import logging
from colorlog import ColoredFormatter
from logging.handlers import TimedRotatingFileHandler
import os

class CustomLogger:
    """
    A custom logger class that configures log formatting, filtering based on the log level,
    and supports log file saving with rotation.
    """
    def __init__(self, save_to_disk: bool = False, log_file_path: str = 'app.log'):
        """
        Initializes the CustomLogger instance with optional disk saving.

        Args:
            save_to_disk (bool, optional): Flag to save logs to disk. Defaults to False.
            log_file_path (str, optional): The file path for saving logs. Defaults to 'app.log'.
        """
        self.save_to_disk = save_to_disk
        self.log_file_path = log_file_path

    @staticmethod
    def get_formatter() -> ColoredFormatter:
        """
        Defines and returns a ColoredFormatter with custom format and colors.

        Returns:
            ColoredFormatter: The configured log formatter.
        """
        log_format = (
            "%(asctime)s - "
            "%(log_color)s"
            "[%(levelname)s]"
            "%(reset)s - "
            "%(dynamic_part)s"
            "%(message_log_color)s"
            "%(message)s"
        )
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

    @classmethod
    def setup_logger(cls, name: str = None, level: int = logging.DEBUG, save_to_disk: bool = False, log_dir: str = 'logs') -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(level)
        logger.propagate = False
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(cls.get_formatter())
        stream_handler.addFilter(cls.ContextFilter())
        logger.addHandler(stream_handler)

        if save_to_disk:
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            file_handler = TimedRotatingFileHandler(
                filename=os.path.join(log_dir, 'app.log'),
                when='D',  # Rotate daily
                interval=1,
                backupCount=7  # Keep logs for 7 days
            )
            file_format = logging.Formatter('%(asctime)s - [%(levelname)s] - %(dynamic_part)s%(message)s')
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)

        return logger

    class ContextFilter(logging.Filter):
        """
        A logging filter that dynamically adds file and line number information to DEBUG and ERROR logs.
        """
        def filter(self, record: logging.LogRecord) -> bool:
            if record.levelno in [logging.DEBUG, logging.ERROR]:
                record.dynamic_part = f"file:{record.filename}:line:{record.lineno} - "
            else:
                record.dynamic_part = ""
            return True

# Example usage
if __name__ == "__main__":
    logger = CustomLogger.setup_logger(__name__, save_to_disk=True, log_dir='./')
    logger.debug("This debug message includes the file and line number.")
    logger.info("This info message does not include the file and line number.")
    logger.warning("This is a warning message.")
    logger.error("This is an error message.")
    logger.critical("This is a critical message.")