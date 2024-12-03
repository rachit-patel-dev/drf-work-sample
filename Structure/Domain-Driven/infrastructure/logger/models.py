import logging


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
