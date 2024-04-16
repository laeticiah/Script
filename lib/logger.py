import logging

def setup_logger(name=__name__, log_level=logging.INFO):
    """
    Initialize global logger and return a logging instance

    Args:
        name: The name of the logger, default __name__ (the name of the module where this is called)
        log_level: The level of logs to handle. Default log level is INFO.
    """

    # Create a custom logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler('logs.log')

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger