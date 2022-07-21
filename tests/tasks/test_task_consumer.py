import unittest
from random import random
from unittest.mock import patch

from tasks.dummy_task import DummyTask
from tasks.dummy_await_task import DummyAwaitTask
from lib.utils import generate_random_id
from models.db import create_all_tables


create_all_tables()



@patch('tasks.base_task.publish_task')
def test_submit_to_queue(mock_publish):
    job_id = str(int(100 * random()))  # generate_random_id()

    t1 = DummyTask(
        job_id=job_id,
        kwargs={'arg1': 1},
    )
    t2 = DummyAwaitTask(
        job_id=job_id,
        kwargs={'arg2': 2},
    )
    t3 = DummyTask(
        job_id=job_id,
        kwargs={'arg3': 3},
    )
    t1.add_next(t2)
    t2.add_next(t3)
    t1.submit_to_queue()

    mock_publish.assert_called_once()
