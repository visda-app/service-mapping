import json
import unittest

from tasks.base_task import BaseTask
from tasks.dummy_task import DummyTask
from tasks.invalid_task import InvalidTask
from lib.utils import generate_random_job_id
from models.db import create_all_tables
from models.task import Task as TaskModel

create_all_tables()


class TestBaseTasks(unittest.TestCase):

    task_ids = []

    def setUp(self):
        pass

    def tearDown(self):
        for id in self.task_ids:
            TaskModel.delete_by_id(id)

    def create_task(self, task_class, kwargs):
        job_id = generate_random_job_id()
        t = task_class(job_id, kwargs)
        self.task_ids.append(t.id)
        return t

    def test_add_task(self):
        kwargs = json.dumps({"a": 1})
        t1 = self.create_task(BaseTask, kwargs)
        t2 = self.create_task(DummyTask, kwargs)
        breakpoint()
        assert int(t1.id) > 0

    def test_add_task__checks_for_execute_function(self):
        kwargs = json.dumps({"a": 1})
        with self.assertRaises(ImportError):
            t1 = self.create_task(InvalidTask, kwargs)
            self.task_ids.append(t1.id)

    def test_add_next(self):
        t1 = self.create_task(BaseTask, json.dumps({'w': 'word'}))
        t2 = self.create_task(BaseTask, json.dumps({'count': 1}))
        t1.add_next(t2)
        t1model = TaskModel.find_by_id(t1.id)
        assert t1model.next_task_id == t2.id

    def test_submit_to_queue(self):
        raise NotImplementedError
