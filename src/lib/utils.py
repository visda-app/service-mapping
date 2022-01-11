import time
import functools
from lib.logger import logger
import importlib
from uuid import uuid4
from urllib.parse import urlparse, parse_qs


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


def get_class_from_string(class_path_string):
    module, class_name = get_module_and_class_from_string(class_path_string)
    python_class = getattr(module, class_name)
    return python_class


def generate_random_id():
    return str(uuid4())


def get_youtube_video_id(url):
    """
    code adopted from here: https://gist.github.com/kmonsoor/2a1afba4ee127cce50a0
    and here: https://stackoverflow.com/questions/4356538/how-can-i-extract-video-id-from-youtubes-link-in-python
    
    Returns Video_ID extracting from the given url of Youtube
    
    Examples of URLs:
      Valid:
        'http://youtu.be/_lOT2p_FCvA',
        'www.youtube.com/watch?v=_lOT2p_FCvA&feature=feedu',
        'http://www.youtube.com/embed/_lOT2p_FCvA',
        'http://www.youtube.com/v/_lOT2p_FCvA?version=3&amp;hl=en_US',
        'https://www.youtube.com/watch?v=rTHlyTphWP0&index=6&list=PLjeDyYvG6-40qawYNR4juzvSOg-ezZ2a6',
        'youtube.com/watch?v=_lOT2p_FCvA',
      
      Invalid:
        'youtu.be/watch?v=_lOT2p_FCvA',
    """
    query = urlparse(url)

    if query.hostname:
        netloc = query.hostname
    elif query.path:
        netloc = query.path
    else:
        netloc = None

    if 'youtube' in netloc:
        if (
            query.path in {'/watch', '/ytscreeningroom', '/'} 
            or any([e in query.path for e in {'/watch', '/ytscreeningroom'}])
        ):
            return (
                parse_qs(query.query).get('v', [None])[0] 
                or parse_qs(query.query).get('vi', [None])[0]
            )
        elif query.path.startswith(('/embed/', '/v/', '/vi/', '/e/')):
            res = query.path.split('/')[2]
            if res.find('&') > 0:
                return res[:res.find('&')]
            return res
        # elif query.path.startswith('/attribution_link'):
        #     return query.query.find('v%3D')
    elif 'youtu.be' in netloc:
        if query.path.find('&') > 0:
            return query.path[1:query.path.find('&')]
        return query.path[1:]
