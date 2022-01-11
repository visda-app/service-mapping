from uuid import uuid4
import pytest

from tasks.get_3rd_party_data import Get3rdPartyData
from lib.cache import cache_region


@pytest.fixture
def cache_key():
    key = str(uuid4())
    cache_region.set(key, 50)

    yield key

    cache_region.delete(key)


def test_get_3rd_party_data_execute(cache_key):
    ## Better Bachelor:
        # 'video_id': 'oieNTzEeeX0',
    kwargs = {
        'source_url': 'https://www.youtube.com/watch?v=jpKoLJ5vc7E',
        'limit_cache_key': cache_key,
        # 'page_token': 'QURTSl9pMTB4OHp1S2JoZUtRTTNsNExkRVRLeTBoNEVvOWl1MmgzUnhHRnFnUmxjVWdXS3ZjOE5fSFowcVg3VHloeHhnV3ZRSTBmVzAwYw=='
    }
    t = Get3rdPartyData(kwargs=kwargs)
    t.execute()

