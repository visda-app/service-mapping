from time import sleep
import json

from lib.logger import logger
from models.db import (
    engine,
    Base,
    session
)
from models.text import (
    TextEmbedding,
    RawText,
    ClusteredText,
    load_from_db,
    load_clustering_from_db
)
from clusterer import load_cluster_save


logger.info('Creating tables...')
Base.metadata.create_all(engine)

logger.debug('Loading data from db...')
rv = load_from_db(sequence_id='1')

import pdb; pdb.set_trace()

res = load_cluster_save(sequence_ids=['1'])

logger.debug("Loading clustering data from DB")
c_data = load_clustering_from_db('1')
logger.debug(f"len data= {len(c_data)}")
