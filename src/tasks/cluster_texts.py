from uuid import uuid4
from copy import copy, deepcopy
import numpy as np
from collections import defaultdict
from sklearn.manifold import TSNE
from sklearn.cluster import AffinityPropagation
from dataclasses import dataclass

from lib.logger import logger
from lib.nlp import get_pruned_stem
from models.clustering_helper import (
    load_first_embeddings_from_db,
    save_clustering_to_db
)
from tasks.base_task import BaseTask
from tasks.base_task import record_start_finish_time_in_db



MAX_CLUSTER_SIZE = 10
# To calculate radius for each bubble
MIN_RADIUS = 1
MIN_ALLOWED_DISTANCE = 1
MAX_NUM_TOKENS = 3


@dataclass
class KeywordItem:
    keyword: str
    count: int
    relevance_score: float

    def __post_init__(self):
        self.relevance_score = round(self.relevance_score, 2)


def run_tsne(x):
    """
    Reduce the dimension of the input vector

    Arg:
        x (numpy.array): a list of lists containing vectors.

    Retrun:
        (numpy.array): reduced dimension
    """
    low_dim_x = TSNE(
        n_components=2,
        learning_rate=200,
        perplexity=30
    ).fit_transform(x)
    return low_dim_x


def reduce_dimension(embedding_data):
    """
    Extracts the hight dimension vectors from the data,
    run the dimension reducsion algorithm and add the
    low dimension vectors to the original data

    Arg:
        embedding_data (List): A list of dictionaries where each
                                dict element has a value for
                                the key `embedding`.
    """
    # get vectors
    embedding_data = copy(embedding_data)
    vect_list = []
    for e in embedding_data:
        vect_list.append(e.get('embedding'))

    # reduce dimension
    vect_array = np.array(vect_list)
    low_dim_embeddings = run_tsne(vect_array)

    # Merge back the low dimensions into the original data
    for i, item in enumerate(embedding_data):
        item['low_dim_embedding'] = list(low_dim_embeddings[i])
    
    logger.debug(f'embedding_data_with_low_dimension={embedding_data}')
    return embedding_data


def ap_cluster(x):
    """
    Clusters data using affinity propagation algorithm.
    """
    clustering = AffinityPropagation(
        random_state=5, damping=0.95
    ).fit(x)

    cluster_labels = clustering.labels_
    cluster_centers = clustering.cluster_centers_
    return cluster_labels, cluster_centers


def cluster_data(data, coordinates_key=None):
    """
    cluster a list of objects with a 'coordinates' key

    Args
        coordinates_key : string, A name for the lookup key for the coordinates
        data : list[dicts], A list of objects that has a key for coordinates
        [
            {
                coordinates_key: [x1, x2, ...],
                ...
            },
            ...
        ]

    Returns
        Adds the clustering_info to each object in the input list of data
    """
    # Cluster data
    coordinates = []
    for item in data:
        coordinates.append(item[coordinates_key])
    cluster_labels, cluster_centers = ap_cluster(np.array(coordinates))

    # add clustering info to the data structure
    for i, item in enumerate(data):
        cluster_info = {}
        cluster_info['is_cluster_head'] = item[coordinates_key] in cluster_centers
        cluster_info['cluster_label'] = cluster_labels[i]
        item['cluster_info'] = cluster_info
        # item['embedding'] = ''
        # item['text'] = ''

    # sort data
    result = sorted(
        data, key=lambda x:
            (x['cluster_info']['cluster_label'], not x['cluster_info']['is_cluster_head'])
    )

    return result


def format_to_nested_clustering(clustered_data):
    """
    transform a list of object into a nested list based on clustering info.
    If there is only one cluster, it retruns the same input

    Arg:
        clustered_data (list): A flat list of objects

    Return:
        (list): a hierarchical list of objects
    """
    # check the number of cluster heads; return if there is only one cluster
    num_cluster_heads = 0
    for item in clustered_data:
        if item['cluster_info']['is_cluster_head']:
            num_cluster_heads += 1
    if num_cluster_heads == 1:
        return clustered_data

    # Break down if there are more than one cluster
    result = []
    for item in clustered_data:
        item['children'] = item.get('children', [])
        if item['cluster_info']['is_cluster_head']:
            # Add cluster head to the tree and also add it as the first child
            result.append(item)
            if not item.get('children'):
                result[-1].get('children', []).append(deepcopy(item))
        else:
            result[-1].get('children', []).append(item)
    # Prune nodes with only one child.
    # which would be the parent that is just repeated
    for item in result:
        if len(item.get('children', [])) <= 1:
            item['children'] = []
    return result


def cluster_hierarchically(
    embedding_data_w_low_dim,
    include_original_cluster_label=False
):
    """
    Gets an array of input data with dimension and performs
    clustering on them and represents data as hierarchical

    This function can be called recursively

    Args
        [ {'low_dim_embedding': [], ...}, ...]
    """
    embedding_data_w_low_dim = deepcopy(embedding_data_w_low_dim)

    clustered_data = cluster_data(
        embedding_data_w_low_dim,
        coordinates_key='low_dim_embedding'
    )
    if include_original_cluster_label:
        for item in clustered_data:
            item['original_cluster_label'] = item['cluster_info']['cluster_label']

    nested_clusters = format_to_nested_clustering(clustered_data)
    return nested_clusters


def bfs_break_down(head, max_cluster_size=MAX_CLUSTER_SIZE):
    """
    Traverse the nested clustering and break down if a node has too many
    children

    Arg:
        head (dict): a dictionary with the following formatting
                    {
                        'children': [
                            {
                                'children': [...]
                                'uuid': '934b0cfe-98c1-4a69-ba01-61565d7ab709',
                                ...
                            },
                            ...
                        ]
                    }
    """
    frontiers = [head]
    while frontiers:
        next = frontiers.pop(0)
        if len(next.get('children', [])) > max_cluster_size:
            next['children'] = cluster_hierarchically(
                next.get('children', [])
            )
        frontiers.extend(next.get('children', []))


def insert_children_count(head):
    """
    Add total number of children for each node recursively

    Arg:
        head (dict): a dictionary with the following formatting
                    {
                        'children': [
                            {
                                'children': [...]
                                'uuid': '934b0cfe-98c1-4a69-ba01-61565d7ab709',
                                ...
                            },
                            ...
                        ]
                    }
    """
    if not head.get('children', []):
        head['children_count'] = 0
        return 0
    sum = 0
    for node in head.get('children', []):
        sum += 1 + node.get(
            'children_count', insert_children_count(node)
        )
    head['children_count'] = sum
    return sum


def insert_d3uuid(head):
    """
    Traverse the tree of data and insert a unique identifier for
    each node that will be used for d3 distinctions later
    """
    if not head:
        return
    frontiers = [head]
    while frontiers:
        next = frontiers.pop(0)
        next['d3uuid'] = str(uuid4())
        frontiers.extend(next.get('children', []))


def insert_parents_info(head):
    """
    Insert parents coordinates and radius in each child

    Arg:
        head (dict): a dictionary with the following formatting
                    {
                        'children': [
                            {
                                'children': [...]
                                'uuid': '934b0cfe-98c1-4a69-ba01-61565d7ab709',
                                ...
                            },
                            ...
                        ]
                    }
    """
    if not head:
        return
    frontiers = [head]
    while frontiers:
        next = frontiers.pop(0)
        for child in next.get('children', []):
            child['parent'] = {
                'low_dim_embedding': next.get('low_dim_embedding'),
                'radius': next.get('radius'),
                'd3uuid': next.get('d3uuid')
            }
        frontiers.extend(next.get('children', []))
    return


def get_radius_multiplier(clustering_data):
    """
    get the max multiplier that is used to inflate the bubble sizes
    Args
        clustering_data : list(dict) : a list of objects. Objects have a key
                            for number of children
    """
    multiplier = float("inf")
    if len(clustering_data) < 2:
        multiplier = 0
    for i in range(len(clustering_data)):
        for j in range(i + 1, len(clustering_data)):
            filled = max(
                np.sqrt(clustering_data[i]['children_count']),
                np.sqrt(clustering_data[j]['children_count'])
            )
            p1 = np.array([
                float(clustering_data[i]['low_dim_embedding'][0]),
                float(clustering_data[i]['low_dim_embedding'][1])
            ])
            p2 = np.array([
                float(clustering_data[j]['low_dim_embedding'][0]),
                float(clustering_data[j]['low_dim_embedding'][1])
            ])
            d = np.linalg.norm(p1 - p2)
            if d > MIN_ALLOWED_DISTANCE:
                multiplier = min(multiplier, d / filled)
    return multiplier


def insert_radius(head, radius_multiplier_factor):
    """
    Insert the radius in all object in the tree, and also for
    each object, insert the radius of their parent

    Arg:
        head (dict): a dictionary with the following formatting
                    {
                        'children': [
                            {
                                'children': [...]
                                'uuid': '934b0cfe-98c1-4a69-ba01-61565d7ab709',
                                ...
                            },
                            ...
                        ]
                    }
    """
    frontiers = copy(head.get('children', []))
    while frontiers:
        next = frontiers.pop(0)
        if next.get('children'):
            next['radius'] = max([
                np.sqrt(next['children_count']) * radius_multiplier_factor,
                MIN_RADIUS
            ])
        else:
            next['radius'] = MIN_RADIUS
        frontiers.extend(next.get('children', []))


def _group_keywords_by_count(keywords):
    """
    Remove punctuations and stem the words and then insert
    the counts of the stemmed root words.
    
    This function is unit tested; to see the input output
    examples, refer to the tests.
    """
    token_count = defaultdict(int)
    token_relevance_score = defaultdict(float)
    for kw in keywords:
        token_count[kw['keyword']] += kw['count']
        token_relevance_score[kw['keyword']] += kw['relevance_score']
    # Construct a new list of results
    res = []
    seen = set()
    for kw in keywords:
        if kw['keyword'] not in seen:
            kw.update({
                'count': token_count[kw['keyword']],
                'relevance_score': _round_2(token_relevance_score[kw['keyword']])
            })
            res.append(kw)
            seen.add(kw['keyword'])
    # sort by counts and then relevance scores
    res.sort(key=lambda x: (-x['count'], -x['relevance_score']))
    return res


def _group_stemmed_keywords_by_counts(keywords):
    keywords = deepcopy(keywords)
    for item in keywords:
        item['keyword'] = get_pruned_stem(item['keyword'])
    return _group_keywords_by_count(keywords)


def insert_and_return_keywords(head):
    """
    Performs a post order tree traverse to insert all the keywords. 
    """
    keywords = []
    children = head.get('children')
    if children:
        for child in children:
            keywords.extend(insert_and_return_keywords(child))
        keywords = _group_stemmed_keywords_by_counts(keywords)
    else:
        keywords = [
            {
                'keyword': item['token'],
                'count': 1,
                'relevance_score': _round_2(item['similarity']), 
            } for item in head['tokens'][:1]
        ]
    head['keywords'] = deepcopy(keywords)
    return head['keywords']


def prune_keywords(head):
    """
    Caps the nubmer of keywords to a pre determined value
    """
    pass


def insert_meta_data(head):
    """
    Insert the metadat field that includes the following
        metadata:
            max_x, min_x
            max_y, min_y
    """
    min_x = float("inf")
    max_x = float("-inf")
    min_y = float("inf")
    max_y = float("-inf")
    frontiers = deepcopy(head.get('children', []))
    while frontiers:
        next = frontiers.pop(0)
        min_x = min(next['low_dim_embedding'][0] - next['radius'], min_x)
        min_y = min(next['low_dim_embedding'][1] - next['radius'], min_y)
        max_x = max(next['low_dim_embedding'][0] + next['radius'], max_x)
        max_y = max(next['low_dim_embedding'][1] + next['radius'], max_y)
        frontiers.extend(next.get('children', []))
    head['metadata'] = {
        'x': {
            'max': max_x,
            'min': min_x,
        },
        'y': {
            'max': max_y,
            'min': min_y,
        },
        'radius': {
            'max': max(max_x - min_x, max_y - min_y)
        }
    }


def get_formatted_item(item):
    """
    Arg:
        An input item
    """
    entry = {
        'x': float(item['low_dim_embedding'][0]),
        'y': float(item['low_dim_embedding'][1]),
        'uuid': item.get('uuid'),
        'd3uuid': item.get('d3uuid'),
        'text': item.get('text'),
        'cluster_label': int(item['original_cluster_label']),
        'children_count': item['children_count'],
        'radius': item['radius'],
        'parent': {
            'x': (
                float(item['parent']['low_dim_embedding'][0])
                if item['parent']['low_dim_embedding']
                else float(item['low_dim_embedding'][0])
            ),
            'y': (
                float(item['parent']['low_dim_embedding'][1])
                if item['parent']['low_dim_embedding']
                else float(item['low_dim_embedding'][1])
                 ),
            'radius': (
                float(item['parent']['radius'])
                if item['parent']['radius']
                else item['radius']
            ),
            'd3uuid': item['parent']['d3uuid'],
        },
        'children': [],
        'keywords': item['keywords'],
    }
    return entry


def get_reshaped_data(node):
    """
    """
    if not node:
        return
    new_node = {}
    if 'low_dim_embedding' in node:
        new_node = get_formatted_item(node)
    new_node['children'] = [
        get_reshaped_data(c) for c in node.get('children', [])
    ]
    return new_node


def partition_by_sequence_id(list_of_objects):
    """
    Partition the input data by their sequence id's

    Args:
      list_of_objects (list): A list of objects (dicts)
    """
    KEY = 'sequence_id'
    partitioned_items = defaultdict(list)
    for item in list_of_objects:
        key = item[KEY]
        partitioned_items[key].append(item)
    return partitioned_items


def cluster_hierarchically_add_meta_data(sequence_id, data_w_low_dim):
    """
    Cluster the input data into a graph (hierarchical)
    clustering and add meta data

    Args:
        sequence_id (str): An ID for the sequence
        data_w_low_dim (list): list of dicts
    """
    logger.debug("Clustering...")
    nested_clusters = cluster_hierarchically(
        data_w_low_dim, include_original_cluster_label=True
    )

    head = {}
    head['children'] = nested_clusters

    # logger.debug("Further breaking down clusters...")
    # bfs_break_down(head)

    logger.debug("Insert Stuff...")
    insert_children_count(head)
    insert_d3uuid(head)
    radius_multiplier_factor = get_radius_multiplier(head.get('children', []))
    insert_radius(head, radius_multiplier_factor)
    insert_parents_info(head)
    insert_meta_data(head)
    insert_and_return_keywords(head)

    logger.debug("Formatting data...")
    reshaped_data = get_reshaped_data(copy(head))
    reshaped_data['metadata'] = head['metadata']
    return reshaped_data


class ClusterTexts(BaseTask):

    public_description = "Creating the text maps and clusters."

    @record_start_finish_time_in_db
    def execute(self):
        """
        Loads all the texts and embeddings for a sequence id,
        performs dimension reduction and clustering, and saves
        the results to database

        Args:
            sequence_ids (list[str]): A list of ids for all
                the texts in the sequence that will be processed
        """
        TOTAL_NUMBER_OF_STEPS = 4
        self.record_progress(0, TOTAL_NUMBER_OF_STEPS)

        sequence_ids = self.kwargs['sequence_ids']

        logger.debug("Loading data from DB...")
        embedding_data = []
        for i in sequence_ids:
            embedding_data.extend(load_first_embeddings_from_db(i))
        self.record_progress(1, TOTAL_NUMBER_OF_STEPS)

        if not embedding_data or type(embedding_data) is not list:
            raise ValueError('Invalid embedding data')

        logger.debug("Reducing dimension...")
        data_w_low_dim = reduce_dimension(embedding_data)
        self.record_progress(2, TOTAL_NUMBER_OF_STEPS)

        logger.debug("Partition by seqence_id...")
        partitioned_data = partition_by_sequence_id(data_w_low_dim)
        self.record_progress(3, TOTAL_NUMBER_OF_STEPS)

        logger.debug("Start clustering for all sequence id's...")
        for sequence_id in partitioned_data:
            clustered_data = cluster_hierarchically_add_meta_data(
                sequence_id, partitioned_data[sequence_id]
            )

            logger.debug(f"Saving sequence_id={sequence_id} to DB...")

            save_clustering_to_db(
                sequence_id, clustered_data
            )
        self.record_progress(4, TOTAL_NUMBER_OF_STEPS)

        logger.debug("Done!")
