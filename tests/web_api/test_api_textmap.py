import pytest
from random import random
from time import sleep

from lib.logger import logger
from models.db import create_all_tables
from route import app as flask_app


@pytest.fixture
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client


logger.info('Creating tables...')
create_all_tables()


def _cleanup_texts(job_id):
    from models.job_text_mapping import JobTextMapping
    sleep(15)
    JobTextMapping.delete_texts_by_job_id(job_id)


def test_textmap_post(client):
    data = {
        'youtube_video_id': 'oieNTzEeeX0',
        'sequence_id': str(int(1000 * random()))
    }

    resp = client.post('/textmap', data=data)
    json_data = resp.get_json()
    job_id = json_data['job_id']
    assert resp.status_code == 200
    # _cleanup_texts(job_id)


def test_status(client):
    resp = client.get('/status')
    assert resp.status_code == 200
