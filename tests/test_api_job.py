from fixtures import client
from lib.logger import logger
from models.db import create_all_tables


logger.info('Creating tables...')
create_all_tables()


def test_job_create(client):
    data = {
        'text': 'some text'
    }

    resp = client.post('/job', data=data)
    json_data = resp.get_json()
    assert resp.status_code == 200


def test_job_status(client):
    pass