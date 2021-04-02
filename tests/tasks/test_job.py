import unittest
from unittest.mock import patch
import pprint
import datetime
import psycopg2
from random import random

from tasks.dummy_task import DummyTask
from tasks.dummy_await_task import DummyAwaitTask
from lib.utils import generate_random_job_id
from models.db import create_all_tables
from models.task import Task as TaskModel
from tasks.job_auditor import JobAuditor


create_all_tables()
pp = pprint.PrettyPrinter(indent=4).pprint
UNORDERED_TASKS = [
    {
        'created': datetime.datetime(
            2021, 4, 1, 17, 24, 54, 781161,
            tzinfo=psycopg2.tz.FixedOffsetTimezone(offset=0, name=None)
        ),
        'finished': None,
        'id': 'ce0310a4-2cb8-4ac6-a019-46bc897fd6be',
        'job_id': 'random_job_id_123',
        'kwargs': '{"arg3": 3}',
        'next_task_id': None,
        'progress': None,
        'started': None,
        'task_class': 'tasks.dummy_task.DummyTask'
    },
    {
        'created': datetime.datetime(
            2021, 4, 1, 17, 24, 54, 771610,
            tzinfo=psycopg2.tz.FixedOffsetTimezone(offset=0, name=None)
        ),
        'finished': None,
        'id': '8e83a9a1-3f9b-4ffb-bbb1-455fb3385792',
        'job_id': 'random_job_id_123',
        'kwargs': '{"arg1": 1}',
        'next_task_id': 'c12a1ea0-24ec-4091-957f-498176c39565',
        'progress': None,
        'started': None,
        'task_class': 'tasks.dummy_task.DummyTask'
    },
    {
        'created': datetime.datetime(
            2021, 4, 1, 17, 24, 54, 775470,
            tzinfo=psycopg2.tz.FixedOffsetTimezone(offset=0, name=None)
        ),
        'finished': None,
        'id': 'c12a1ea0-24ec-4091-957f-498176c39565',
        'job_id': 'random_job_id_123',
        'kwargs': '{"arg2": 2}',
        'next_task_id': 'ce0310a4-2cb8-4ac6-a019-46bc897fd6be',
        'progress': None,
        'started': None,
        'task_class': 'tasks.dummy_await_task.DummyAwaitTask'
    }
]


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

    def test__get_ordered_tasks(self):
        tasks = [
            {
                'id': '1',
                'next_task_id': None,
            },
            {
                'id': '2',
                'next_task_id': '1',
            },
            {
                'id': '3',
                'next_task_id': '4',
            },
            {
                'id': '4',
                'next_task_id': '2',
            },
        ]
        actual_results = JobAuditor()._get_ordered_tasks(tasks)
        expected_results = [
            {
                'id': '3',
                'next_task_id': '4',
            },
            {
                'id': '4',
                'next_task_id': '2',
            },
            {
                'id': '2',
                'next_task_id': '1',
            },
            {
                'id': '1',
                'next_task_id': None,
            },
        ]
        assert actual_results == expected_results

    def test__get_ordered_tasks_raises_no_head(self):
        tasks = [
            {
                'id': '1',
                'next_task_id': '3',
            },
            {
                'id': '2',
                'next_task_id': '1',
            },
            {
                'id': '3',
                'next_task_id': '2',
            },
        ]
        with self.assertRaises(ValueError):
            JobAuditor()._get_ordered_tasks(tasks)

    def test__get_ordered_tasks_raises_more_than_one_head(self):
        tasks = [
            {
                'id': '1',
                'next_task_id': None,
            },
            {
                'id': '2',
                'next_task_id': '1',
            },
            {
                'id': '3',
                'next_task_id': '1',
            },
        ]
        with self.assertRaises(ValueError):
            JobAuditor()._get_ordered_tasks(tasks)

    @patch('tasks.base_task.publish_task')
    def test_get_job_details(self, mock_publish_task):
        job_id = str(int(random() * 100))

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

        res = JobAuditor.get_job_details(job_id)
        breakpoint()

        assert res[0]['id'] == t1.id
        assert res[1]['id'] == t2.id
        assert res[2]['id'] == t3.id

        assert res[0]['description'] == t1.public_description
        assert res[1]['description'] == t2.public_description
        assert res[2]['description'] == t3.public_description
