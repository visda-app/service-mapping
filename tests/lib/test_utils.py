from lib import utils
import importlib


def test_get_module_from_string():
    # m = utils.get_module_from_string('tasks.get_3rd_party_data.Get3rdPartyData')
    m = utils.get_module_from_string('tasks.get_3rd_party_data')
    import pdb; pdb.set_trace()

