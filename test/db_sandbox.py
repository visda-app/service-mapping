from time import sleep
import json

from src.lib.logger import logger
from src.models.db import (
    engine,
    Base,
    session
)
from src.models.text import (
    TextEmbedding,
    RawText,
    ClusteredText,
    load_from_db,
    load_clustering_from_db
)
from src.clusterer import load_cluster_save


logger.info('Creating tables...')
Base.metadata.create_all(engine)

logger.debug('Loading data from db...')
rv = load_from_db(sequence_id='1')

# res = load_cluster_save(sequence_ids=['1'])

logger.debug("Loading clustering data from DB")
c_data = load_clustering_from_db('1')
