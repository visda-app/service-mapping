import time
import functools
from lib.logger import logger
import importlib
from uuid import uuid4


def timerD(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        logger.info(f"func={func}, elapsed_time={elapsed_time}")
        return result
    return wrapper


def text_tip(s):
    "Return a shortened version of the text"
    if type(s) == bytes:
        s = s.decode()
    if len(s) > 50:
        return s[:20] + " ... " + s[-15:]
    else:
        return s


def _get_module_from_string(module_path):
    return importlib.import_module(module_path)


def get_module_and_class_from_string(class_path):
    class_name = class_path.split('.')[-1]
    class_path = '.'.join(class_path.split('.')[:-1])
    module = _get_module_from_string(class_path)
    return module, class_name


def generate_random_job_id():
    return str(uuid4())
