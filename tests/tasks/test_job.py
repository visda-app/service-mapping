import unittest
from unittest.mock import patch
import pprint

from tasks.dummy_task import DummyTask
from tasks.dummy_await_task import DummyAwaitTask
from lib.utils import generate_random_job_id
from models.db import create_all_tables
from models.task import Task as TaskModel
from tasks.job_observer import JobObserver


create_all_tables()
pp = pprint.PrettyPrinter(indent=4).pprint


class TestJob(unittest.TestCase):
    task_ids = []

    def setUp(self):
        pass

    def tearDown(self):
        for id in self.task_ids:
            TaskModel.delete_by_id(id)

    def create_task(self, task_class, job_id=None, kwargs={}):
        if job_id is None:
            job_id = generate_random_job_id()
        t = task_class(job_id=job_id, kwargs=kwargs)
        self.task_ids.append(t.id)
        return t

    @patch('tasks.base_task.publish_task')
    def test_get_job_details(self, mock_publish_task):
        job_id = 'random_job_id_123'

        t1 = self.create_task(
            DummyTask,
            job_id=job_id,
            kwargs={'arg1': 1},
        )
        t2 = self.create_task(
            DummyAwaitTask,
            job_id=job_id,
            kwargs={'arg2': 2},
        )
        t3 = self.create_task(
            DummyTask,
            job_id=job_id,
            kwargs={'arg3': 3},
        )
        t1.add_next(t2)
        t2.add_next(t3)
        # t1.submit_to_queue()

        result = JobObserver.get_job_details(job_id)
        breakpoint()
