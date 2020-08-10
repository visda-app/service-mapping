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
)


def session_add(session, d, sequence_id):
    uuid = d['uuid']
    # logger.debug(f"Wrting data for uuid={uuid}")
    session.add(
        RawText(
            uuid=uuid,
            text=d['text'],
            sequence_id=sequence_id,
        ),
    )
    session.commit()
    session.add(
        TextEmbedding(
            uuid=uuid,
            text=d['text'],
            embedding=d['embedding'],
        )
    )
    session.commit()



logger.debug('Creating tables...')
Base.metadata.create_all(engine)

# Seeding the tables:
logger.debug("Loading unlabeled data from file...")
with open('/code/tmp/output_1000.json', 'r') as f:
    lines = f.readlines()

logger.debug("Writing data to DB...")
for i in range(len(lines)):
    sequence_id = str(i // 300)
    d = json.loads(lines[i])
    session_add(session, d, sequence_id)


# seeding the sentiments
logger.debug("Loading sentiment data from file and writing to DB...")
with open('/code/tmp/labeled_sentiments.json', 'r') as f:
    lines = f.readlines()
for line in lines:
    d = json.loads(line)
    session_add(session, d, 'labeled')
