#
# Part of this file is from <https://github.com/madzak/python-json-logger>.
#

import logging
import logging.handlers
import re

from datetime import datetime

try:
    import json
except ImportError, e:
    import simplejson as json


class JsonFormatter(logging.Formatter):

    """A custom formatter to format logging records as json objects"""

    def parse(self):
        standard_formatters = re.compile(r'\((.*?)\)', re.IGNORECASE)
        return standard_formatters.findall(self._fmt)

    def format(self, record):
        """Formats a log record and serializes to json"""
        mappings = {
            'asctime': create_timestamp,
            'message': lambda r: r.msg,
        }

        formatters = self.parse()

        log_record = {}
        for formatter in formatters:
            try:
                log_record[formatter] = mappings[formatter](record)
            except KeyError:
                log_record[formatter] = record.__dict__[formatter]

        return json.dumps(log_record, True)


def create_timestamp(record):
    """Creates a human readable timestamp for a log records created date"""

    timestamp = datetime.fromtimestamp(record.created)
    return timestamp.strftime("%y-%m-%d %H:%M:%S,%f"),


def setup_logger(name, enable_syslog=True, use_json=False):
    if use_json:
        supported_keys = [
            'asctime',
            'created',
            'filename',
            'funcName',
            'levelname',
            'levelno',
            'lineno',
            'module',
            'msecs',
            'message',
            'name',
            'pathname',
            'process',
            'processName',
            'relativeCreated',
            'thread',
            'threadName'
        ]

        log_format = ' '.join(['%({})'] * len(supported_keys))
        custom_format = log_format.format(*supported_keys)

        formatter = JsonFormatter(custom_format)
    else:
        formatter = logging.Formatter(
            fmt='HYPNOLOG %(asctime)s - %(levelname)s - %(module)s - %(message)s')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

    if enable_syslog:
        syslog_handler = logging.handlers.SysLogHandler(address='/dev/log')
        logger.addHandler(syslog_handler)

    return logger
