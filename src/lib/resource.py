def log_exception(sender, exception, **extra):
    """ Log an exception to our logging framework """
    sender.logger.exception(exception)
