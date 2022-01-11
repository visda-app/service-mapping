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
    url= 'https://www.youtube.com/watch?v=jpKoLJ5vc7E'
    job_id = str(uuid4())

    t = Get3rdPartyData(
        job_id=job_id,
        kwargs={
            'source_url': url,
            'limit_cache_key': cache_key,
        }
    )

    t.execute()

