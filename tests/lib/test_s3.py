import json
import pytest
from unittest import TestCase

from lib import s3


S3_TEST_KEY = 'test/atestfilename0921.txt'

@pytest.fixture(scope='module')
def s3_key():
    yield S3_TEST_KEY
    s3._delete_from_s3(S3_TEST_KEY)


def test__upload_to_s3(s3_key):
    data = {'children': ['a', 'list', 'of', 'data']}
    s3._upload_to_s3(S3_TEST_KEY, data)

    obj_bin = s3._download_from_s3(S3_TEST_KEY)
    obj_str = obj_bin.decode('utf-8')
    result = json.loads(obj_str)

    assert result == data


def test__upload_to_s3_duplicated_key(s3_key):

    data = {'children': ['a', 'list', 'of', 'data']}
    s3._upload_to_s3(S3_TEST_KEY, data)

    new_data = {'parents': ['another', 'list', 'of', 'data']}
    with pytest.raises(ValueError) as e:
        s3.upload_to_s3_with_check(S3_TEST_KEY, data)

@pytest.mark.parametrize('test_data', [
    {'children': ['a', 'list', 'of', 'data']},
    {'children': [
        {'name': 'a'},
        {'embedding': [1.334, 1.4e-10, 1.2e2, 5]},
        {'text': '''⌛ Ḽơᶉëᶆ ȋṕšᶙṁ ḍỡḽǭᵳ ʂǐť ӓṁệẗ, ĉṓɲṩḙċťᶒțûɾ ấɖḯƥĭṩčįɳġ ḝłįʈ
                ᶻᶜᶜᶜᶜᶜᶜᶜᶜᶜᶜᶜᶜᶜᶜᶜᶜᶜᶜᶜᶜ, șếᶑ ᶁⱺ ẽḭŭŝḿꝋď ṫĕᶆᶈṓɍ ỉñḉīḑȋᵭṵńť ṷŧ 
                ḹẩḇőꝛế éȶ đꝍꞎôꝛȇ ᵯáꞡᶇā ąⱡîɋṹẵ'''
        }
    ]},
])
def test__compress(s3_key, test_data):
    data = json.dumps(test_data)
    compressed_data = s3._compress(data)
    s3._upload_to_s3(S3_TEST_KEY, compressed_data)

    d0 = s3._download_from_s3(S3_TEST_KEY)
    d1 = s3._decompress(d0)
    d5 = json.loads(d1)

    assert d5 == test_data
