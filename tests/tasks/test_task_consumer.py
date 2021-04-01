import unittest
import pytest

from tasks.base_task import BaseTask
from tasks.dummy_task import DummyTask
from tasks.dummy_await_task import DummyAwaitTask
from lib.utils import generate_random_job_id
from models.db import create_all_tables


create_all_tables()


class TestTaskConsumer(unittest.TestCase):

    task_ids = []

    def setUp(self):
        pass

    def create_task(self, task_class, kwargs, job_id=None):
        if job_id is None:
            job_id = generate_random_job_id()
        t = task_class(job_id=job_id, kwargs=kwargs)
        self.task_ids.append(t.id)
        return t

    def test_submit_to_queue(self):
        job_id = 123

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
