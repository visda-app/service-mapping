import json
from uuid import uuid4
import unittest
from unittest.mock import patch

from tasks.base_task import BaseTask
from tasks.base_task import TASK_RETRY_DELAY_MS
from tasks.dummy_task import DummyTask
from lib.utils import generate_random_job_id
from models.db import create_all_tables
from models.task import Task as TaskModel
from invalid_task import InvalidTask
from lib.utils import get_module_and_class_from_string

create_all_tables()


class TestBaseTasks(unittest.TestCase):

    task_ids = []

    def setUp(self):
        pass

    def tearDown(self):
        for id in self.task_ids:
            TaskModel.delete_by_id(id)

    def create_task(self, task_class, kwargs, job_id=None):
        if job_id is None:
            job_id = generate_random_job_id()
        t = task_class(job_id=job_id, kwargs=kwargs)
        self.task_ids.append(t.id)
        return t

    def test___init___add_task(self):
        kwargs = {"a": 1}
        t1 = self.create_task(BaseTask, kwargs)
        t2 = self.create_task(DummyTask, kwargs)

        t1model = TaskModel.find_by_id(t1.id)
        assert t1model.task_class == 'tasks.base_task.BaseTask'

        t2model = TaskModel.find_by_id(t2.id)
        assert t2model.task_class == 'tasks.dummy_task.DummyTask'

    def test___init___load_task(self):
        kwargs = {"a": 1}
        t1 = self.create_task(BaseTask, kwargs)
        task_id = t1.id
        task_class = t1.task_class

        m, c = get_module_and_class_from_string(task_class)
        t_class = getattr(m, c)
        t_obj = t_class(task_id=task_id)

        assert t_obj.id == task_id

    def test___init___load_task_raises(self):
        task_id = str(uuid4())

        with self.assertRaises(ValueError):
            BaseTask(task_id=task_id)

    def _test_add_task__checks_for_execute_function(self):
        kwargs = {"a": 1}
        with self.assertRaises(ImportError):
            t1 = self.create_task(InvalidTask, kwargs)
            self.task_ids.append(t1.id)

    def test_add_next(self):
        t1 = self.create_task(BaseTask, {'w': 'word'})
        t2 = self.create_task(BaseTask, {'count': 1})
        t1.add_next(t2)
        t1model = TaskModel.find_by_id(t1.id)
        assert t1model.next_task_id == t2.id

    @patch('tasks.base_task.publish_task')
    def test_submit_to_queue(self, mock_publish_task):
        kwargs = {"pub": "sub"}
        t = self.create_task(BaseTask, kwargs)
        task_id = t.id
        t.submit_to_queue()
        mock_publish_task.assert_called_with(
            'tasks.base_task.BaseTask',
            task_kwargs=kwargs,
            task_id=task_id,
            job_id=t.job_id,
            deliver_after_ms=0,
        )

    @patch('tasks.base_task.publish_task')
    def test_submit_next_to_queue(self, mock_publish_task):
        job_id = '123'
        t1 = self.create_task(
            BaseTask,
            {'arg1': 1, '2': 'two'},
            job_id
        )
        t2 = self.create_task(
            DummyTask,
            {'arg2': 2, '3': 'three'},
            job_id
        )
        t1.add_next(t2)
        t1.submit_next_to_queue()
        mock_publish_task.assert_called_with(
            'tasks.dummy_task.DummyTask',
            task_kwargs={'arg2': 2, '3': 'three'},
            task_id=t2.id,
            job_id=job_id,
            deliver_after_ms=0,
        )

    @patch('tasks.base_task.publish_task')
    def test_submit_next_to_queue__no_next_task(self, mock_publish_task):
        job_id = '123'
        t1 = self.create_task(
            BaseTask,
            {'arg1': 1, '2': 'two'},
            job_id
        )
        t1.submit_next_to_queue()
        mock_publish_task.assert_not_called()

    @patch('tasks.base_task.publish_task')
    def test_retry_with_delay(self, mock_publish_task):
        kwargs = {"pub1": "sub2"}
        t = self.create_task(BaseTask, kwargs)
        task_id = t.id
        t.retry_with_delay()
        mock_publish_task.assert_called_with(
            'tasks.base_task.BaseTask',
            task_kwargs=kwargs,
            task_id=task_id,
            job_id=t.job_id,
            deliver_after_ms=TASK_RETRY_DELAY_MS,
        )

    def test_get_by_id(self):
        job_id = '345'
        t1 = self.create_task(
            BaseTask,
            {'arg1': 1, '2': 'two'},
            job_id
        )
        task_id = t1.id

        t = BaseTask.get_by_id(task_id)

        assert t.id == task_id
        assert t.kwargs == {'arg1': 1, '2': 'two'}
        assert t.job_id == job_id
