from curses import raw
import pytest
from unittest.mock import Mock, patch
import json
import numpy as np
from copy import deepcopy
from uuid import uuid4

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


def get_test_embedding_data():
    file_name = 'tests/data/raw_embedding_1000.json'
    with open(file_name, 'r') as f:
        lines = f.readlines()

    lines = lines[:100]
    for line in lines:
        line = line.strip()

    embedding_data = [json.loads(line) for line in lines]
    return embedding_data


@pytest.fixture
def raw_embedding():
    return get_test_embedding_data()


@pytest.fixture
def raw_embedding_w_seq_id():
    embedding_data = get_test_embedding_data()
    for item in embedding_data:
        item['sequence_id'] = 'a_job_id_fixture'
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


@patch('tasks.cluster_texts._load_embeddings_from_db')
@patch('tasks.cluster_texts.TextModel')
def test_execute(mock_text_model, mock_embedding, raw_embedding_w_seq_id):

    np.random.seed(1)
    class MockTextModel:
        def get_embedding_by_text(self, *args):
            return list(np.random.randn(2))

    sequence_id = 'test_sequence_id_' + str(uuid4())

    # mock_text_model.get_embedding_by_text.return_value = list(rnd_vect)
    mock_text_model.return_value = MockTextModel

    cluster_texts = clusterer.ClusterTexts(kwargs={
        "sequence_id": sequence_id,
    })
    mock_embedding.return_value = raw_embedding_w_seq_id
    res = cluster_texts.execute()
    # breakpoint()
