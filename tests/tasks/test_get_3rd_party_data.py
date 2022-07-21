from uuid import uuid4
import pytest
from unittest.mock import patch

from tasks.get_3rd_party_data import Get3rdPartyData
from lib.cache import cache_region


@pytest.fixture
def cache_key():
    key = str(uuid4())
    cache_region.set(key, 50)

    yield key

    cache_region.delete(key)


@pytest.fixture
def cache_key_02():
    key = str(uuid4())
    cache_region.set(key, 50)

    yield key

    cache_region.delete(key)


@patch('tasks.get_3rd_party_data.Get3rdPartyData._publish_texts_on_message_bus')
def test_get_3rd_party_data_execute(mock_publish_texts_on_message_bus, cache_key, cache_key_02):
    url= 'https://www.youtube.com/watch?v=jpKoLJ5vc7E'
    job_id = str(uuid4())

    t = Get3rdPartyData(
        job_id=job_id,
        kwargs={
            'source_url': url,
            'limit_cache_key': cache_key,
            'total_num_texts_cache_key': cache_key_02,
            'use_test_data': True,
        }
    )

    t.execute()

