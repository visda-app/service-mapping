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


def test_get_youtube_video_url():
    TEST_URLS = {
        "www.youtube.com/watch?v=_lOT2p_FCvA&feature=feedu": "_lOT2p_FCvA",
        "http://www.youtube.com/watch?v=-wtIMTCHWuI": "-wtIMTCHWuI",
        "http://www.youtube.com/v/-wtIMTCHWuI?version=3&autohide=1": "-wtIMTCHWuI",
        "http://youtu.be/-wtIMTCHWuI": "-wtIMTCHWuI",
        # "http://www.youtube.com/oembed?url=http%3A//www.youtube.com/watch?v%3D-wtIMTCHWuI&format=json": "-wtIMTCHWuI",
        # "http://www.youtube.com/attribution_link?a=JdfC0C9V6ZI&u=%2Fwatch%3Fv%3DEhxJLojIE_o%26feature%3Dshare": "EhxJLojIE_o",
        # "https://www.youtube.com/attribution_link?a=8g8kPrPIi-ecwIsS&u=/watch%3Fv%3DyZv2daTWRZU%26feature%3Dem-uploademail": "yZv2daTWRZU",
        "https://www.youtube.com/watch?v=yZv2daTWRZU&feature=em-uploademail": "yZv2daTWRZU",
        "https://www.youtube.com/watch?v=0zM3nApSvMg&feature=feedrec_grec_index": "0zM3nApSvMg",
        "https://www.youtube.com/user/IngridMichaelsonVEVO#p/a/u/1/QdK8U-VIH_o": None,
        "https://www.youtube.com/v/0zM3nApSvMg?fs=1&amp;hl=en_US&amp;rel=0": "0zM3nApSvMg",
        "https://www.youtube.com/watch?v=0zM3nApSvMg#t=0m10s": "0zM3nApSvMg",
        "https://www.youtube.com/embed/0zM3nApSvMg?rel=0": "0zM3nApSvMg",
        "//www.youtube-nocookie.com/embed/up_lNV-yoK4?rel=0": "up_lNV-yoK4",
        "https://www.youtube-nocookie.com/embed/up_lNV-yoK4?rel=0": "up_lNV-yoK4",
        "http://www.youtube.com/user/Scobleizer#p/u/1/1p3vcRhsYGo": None,
        "http://www.youtube.com/watch?v=cKZDdG9FTKY&feature=channel": "cKZDdG9FTKY",
        "http://www.youtube.com/watch?v=yZ-K7nCVnBI&playnext_from=TL&videos=osPknwzXEas&feature=sub": "yZ-K7nCVnBI",
        "http://www.youtube.com/ytscreeningroom?v=NRHVzbJVx8I": "NRHVzbJVx8I",
        "http://www.youtube.com/watch?v=6dwqZw0j_jY&feature=youtu.be": "6dwqZw0j_jY",
        "http://www.youtube.com/user/Scobleizer#p/u/1/1p3vcRhsYGo?rel=0": None,
        "http://www.youtube.com/embed/nas1rJpm7wY?rel=0": "nas1rJpm7wY",
        "https://www.youtube.com/watch?v=peFZbP64dsU": "peFZbP64dsU",
        "http://youtube.com/v/dQw4w9WgXcQ?feature=youtube_gdata_player": "dQw4w9WgXcQ",
        "http://youtube.com/?v=dQw4w9WgXcQ&feature=youtube_gdata_player": "dQw4w9WgXcQ",
        "http://www.youtube.com/watch?v=dQw4w9WgXcQ&feature=youtube_gdata_player": "dQw4w9WgXcQ",
        "http://youtube.com/?vi=dQw4w9WgXcQ&feature=youtube_gdata_player": "dQw4w9WgXcQ",
        "http://youtube.com/watch?v=dQw4w9WgXcQ&feature=youtube_gdata_player": "dQw4w9WgXcQ",
        "http://youtube.com/watch?vi=dQw4w9WgXcQ&feature=youtube_gdata_player": "dQw4w9WgXcQ",
        "http://youtube.com/vi/dQw4w9WgXcQ?feature=youtube_gdata_player": "dQw4w9WgXcQ",
        "http://youtu.be/dQw4w9WgXcQ?feature=youtube_gdata_player": "dQw4w9WgXcQ",
        "http://www.youtube.com/user/SilkRoadTheatre#p/a/u/2/6dwqZw0j_jY": None,
        "https://www.youtube.com/watch?v=ishbTyLs6ps&list=PLGup6kBfcU7Le5laEaCLgTKtlDcxMqGxZ&index=106&shuffle=2655": "ishbTyLs6ps",
        "http://www.youtube.com/v/0zM3nApSvMg?fs=1&hl=en_US&rel=0": "0zM3nApSvMg",
        "http://www.youtube.com/watch?v=0zM3nApSvMg&feature=feedrec_grec_index": "0zM3nApSvMg",
        "http://www.youtube.com/watch?v=0zM3nApSvMg#t=0m10s": "0zM3nApSvMg",
        "http://www.youtube.com/embed/dQw4w9WgXcQ": "dQw4w9WgXcQ",
        "http://www.youtube.com/v/dQw4w9WgXcQ": "dQw4w9WgXcQ",
        "http://www.youtube.com/e/dQw4w9WgXcQ": "dQw4w9WgXcQ",
        "http://www.youtube.com/?v=dQw4w9WgXcQ": "dQw4w9WgXcQ",
        "http://www.youtube.com/watch?feature=player_embedded&v=dQw4w9WgXcQ": "dQw4w9WgXcQ",
        "http://www.youtube.com/?feature=player_embedded&v=dQw4w9WgXcQ": "dQw4w9WgXcQ",
        "http://www.youtube.com/user/IngridMichaelsonVEVO#p/u/11/KdwsulMb8EQ": None,
        "http://www.youtube-nocookie.com/v/6L3ZvIMwZFM?version=3&hl=en_US&rel=0": "6L3ZvIMwZFM",
        "http://www.youtube.com/user/dreamtheater#p/u/1/oTJRivZTMLs": None,
        "https://youtu.be/oTJRivZTMLs?list=PLToa5JuFMsXTNkrLJbRlB--76IAOjRM9b": "oTJRivZTMLs",
        "http://www.youtube.com/watch?v=oTJRivZTMLs&feature=youtu.be": "oTJRivZTMLs",
        "http://youtu.be/oTJRivZTMLs&feature=channel": "oTJRivZTMLs",
        "http://www.youtube.com/ytscreeningroom?v=oTJRivZTMLs": "oTJRivZTMLs",
        "http://www.youtube.com/embed/oTJRivZTMLs?rel=0": "oTJRivZTMLs",
        "http://youtube.com/vi/oTJRivZTMLs&feature=channel": "oTJRivZTMLs",
        "http://youtube.com/?v=oTJRivZTMLs&feature=channel": "oTJRivZTMLs",
        "http://youtube.com/?feature=channel&v=oTJRivZTMLs": "oTJRivZTMLs",
        "http://youtube.com/?vi=oTJRivZTMLs&feature=channel": "oTJRivZTMLs",
        "http://youtube.com/watch?v=oTJRivZTMLs&feature=channel": "oTJRivZTMLs",
        "http://youtube.com/watch?vi=oTJRivZTMLs&feature=channel": "oTJRivZTMLs",
        "https://m.youtube.com/watch?v=m_kbvp0_8tc": "m_kbvp0_8tc",
        "http://youtu.be/_lOT2p_FCvA": "_lOT2p_FCvA",
        "http://www.youtube.com/embed/_lOT2p_FCvA": "_lOT2p_FCvA",
        "http://www.youtube.com/v/_lOT2p_FCvA?version=3&amp;hl=en_US": "_lOT2p_FCvA",
        "https://www.youtube.com/watch?v=rTHlyTphWP0&index=6&list=PLjeDyYvG6-40qawYNR4juzvSOg-ezZ2a6": "rTHlyTphWP0",
        "youtube.com/watch?v=_lOT2p_FCvA": "_lOT2p_FCvA",
        "google.com": None,
        "youtube.com": None,
        "http://youtube.com/": None,
        "https://www.youtube.com": None,
    }
    for key in TEST_URLS:
        assert utils.get_youtube_video_id(key) == TEST_URLS[key], f"url= {key}"