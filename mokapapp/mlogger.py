"""mlogger.py

Application logging for mokapapp.
"""

import logging
from logging.config import dictConfig

def log_setup(logfile=None, syslog='/dev/log'):
    """Setup application logging using python's standard library logging module
    
    Args:
        logfile (str): The name of the output logfile written to by the file handler
        syslog (str): Target for the system log handler. Set to Linux OS default.
    """
    # Define the default log output locations as defined in the logging_config dictionary below.
    root_handlers = ['stream_handler', 'syslog_handler']
    handlers = {
        'stream_handler': {'class': 'logging.StreamHandler', 'formatter': 'log_formatter', 'level': logging.DEBUG},
        'syslog_handler': {'class': 'logging.handlers.SysLogHandler', 'formatter': 'log_formatter', 'level': logging.DEBUG, 'address': syslog}
    }
    # If a logfile path is passed, add a file handler to the handlers list.
    if logfile:
        handlers['file_handler'] = {'class': 'logging.FileHandler', 'formatter': 'log_formatter', 'level': 'DEBUG', 'filename': logfile, 'mode':'w'}
        root_handlers.append('file_handler')

    logging_config = dict(
        version=1.0,
        formatters={'log_formatter': {'format': "{asctime} {name}.{module}: {levelname} - {message}",
            'style': '{', 'datefmt': r'%Y-%m-%d %H:%M:%S'}},
        handlers=handlers,
        root={'handlers': root_handlers, 'level': logging.DEBUG}
    )
    dictConfig(logging_config)


if __name__ == '__main__':
    log_setup()
    log = logging.getLogger('TEST')
    log.info('TEST')