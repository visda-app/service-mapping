import json
from uuid import uuid4
import unittest
from unittest.mock import patch
from unittest import TestCase
from datetime import timedelta
from copy import deepcopy

from tasks.base_task import BaseTask
from tasks.base_task import TASK_RETRY_DELAY_MS
from tasks.dummy_task import DummyTask
from tasks.dummy_task import DUMMY_TASK_EXEC_TIME
from lib.utils import generate_random_id
from models.db import create_all_tables
from models.task import Task as TaskModel
from invalid_task import InvalidTask
from lib.utils import get_module_and_class_from_string
from tasks import event_collection

create_all_tables()


class TestBaseTask(TestCase):

    task_ids = []

    def setUp(self):
        pass

    def tearDown(self):
        for id in self.task_ids:
            TaskModel.delete_by_id(id)

    def create_task(self, task_class, kwargs, job_id=None):
        if job_id is None:
            job_id = generate_random_id()
        t = task_class(job_id=job_id, kwargs=kwargs)
        self.task_ids.append(t.id)
        return t

    def test___init___add_task(self):
        kwargs = {"a": 1}
        t1 = self.create_task(BaseTask, kwargs)
        t2 = self.create_task(DummyTask, kwargs)

        t1model = TaskModel.get_by_id(t1.id)
        assert t1model.task_class == 'tasks.base_task.BaseTask'

        t2model = TaskModel.get_by_id(t2.id)
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

    @unittest.skip('')
    def test_add_task__checks_for_execute_function(self):
        kwargs = {"a": 1}
        with self.assertRaises(ImportError):
            t1 = self.create_task(InvalidTask, kwargs)
            self.task_ids.append(t1.id)

    def test_add_next(self):
        t1 = self.create_task(BaseTask, {'w': 'word'})
        t2 = self.create_task(BaseTask, {'count': 1})
        t1.add_next(t2)
        t1model = TaskModel.get_by_id(t1.id)
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

        t = BaseTask.load_by_id(task_id)

        assert t.id == task_id
        assert t.kwargs == {'arg1': 1, '2': 'two'}
        assert t.job_id == job_id

    def test_record_start_finish_time(self):
        job_id = '002'
        t1 = self.create_task(
            DummyTask,
            {'a': 1},
            job_id
        )
        from datetime import datetime
        from datetime import timedelta
        import pytz

        utc_time = (
            datetime.utcnow().replace(tzinfo=pytz.utc)
            + timedelta(minutes=3, seconds=11)
        )
        t1.record_start_time(utc_time)
        t1model = TaskModel.get_by_id(t1.id)
        assert t1model.started == utc_time

        utc_time = (
            datetime.utcnow().replace(tzinfo=pytz.utc)
            + timedelta(minutes=7, seconds=34)
        )
        t1.record_finish_time(utc_time)
        t1model = TaskModel.get_by_id(t1.id)
        assert t1model.finished == utc_time

    def test_record_time(self):
        job_id = '001'
        t1 = self.create_task(
            DummyTask,
            {'a': 1},
            job_id
        )
        t1.execute()
        assert (
            t1.finished - t1.started
            > timedelta(seconds=DUMMY_TASK_EXEC_TIME)
        )

    def test_record_progress(self):
        job_id = '234'
        t1 = self.create_task(
            DummyTask,
            {'b': 2},
            job_id
        )
        t1.record_progress(4, 5)
        assert t1.progress == {'done': 4, 'total': 5}

    def test__append_event(self):
        job_id = "345"
        t = self.create_task(
            DummyTask,
            {'b': 3},
            job_id,
        )

        result = t.get_events()
        assert result == []

        test_event_msg_01 = "a test event"
        t._append_event(test_event_msg_01)
        result = t.get_events()
        assert result == [
            test_event_msg_01
        ]

        test_event_msg_02 = "another event"
        t._append_event(test_event_msg_02)
        result = t.get_events()
        assert result == [
            test_event_msg_01,
            test_event_msg_02
        ]

        test_event_msg_03 = 1234
        t._append_event(test_event_msg_03)
        result = t.get_events()
        assert result == [
            test_event_msg_01,
            test_event_msg_02,
            test_event_msg_03,
        ]


    def test__append_a_dict_event(self):
        job_id = "345"
        t = self.create_task(
            DummyTask,
            {'b': 3},
            job_id,
        )

        test_events = []
        test_events.append({
            "key": "a_unique_key",
            "description": "a description to know what this was about",
            "params": {
                "num_resp": 32,
                "success": True,
                "message": "201 success"
            }
        })
        test_events.append("a simple text")

        for e in test_events:
            t._append_event(e)

        result = t.get_events()
        assert result == test_events

    @patch('tasks.base_task.BaseTask._get_current_timestamp')
    def test_append_event(self, dummy_timestamp):
        job_id = "345"
        t = self.create_task(
            DummyTask,
            {'b': 3},
            job_id,
        )
        a_timestamp = 3984357.45
        dummy_timestamp.return_value = a_timestamp
        expected_result = [
            {
                'event_lookup_key': 'dummy_event_lookup_key',
                'timestamp': a_timestamp,
                'description': 'This is a dummy lookup key for testing',
                'args': {
                    'test1': 'one two three',
                    'test2': 123
                },
            },
        ]

        t.append_event(event_lookup_key='dummy_event_lookup_key')
        result = t.get_events()

        assert result == expected_result

    @patch('tasks.base_task.BaseTask._get_current_timestamp')
    def test_append_event_with_args(self, dummy_timestamp):
        job_id = "345"
        t = self.create_task(
            DummyTask,
            {'b': 3},
            job_id,
        )
        a_timestamp = 3984357.45
        dummy_timestamp.return_value = a_timestamp
        expected_result = [
            {
                'event_lookup_key': 'dummy_event_lookup_key',
                'timestamp': a_timestamp,
                'description': 'This is a dummy lookup key for testing',
                'args': {
                    'test1': 'one two three',
                    'test2': 123,
                    'arg1': 'test_arg1',
                    'arg2': 23456,
                },
            },
        ]

        t.append_event(
            event_lookup_key='dummy_event_lookup_key',
            arg1="test_arg1",
            arg2=23456,
        )
        result = t.get_events()

        assert result == expected_result


    def test_append_event_raises(self):
        job_id = "345"
        t = self.create_task(
            DummyTask,
            {'b': 3},
            job_id,
        )

        with TestCase().assertRaises(ValueError) as e:
            t.append_event(event_lookup_key='TEST_invalid_event_lookup_key')
