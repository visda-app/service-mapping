from functools import wraps
import flask_restful
from flask import request

from lib.logger import logger


def _request_call_logger(f):
    """
    Logs the API call
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        user_id = None
        if hasattr(request, 'user'):
            user_id = request.user.user_id
        logger.info(
            f"{request.method} {request.full_path} args={args} kwargs={kwargs} user_id={user_id}"  # noqa
        )
        # Catch all the exceptions and log them
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.exception(e)
            raise
    return wrapper


class Resource(flask_restful.Resource):
    method_decorators = [
            _request_call_logger,
    ]
