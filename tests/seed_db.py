import json

from lib.logger import logger
from models.db import (
    create_all_tables,
    session
)
# Import all the models you want to create tables for
from models.text import Text as TextModel
from models.job import Job


def session_add(session, d, sequence_id):
    uuid = d['uuid']
    # logger.debug(f"Writing data for uuid={uuid}")
    TextModel(
        id=uuid,
        text=d['text'],
        embedding=d['embedding'],
    ).save_or_update()


logger.debug('Creating tables...')
create_all_tables()

# Seeding the tables:
logger.debug("Loading unlabeled data from file...")
with open('/code/tests/data/raw_embedding_1000.json', 'r') as f:
    lines = f.readlines()

logger.debug("Writing data to DB...")
for i in range(len(lines)):
    sequence_id = str(i // 300)
    d = json.loads(lines[i])
    session_add(session, d, sequence_id)


# # seeding the sentiments
# logger.debug("Loading sentiment data from file and writing to DB...")
# with open('/code/tests/data/labeled_sentiments.json', 'r') as f:
#     lines = f.readlines()
# for line in lines:
#     d = json.loads(line)
#     session_add(session, d, 'labeled')
