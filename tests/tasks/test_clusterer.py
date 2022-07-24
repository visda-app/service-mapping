import pytest
import json
import numpy as np
from copy import deepcopy

import tasks.cluster_texts as clusterer
from tasks.cluster_texts import KeywordItem
from tests.data.fixtures import (
    CLUSTERED_DATA,
    NESTED_DATA,
    MULTI_NESTED_DATA,
    MULTI_NESTED_DATA_W_CHILDREN_COUNT
)


class MyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return super(MyEncoder, self).default(obj)


@pytest.fixture
def raw_embedding():
    file_name = 'tests/data/raw_embedding_1000.json'
    with open(file_name, 'r') as f:
        lines = f.readlines()

    lines = lines[:100]
    for line in lines:
        line = line.strip()

    embedding_data = [json.loads(line) for line in lines]
    return embedding_data


@pytest.fixture
def low_dim_embedding():
    file_name = 'tests/data/low_dim_embedding.json'
    with open(file_name, 'r') as f:
        content = f.read()
    return json.loads(content)


@pytest.fixture
def hierarchical_clustering():
    file_name = 'tests/data/hierarchical_clustering.json'
    with open(file_name) as f:
        content = f.read()
    return json.loads(content)


@pytest.fixture
def bfs_break_down():
    file_name = 'tests/data/bfs_break_down.json'
    with open(file_name) as f:
        content = f.read()
    return json.loads(content)


def test_reduce_dimension(raw_embedding):
    ret_val = clusterer.reduce_dimension(raw_embedding)
    assert len(ret_val) == len(raw_embedding)
    for e in ret_val:
        assert 'low_dim_embedding' in e
        assert len(e['low_dim_embedding']) == 2


def test_cluster_data(low_dim_embedding):
    clustered_data = clusterer.cluster_data(
        low_dim_embedding,
        coordinates_key='low_dim_embedding'
        )
    for item in clustered_data:
        assert 'cluster_info' in item
        assert 'is_cluster_head' in item['cluster_info']
        assert 'cluster_label' in item['cluster_info']


def test_format_to_nested_clustering():
    actual_result = clusterer.format_to_nested_clustering(
        CLUSTERED_DATA
    )
    expected_result = NESTED_DATA

    assert actual_result == expected_result


def test_cluster_hierarchically(
    low_dim_embedding,
    hierarchical_clustering
):
    # massage data
    for e in low_dim_embedding:
        e['embedding'] = ''
        # e['text'] = e['uuid'][:6]

    actual_result = clusterer.cluster_hierarchically(
        low_dim_embedding
    )

    # with open('tests/data/hierarchical_clustering.json', 'w') as f:
    #     f.write(json.dumps(
    #         actual_result,
    #         cls=MyEncoder,
    #         indent=4
    #     ))

    expected_result = hierarchical_clustering
    assert expected_result == actual_result


@pytest.mark.skip("BFS break down is deprecated for now")
def test_bfs_break_down(
    hierarchical_clustering,
    bfs_break_down
):
    data = deepcopy({'children': hierarchical_clustering})
    clusterer.bfs_break_down(data, max_cluster_size=5)
    assert data == bfs_break_down


def test_insert_children_count():
    expected_result = MULTI_NESTED_DATA_W_CHILDREN_COUNT
    clusterer.insert_children_count(MULTI_NESTED_DATA)
    actual_result = MULTI_NESTED_DATA
    assert actual_result == expected_result


def test_partition_by_sequence_id():
    KEY = 'sequence_id'
    data = [
        {
            KEY: '1',
            "text": "This is the first entry",
        },
        {
            KEY: 2,
            "text": "Fall is colorful",
        },
        {
            KEY: 2,
            "text": "Baked potato is delicious",
        }
    ]
    actual_results = clusterer.partition_by_sequence_id(data)
    expected_result = {
        2: [
            {
                KEY: 2,
                "text": "Fall is colorful",
            },
            {
                KEY: 2,
                "text": "Baked potato is delicious",
            }
        ],
        '1': [
            {
                KEY: '1',
                "text": "This is the first entry",
            },
        ]
    }
    assert actual_results == expected_result


def test__group_keywords_by_count():
    sample_data = [
        KeywordItem(count=1, word='cables', relevance_score=0.39),
        KeywordItem(count=1, word='cable', relevance_score=0.3),
        KeywordItem(count=1, word='snapon', relevance_score=0.44),
        KeywordItem(count=1, word='cable', relevance_score=0.23),
        KeywordItem(count=1, word='cable', relevance_score=0.35),
        KeywordItem(count=1, word='cable', relevance_score=0.35),
        KeywordItem(count=1, word='copper', relevance_score=0.39),
        KeywordItem(count=1, word='cable', relevance_score=0.43),
        KeywordItem(count=1, word='cable', relevance_score=0.35),
        KeywordItem(count=1, word='cable', relevance_score=0.43),
        KeywordItem(count=1, word='cable', relevance_score=0.28),
        KeywordItem(count=1, word='cabled', relevance_score=0.39),
    ]
    expected_result = [
        {'count': 8, 'keyword': 'cable', 'relevance_score': 2.72},
        {'count': 1, 'keyword': 'snapon', 'relevance_score': 0.44},
        {'count': 1, 'keyword': 'cables', 'relevance_score': 0.39},
        {'count': 1, 'keyword': 'copper', 'relevance_score': 0.39},
        {'count': 1, 'keyword': 'cabled', 'relevance_score': 0.39},
    ]
    result = clusterer._group_keywords_by_count(sample_data)
    assert (result[0].word, result[0].count, result[0].relevance_score) == ('cable', 8, 2.72)


def test_cluster_hierarchically_add_meta_data(low_dim_embedding):
    """
    Main test to test the excec function of the 
    """
    res = clusterer.cluster_hierarchically_add_meta_data("-", low_dim_embedding)
    import pprint, json
    pp = pprint.PrettyPrinter().pprint
    # pp(res)
    breakpoint()

    # with open("_temp.txt", "w") as f:
    #     f.write(json.dumps(res, indent=4))


def test_main():
    """
    A functional test for the main clusterer
    """
    sequence_ids = ['1', '2']
    # clusterer.load_and_cluster_and_save(sequence_ids)

    # from models.text import ClusteredText
    # res = ClusteredText.get_last_by_sequence_id('1')
    # import pdb; pdb.set_trace()
