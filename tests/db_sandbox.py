from time import sleep
import json

from lib.logger import logger
from models.db import create_all_tables
from models.text import *
from clusterer import load_cluster_save


logger.info('Creating tables...')
create_all_tables()

# logger.debug('Loading data from db...')
# rv = load_embeddings_from_db(sequence_id='1')

# res = load_cluster_save(sequence_ids=['1'])

# logger.debug("Loading clustering data from DB")
# c_data = load_clustering_from_db('1')
# logger.debug(f"len data= {len(c_data)}")
