# import django
import datetime
import logging

import json_log_formatter
import ujson

logging.addLevelName(logging.CRITICAL, "FATAL")


class CustomizedJSONFormatter(json_log_formatter.JSONFormatter):
    json_lib = ujson

    def json_record(self, message, extra, record):
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
    def __init__(self):
        super().__init__()
        self.counter = 0

    def format(self, record):
        self.counter += 1
        timestamp = datetime.datetime.fromtimestamp(record.created).isoformat()
        msg = f"Log #{self.counter} - {record.levelname} - {timestamp} - {record.getMessage()}\n"
        return msg
