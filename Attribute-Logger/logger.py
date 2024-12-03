# in settings.py
LOGGER_HANDLERS = os.getenv(
    "LOGGER_HANDLERS",
    [
        "debug_file",
        "info_file",
        "warn_file",
        "error_file",
    ],
).split(",")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": CustomizedJSONFormatter,
        },
        "app": {
            "()": ExtraFormatter,
            "format": 'level: "%(levelname)s"\t msg: "%(message)s"\t logger: "%(name)s"\t func: "%(funcName)s"\t time: "%(asctime)s"',
            "datefmt": "%Y-%m-%dT%H:%M:%S.%z",
            "extra_fmt": "\t extra: %s",
        },
        "simple_string": {
            "format": "%(levelname)s %(asctime)s %(message)s\n",
            "datefmt": "%Y-%m-%dT%H:%M:%S.%z",
        },
        "custom_format_with_counter": {
            "()": CounterLogFormatter,
        },
    },
    "handlers": {
        "debug_file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": f"logs/debug/{date.today()}_logger.log",
            "formatter": "json",
        },
        "info_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": f"logs/info/{date.today()}_info.log",
            "formatter": "json",
        },
        "warn_file": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": f"logs/warning/{date.today()}_warn.log",
            "formatter": "json",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.FileHandler",
            "filename": f"logs/error/{date.today()}_error.log",
            "formatter": "json",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "db_query_file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "formatter": "custom_format_with_counter",
            "filename": f"logs/db_query/{date.today()}_debug.log",
        },
    },
    "loggers": {
        "": {
            "handlers": LOGGER_HANDLERS,
            "level": "DEBUG",
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["db_query_file"],
            "level": "DEBUG",
            "propagate": False,
        },
    },
}

# Formatting services


class CustomizedJSONFormatter(json_log_formatter.JSONFormatter):
    """
    A class that represents a customized JSON log formatter.

    Attributes:
        json_lib (module): The JSON library to use for formatting the log record into JSON format.

    Methods:
        json_record(message, extra, record):
            Formats the log record into a JSON format.

            Parameters:
                message (str): The log message.
                extra (dict): A dictionary containing extra information to be included in the log record.
                record (logging.LogRecord): The log record object.

            Returns:
                dict: The formatted log record in JSON format.

            Notes:
                - The method adds the following fields to the 'extra' dictionary:
                    - 'level': The log level name.
                    - 'msg': The log message.
                    - 'logger': The logger name.
                    - 'func': The name of the function where the log record originated.
                    - 'time': The current timestamp in ISO format.
                - If the 'request' key is present in the 'extra' dictionary, the method extracts the 'X-FORWARD-FOR' value from the 'request.META' dictionary and adds it as 'x_forward_for' field in the 'extra' dictionary.
                - The method then returns the modified 'extra' dictionary as the formatted log record.
    """

    json_lib = ujson

    def json_record(self, message, extra, record):
        """
        This method is responsible for formatting the log record into a JSON format.

        Parameters:
            - message (str): The log message.
            - extra (dict): A dictionary containing extra information to be included in the log record.
            - record (logging.LogRecord): The log record object.

        Returns:
            dict: The formatted log record in JSON format.

        Notes:
            - The method adds the following fields to the 'extra' dictionary:
                - 'level': The log level name.
                - 'msg': The log message.
                - 'logger': The logger name.
                - 'func': The name of the function where the log record originated.
                - 'time': The current timestamp in ISO format.
            - If the 'request' key is present in the 'extra' dictionary, the method extracts the 'X-FORWARD-FOR' value from the 'request.META' dictionary and adds it as 'x_forward_for' field in the 'extra' dictionary.
            - The method then returns the modified 'extra' dictionary as the formatted log record.
        """
        extra["level"] = record.__dict__["levelname"]
        extra["msg"] = message
        extra["logger"] = record.__dict__["name"]
        extra["func"] = record.__dict__["funcName"]
        extra["time"] = datetime.datetime.now().isoformat()

        request = extra.pop("request", None)
        if request:
            extra["x_forward_for"] = request.META.get("X-FORWARD-FOR")
        return extra


# Create a custom log formatter that includes a counter
class CounterLogFormatter(logging.Formatter):
    """
    A class that represents a customized log formatter with a counter.

    Attributes:
        counter (int): The counter for the log records.

    Methods:
        format(record):
            Formats the log record into a specific format.

            Parameters:
                record (logging.LogRecord): The log record object.

            Returns:
                str: The formatted log record.

            Description:
                This method is responsible for formatting the log record into a specific format. It increments the counter by 1, retrieves the timestamp from the log record, and constructs a message string with the log counter, log level, timestamp, and log message. The formatted log record is then returned as a string.

            Example:
                >>> formatter = CounterLogFormatter()
                >>> record = logging.LogRecord(...)
                >>> formatted_record = formatter.format(record)
    """

    def __init__(self):
        super().__init__()
        self.counter = 0

    def format(self, record):
        """
        Formats the log record into a specific format.

        Parameters:
            record (logging.LogRecord): The log record object.

        Returns:
            str: The formatted log record.

        Description:
            This method is responsible for formatting the log record into a specific format. It increments the counter by 1, retrieves the timestamp from the log record, and constructs a message string with the log counter, log level, timestamp, and log message. The formatted log record is then returned as a string.

        Example:
            >>> formatter = CounterLogFormatter()
            >>> record = logging.LogRecord(...)
            >>> formatted_record = formatter.format(record)
        """
        self.counter += 1
        timestamp = datetime.datetime.fromtimestamp(record.created).isoformat()
        msg = f"Log #{self.counter} - {record.levelname} - {timestamp} - {record.getMessage()}\n"
        return msg


import logging

# Main attribute logger


class AttributeLogger(object):
    """
    The AttributeLogger is a logging helper class that stores a set of
    attributes that are automatically inserted as extra params on every log
    call.

    Attributes:
        logger (logging.Logger): The underlying logger instance.
        attributes (dict): A dictionary containing attributes to be included in every log call.
    """

    _instance = None
    attributes: dict = {}

    def __new__(cls, *args, **kwargs):
        """
        Ensure that only one instance of AttributeLogger is created using the Singleton pattern.

        Returns:
            AttributeLogger: The singleton instance of AttributeLogger.
        """
        if not cls._instance:
            cls._instance = super(AttributeLogger, cls).__new__(cls)
        return cls._instance

    def __del__(self):
        print(f"------{self} is being destroyed-----")

    def __init__(self, logger: logging.Logger, **attr):
        """
        Initialize the AttributeLogger with a logger and initial set of attributes.

        Args:
            logger (logging.Logger): The logger to use for logging.
            **attr: Additional attributes to be included in every log call.
        """
        self.logger = logger
        self.attributes = attr

    def info(self, msg: str, *args, **kwargs):
        """
        Log an info message with additional attributes.

        Args:
            msg (str): The log message.
            *args: Variable length argument list.
            **kwargs: Keyword arguments for additional configuration.
        """
        kwargs["extra"] = self.attributes
        kwargs["stacklevel"] = 2
        self.logger.info(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """
        Log an error message with additional attributes.

        Args:
            msg (str): The log message.
            *args: Variable length argument list.
            **kwargs: Keyword arguments for additional configuration.
        """
        kwargs["extra"] = self.attributes
        kwargs["stacklevel"] = 2
        self.logger.error(msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        """
        Log a debug message with additional attributes.

        Args:
            msg (str): The log message.
            *args: Variable length argument list.
            **kwargs: Keyword arguments for additional configuration.
        """
        kwargs["extra"] = self.attributes
        kwargs["stacklevel"] = 2
        self.logger.debug(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """
        Log a warning message with additional attributes.

        Args:
            msg (str): The log message.
            *args: Variable length argument list.
            **kwargs: Keyword arguments for additional configuration.
        """
        kwargs["extra"] = self.attributes
        kwargs["stacklevel"] = 2
        self.logger.warning(msg, *args, **kwargs)

    def fatal(self, msg: str, *args, **kwargs):
        """
        Log a fatal message with additional attributes.

        Args:
            msg (str): The log message.
            *args: Variable length argument list.
            **kwargs: Keyword arguments for additional configuration.
        """
        kwargs["extra"] = self.attributes
        kwargs["stacklevel"] = 2
        self.logger.fatal(msg, *args, **kwargs)

    def with_attributes(self, **kwargs):
        """
        Create a new AttributeLogger with additional attributes.

        Args:
            **kwargs: Additional attributes to be added.

        Returns:
            AttributeLogger: A new instance of AttributeLogger with the updated attributes.
        """
        new_attrs = self.attributes.copy()
        new_attrs.update(kwargs)
        return AttributeLogger(self.logger, **new_attrs)


# use of the AttributeLogger
log = AttributeLogger(logging.getLogger(__name__))
