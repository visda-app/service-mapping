from dogpile.cache import make_region
from uuid import uuid4

from configs.app import Cache as cache_configs
from lib.logger import logger


# https://dogpilecache.sqlalchemy.org/en/latest/api.html#redis-backends
cache_region = make_region().configure(
    'dogpile.cache.redis',
    arguments = {
        'host': cache_configs.host,
        'port': cache_configs.port,
        'db': 0,
        'redis_expiration_time': 60*60*10,   # 10 hours
        'distributed_lock': True,
        'thread_local_lock': False
    }
)

def test_cache():
    key = str(uuid4())
    val = key[:5]
    cache_region.set(key, val)
    res = cache_region.get(key)
    if res != val:
        raise Exception('Cache verification failed.')
    cache_region.delete(key)
    logger.debug("Cache seems to be working fine...")

test_cache()