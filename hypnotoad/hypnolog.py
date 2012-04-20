import logging
import logging.handlers

def setup_logger(name, enable_syslog=True):
    formatter = logging.Formatter(fmt='HT_PANLINKS %(asctime)s - %(levelname)s - %(module)s - %(message)s')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

    if enable_syslog:
        syslog_handler = logging.handlers.SysLogHandler(address='/dev/log')
        logger.addHandler(syslog_handler)

    return logger
