import pytest
from random import random
from time import sleep
import json
from uuid import uuid4
from unittest.mock import patch

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


@patch('tasks.base_task.publish_task')
def test_textmap_post(mock_publish_task, client):
    job_id = str(uuid4())
    data = json.dumps({
        "source_urls": [
            "https://www.youtube.com/watch?v=4E29RzEUGrs",
            "https://www.youtube.com/watch?v=pXswr3XmDw8",
            "https://www.youtube.com/watch?v=DHjqpvDnNGE"
        ],
        "user_id": "a_user_id",
        "limit": 200,
        "sequence_id": job_id
    })

    resp = client.post('/textmap', data=data)
    json_data = resp.get_json()
    resp_job_id = json_data['job_id']
    assert resp.status_code == 200
    assert resp_job_id == job_id
    # _cleanup_texts(job_id)
    mock_publish_task.assert_called_once()


def test_status(client):
    resp = client.get('/status')
    assert resp.status_code == 200
