import unittest
from tasks.get_3rd_party_data import Get3rdPartyData


def test_get_3rd_party_data_execute():
    args = ['one', 'and', 'two']
    kwargs = {'one': 1, 'two': 2}
    Get3rdPartyData().execute(*args, **kwargs)

