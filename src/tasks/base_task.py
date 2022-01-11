import json
import functools
import time
from datetime import datetime
import pytz

from models.task import Task as TaskModel
from lib.utils import get_module_and_class_from_string
from lib.logger import logger
from lib.messaging import publish_task


TASK_RETRY_DELAY_MS = 1250


class BaseTask:
    """
    The base class for tasks.
    """
    public_description = "Base task"

    def __init__(self, job_id=None, kwargs={}, task_id=None):
        """
        Args:
            kwargs: (dict)
        """
        if type(kwargs) is not dict:
            raise TypeError('Argument `kwargs` must be a dictionary.')
        task = self._get_or_create_task_in_db(
            task_id, job_id, kwargs
        )
        if not task:
            raise ValueError('Invalid task ID.')
        self.id = task.id
        self.job_id = task.job_id
        self.kwargs = json.loads(task.kwargs)
        self.task_class = self._get_full_self_module_and_class_path()
        self.next_task_id = task.next_task_id
        self.progress = task.get_progress()

    def _get_full_self_module_and_class_path(self):
        """
        E.g., tasks.base_task.BaseTask
        """
        return self.__module__ + '.' + self.__class__.__name__

    def _validate_task_class(self, task_class):
        m, c = get_module_and_class_from_string(task_class)
        if 'execute' not in dir(getattr(m, c)):
            raise ImportError('Task class must have an `exectue` function.')

    def _get_or_create_task_in_db(self, task_id, job_id, kwargs):
        if task_id is None:
            task_class = self._get_full_self_module_and_class_path()
            self._validate_task_class(task_class)
            kwargs_json = json.dumps(kwargs)
            task = TaskModel(
                job_id=job_id,
                task_class=task_class,
                kwargs=kwargs_json,
            ).save_to_db()
        else:
            task = TaskModel.get_by_id(task_id)
            if task:
                self._validate_task_class(task.task_class)
            if task and self._get_full_self_module_and_class_path() != task.task_class:
                raise ValueError('Inconsistent task class in DB.')
        return task

    @classmethod
    def load_by_id(cls, task_id):
        task = TaskModel.get_by_id(task_id)
        if task:
            m, c = get_module_and_class_from_string(task.task_class)
            task_class = getattr(m, c)
            return task_class(task_id=task.id)

    def add_next(self, next_task_obj):
        # if not isinstance(next_task_obj, self.__class__):
        #     raise TypeError('Wrong type for task class.')
        current_task = TaskModel.get_by_id(self.id)
        current_task.upsert_next_task(next_task_obj)

    def __rshift__(self, other):
        self.add_next(other)
        return other

    def _submit_to_queue(self, deliver_after_ms=0):
        task = TaskModel.get_by_id(self.id)
        publish_task(
            task.task_class,
            task_kwargs=json.loads(task.kwargs),
            task_id=task.id,
            job_id=task.job_id,
            deliver_after_ms=deliver_after_ms,
        )

    def submit_to_queue(self):
        self._submit_to_queue()

    def start(self):
        self._submit_to_queue()

    def retry_with_delay(self):
        """
        submit self with a delay to be retried
        """
        self._submit_to_queue(deliver_after_ms=TASK_RETRY_DELAY_MS)

    def submit_next_to_queue(self):
        """
        submit next task for execution
        """
        task = self.load_by_id(self.id)
        next_task_id = task.next_task_id
        next_task = self.load_by_id(next_task_id)
        if next_task:
            next_task._submit_to_queue()

    def _get_from_db_by_id(self):
        task_model = TaskModel.get_by_id(self.id)
        if not task_model:
            raise ValueError(f"Could not find task with task_id={self.id}")
        return task_model

    def record_start_time(self, utc_time):
        task_model = self._get_from_db_by_id()
        task_model.save_start_time(utc_time)
        self.started = utc_time

    def record_finish_time(self, utc_time):
        task_model = self._get_from_db_by_id()
        task_model.save_finish_time(utc_time)
        self.finished = utc_time

    def record_progress(self, done, total):
        """
        progress in the form of 56/234
        """
        task_model = self._get_from_db_by_id()
        task_model.save_progress(done, total)
        self.progress = task_model.get_progress()

    def execute(self):
        raise NotImplementedError(
            'This method should be implemented in the derived class.'
        )


def record_start_finish_time_in_db(func):
    @functools.wraps(func)
    def wrapper(self_obj, *args, **kwargs):
        utc_time = datetime.utcnow().replace(tzinfo=pytz.utc)
        self_obj.record_start_time(utc_time)

        result = func(self_obj, *args, **kwargs)

        utc_time = datetime.utcnow().replace(tzinfo=pytz.utc)
        self_obj.record_finish_time(utc_time)

        return result

    return wrapper
