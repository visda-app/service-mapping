import json
import pytest
from unittest import TestCase
from lib import s3


class TestS3(TestCase):
    def setUp(self):
        self.key = 'test/atestfilename0921.txt'
    
    def tearDown(self) -> None:
        s3._delete_from_s3(self.key)

    def test__upload_to_s3(self):
        data = {'children': ['a', 'list', 'of', 'data']}
        s3._upload_to_s3(self.key, data)

        result = s3._get_object_from_s3(self.key)

        assert result == data

    def test__upload_to_s3_duplicated_key(self):

        data = {'children': ['a', 'list', 'of', 'data']}
        s3._upload_to_s3(self.key, data)

        new_data = {'parents': ['another', 'list', 'of', 'data']}
        with pytest.raises(ValueError) as e:
            s3.upload_to_s3_with_check(self.key, data)

