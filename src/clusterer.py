import json
import time
import numpy as np
from sklearn.manifold import TSNE
from sklearn.cluster import AffinityPropagation
import matplotlib.pyplot as plt

from src.lib.logger import logger
from src.models.text import (
    load_from_db,
    save_clustering_to_db
    )


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


def load_cluster_save(sequence_ids):
    """
    load all the texts and embeddings for a sequence id,
    performs dimension reduction and clustering, and saves
    the results to database

    Args:
        sequence_ids (list[str]): A list of ids for all
            the texts in the sequence that will be processed
    """
    logger.debug("Loading data from DB...")
    embedding_data = []
    for i in sequence_ids:
        embedding_data.extend(load_from_db(i))

    vect_list = []
    for e in embedding_data:
        vect_list.append(e.get('embedding'))
    vect_array = np.array(vect_list)

    logger.debug("Reducing dimension...")
    low_dim_embeddings = reduce_dimension(vect_array)

    logger.debug("Clustering...")
    cluster_labels, cluster_centers = cluster(low_dim_embeddings)

    data_summary = get_formatted_data(
        low_dim_embeddings,
        embedding_data,
        cluster_labels,
        cluster_centers
    )

    logger.debug("Saving to DB...")
    save_clustering_to_db(data_summary)