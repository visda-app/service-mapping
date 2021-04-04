from tasks.get_3rd_party_data import Get3rdPartyData


def test_get_3rd_party_data_execute():
    ## Better Bachelor:
        # 'video_id': 'oieNTzEeeX0',
    kwargs = {
        'video_id': 'I08SRDHwCos',        
        # 'page_token': 'QURTSl9pMTB4OHp1S2JoZUtRTTNsNExkRVRLeTBoNEVvOWl1MmgzUnhHRnFnUmxjVWdXS3ZjOE5fSFowcVg3VHloeHhnV3ZRSTBmVzAwYw=='
    }
    t = Get3rdPartyData(kwargs=kwargs)
    t.execute()

