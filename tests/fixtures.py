import pytest
import json

from route import app as app
from models.db import create_all_tables
from lib.logger import logger
from models.text import (
    TextEmbedding,
    RawText,
)


@pytest.fixture
def client():
    create_all_tables()

    # seed_db()

    client = app.test_client()
    yield client

    # with app.app_context():
    #     db.session.remove()


def seed_db():
    def write_data_to_db(d, sequence_id):
        uuid = d['uuid']
        # logger.debug(f"Writing data for uuid={uuid}")
        RawText(
            uuid=uuid,
            text=d['text'],
            sequence_id=sequence_id,
        ).save_to_db()
        TextEmbedding(
            uuid=uuid,
            embedding=d['embedding'],
        ).save_to_db()

    # Seeding the tables:
    logger.debug("Loading unlabeled data from file...")
    with open('/code/tests/data/output_1000.json', 'r') as f:
        lines = f.readlines()

    logger.debug("Writing data to DB...")
    for i in range(len(lines)):
        sequence_id = str(i // 300)
        d = json.loads(lines[i])
        write_data_to_db(d, sequence_id)


    # seeding the sentiments
    logger.debug("Loading sentiment data from file and writing to DB...")
    with open('/code/tests/data/labeled_sentiments.json', 'r') as f:
        lines = f.readlines()
    for line in lines:
        d = json.loads(line)
        write_data_to_db(d, 'labeled')
