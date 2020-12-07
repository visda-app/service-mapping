import pytest
import json
import numpy as np
from copy import deepcopy

import clusterer
from data.fixtures import (
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
