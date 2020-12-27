from tasks.get_3rd_party_data import Get3rdPartyData


def test_get_3rd_party_data_execute():
    # kwargs = {
    #     'video_id': 'Hag7CLks5jc',  # 'oieNTzEeeX0',
    #     'test': True,  # means the excute class will save the results to a local file
    # }

    ## Better Bachelor:
    kwargs = {
        'video_id': 'oieNTzEeeX0',
        'test': True,  # means the excute class will save the results to a local file
        'page_token': 'QURTSl9pMTB4OHp1S2JoZUtRTTNsNExkRVRLeTBoNEVvOWl1MmgzUnhHRnFnUmxjVWdXS3ZjOE5fSFowcVg3VHloeHhnV3ZRSTBmVzAwYw=='
    }
    Get3rdPartyData().execute(**kwargs)

