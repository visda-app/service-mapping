from lib import utils
import tasks


def test_get_module_and_class_from_string():
    m, c = utils.get_module_and_class_from_string(
        'tasks.get_3rd_party_data.Get3rdPartyData'
    )
    assert m is tasks.get_3rd_party_data
    assert c == 'Get3rdPartyData'


def test_get_class_from_string():
    class_string = 'tasks.get_3rd_party_data.Get3rdPartyData'
    assert (
        utils.get_class_from_string(class_string)
        is tasks.get_3rd_party_data.Get3rdPartyData
    )


def test_get_class_from_string__predicate():
    class_string = 'tasks.get_3rd_party_data'
    assert (
        utils.get_class_from_string(class_string)
        is not tasks.get_3rd_party_data.Get3rdPartyData
    )
