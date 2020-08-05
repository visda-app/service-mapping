import json
import time
import numpy as np
from sklearn.manifold import TSNE
from sklearn.cluster import AffinityPropagation
import matplotlib.pyplot as plt

from lib.logger import logger


def load_embeddings():
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
    FILE_NAME = "/code/tmp/output_1000.json"
    with open(FILE_NAME, 'r') as f:
        lines = f.readlines()
    embedding_data = []
    for line in lines:
        embedding_data.append(json.loads(line))
    vect_list = []
    for e in embedding_data:
        vect_list.append(e.get('embedding'))
    vect_array = np.array(vect_list)
    return embedding_data, vect_array


def reduce_dimension(x):
    """
    Reduce the dimension of the input vector
    Arg:
        x (numpy.array): a list of lists containing vectors.
    Retrun:
        (numpy.array): reduced dimension
    """
    low_dim_x = TSNE(n_components=2, learning_rate=200, perplexity=30).fit_transform(x)
    return low_dim_x


def cluster(x):
    """
    Clusters data
    """
    clustering = AffinityPropagation(random_state=5, damping=0.95).fit(x)

    cluster_labels = clustering.labels_
    cluster_centers = clustering.cluster_centers_
    return cluster_labels, cluster_centers


start_time = time.time()

embedding_data, embedding_vectors = load_embeddings()
logger.debug(f"Finished reading file at t={time.time() - start_time} sec")

low_dim_embeddings = reduce_dimension(embedding_vectors)
logger.info(f"Finished t-SNE at t={time.time() - start_time} sec")

cluster_labels, cluster_centers = cluster(low_dim_embeddings)
logger.info(f"Finished clustering at t={time.time() - start_time} sec")


summary = []
for i in range(len(embedding_data)):
    entry = {
        'x': str(low_dim_embeddings[i, 0]),
        'y': str(low_dim_embeddings[i, 1]),
        'uuid': embedding_data[i].get('uuid'),
        'text': embedding_data[i].get('text'),
        'cluster_label': int(cluster_labels[i]),
        'is_cluster_head': low_dim_embeddings[i, :] in cluster_centers
    }
    summary.append(entry)
result = sorted(summary, key=lambda x: (x['cluster_label'], not x['is_cluster_head']))


FILE_NAME_CLUSTERED = "/code/tmp/output_clustered.json"

with open(FILE_NAME_CLUSTERED, 'w') as f:
    f.write(json.dumps(result, indent=4))
