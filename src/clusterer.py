import json
import time
import numpy as np
from sklearn.manifold import TSNE
from sklearn.cluster import AffinityPropagation
import matplotlib.pyplot as plt

from lib.logger import logger

def load_embeddings(filename):
    """
    Load high dimensional embedding from database
    Args:
    Return:
        [
            {
                "uuid": "a uuid",
                "text": "a text ",
                "embedding": ['float1', 'float2', ....]
            },
            ...
        ]
    """
    with open(filename, 'r') as f:
        lines = f.readlines()
    embedding_data = []
    for line in lines:
        embedding_data.append(json.loads(line))
    vect_list = []
    for e in embedding_data:
        vect_list.append(e.get('embedding'))
    vect_array = np.array(vect_list)
    return embedding_data, vect_array


def get_positive_sentiment_embedding():
    """
    Get the embedding vector for a statement with
    a positive sentiment

    Return:
        (numpy.array): a vector embedding for a positive statemen
    """
    pass


def get_negative_sentiment_embedding():
    """
    Get the embedding vector for a statement with a
    negative sentiment

    Return:
        (numpy.array): a vector embedding for a negative statemen
    """
    pass


def reduce_dimension(x):
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


def cluster(x):
    """
    Clusters data
    """
    clustering = AffinityPropagation(
        random_state=5, damping=0.95
    ).fit(x)

    cluster_labels = clustering.labels_
    cluster_centers = clustering.cluster_centers_
    return cluster_labels, cluster_centers


def get_formatted_data(
    low_dim_embeddings,
    embedding_data,
    cluster_labels,
    cluster_centers
):
    """
    Returns a list of dictionaries that contains
    low dimension coordinates, and meta data. This
    function also formats the output and sort them by
    clustering label and bring the cluster head to
    the top of each category
    """
    metadata = []
    for i in range(len(embedding_data)):
        entry = {
            'x': str(low_dim_embeddings[i, 0]),
            'y': str(low_dim_embeddings[i, 1]),
            'uuid': embedding_data[i].get('uuid'),
            'text': embedding_data[i].get('text'),
            'cluster_label': int(cluster_labels[i]),
            'is_cluster_head': low_dim_embeddings[i, :] in cluster_centers
        }
        metadata.append(entry)
    result = sorted(
        metadata, key=lambda x:
            (x['cluster_label'], not x['is_cluster_head'])
    )
    return result


FILE_NAME = "/code/tmp/output_1000.json"
sentiment_file_name = "/code/tmp/labeled_sentiments.json"

unlabeled_embedding_data, unlabeled_vects = load_embeddings(FILE_NAME)
labeled_embedding_data, labeled_vects = load_embeddings(sentiment_file_name)
aug_vects = np.concatenate(
    (unlabeled_vects, labeled_vects),
    axis=0
)

logger.debug("Start reducing dimenssion...")
low_dim_embeddings = reduce_dimension(aug_vects)

logger.debug("Start Clustering...")
cluster_labels, cluster_centers = cluster(low_dim_embeddings)

splitter = len(unlabeled_embedding_data)

unlabeled_data_summary = get_formatted_data(
    low_dim_embeddings[:splitter],
    unlabeled_embedding_data,
    cluster_labels[:splitter],
    cluster_centers[:splitter]
)

labeled_data_summary = get_formatted_data(
    low_dim_embeddings[splitter:],
    labeled_embedding_data,
    cluster_labels[splitter:],
    cluster_centers[splitter:]
)

FILE_NAME_CLUSTERED_UNLABELED = "/code/tmp/output_unl_clustered.json"
with open(FILE_NAME_CLUSTERED_UNLABELED, 'w') as f:
    f.write(json.dumps(unlabeled_data_summary, indent=4))
FILE_NAME_CLUSTERED_LABELED = "/code/tmp/output_l_clustered.json"
with open(FILE_NAME_CLUSTERED_LABELED, 'w') as f:
    f.write(json.dumps(labeled_data_summary, indent=4))
