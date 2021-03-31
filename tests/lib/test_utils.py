from lib import utils
import tasks


def test_get_module_and_class_from_string():
    m, c = utils.get_module_and_class_from_string(
        'tasks.get_3rd_party_data.Get3rdPartyData'
    )
    assert m is tasks.get_3rd_party_data
    assert c == 'Get3rdPartyData'
