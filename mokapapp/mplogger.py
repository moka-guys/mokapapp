"""mlogger.py

Application logging for mokapapp.
"""

import logging
import pathlib
from datetime import datetime
from logging.config import dictConfig


def setup(logdir, syslog='/dev/log'):
    """Setup logging to stderr, syslog and logfile.

    Args:
        logdir(str): A directory in which to write logfiles to in the format 'YYMMDD_mokapapp.log'
        syslog(str): Path to sys log. Set to linux default.
    """
    if not pathlib.Path(logdir).is_dir():
        raise IOError('Logdir argument is not a valid directory')

    logfilepath = pathlib.Path(logdir, datetime.now().strftime("%y%m%d") + "_mokapapp.log")

    logging_config = dict(
        version=1.0,
        formatters={
            'log_formatter': {
                'format': "{asctime} {name}.{module}: {levelname} - {message}",
                'style': '{',
                'datefmt': r'%Y-%m-%d %H:%M:%S'
            }
        },
        handlers={
            'stream_handler': {'class': 'logging.StreamHandler', 'formatter': 'log_formatter', 'level': logging.DEBUG},
            'syslog_handler': {'class': 'logging.handlers.SysLogHandler', 'formatter': 'log_formatter', 'level': logging.DEBUG, 'address': syslog},
            'file_handler' : {'class': 'logging.FileHandler', 'formatter': 'log_formatter', 'level': logging.DEBUG, 'filename': logfilepath, 'mode':'w'}
        },
        root={'handlers': ['stream_handler', 'syslog_handler', 'file_handler'], 'level': logging.DEBUG}
    )
    dictConfig(logging_config)