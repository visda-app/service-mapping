import json

from models.task import Task as TaskModel
from lib.utils import get_module_and_class_from_string
from lib.messaging import publish_task


TASK_RETRY_DELAY_MS = 2000


class BaseTask:
    """
    The base class for tasks.
    """
    def __init__(self, job_id=None, kwargs={}, task_id=None):
        """
        Args:
            kwargs: (dict)
        """
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
            task = TaskModel.find_by_id(task_id)
            if task:
                self._validate_task_class(task.task_class)
            if task and self._get_full_self_module_and_class_path() != task.task_class:
                raise ValueError('Inconsistent task class in DB.')
        return task

    @classmethod
    def get_by_id(cls, task_id):
        task = TaskModel.find_by_id(task_id)
        if task:
            return cls(task_id=task.id)

    def add_next(self, next_task_obj):
        if not isinstance(next_task_obj, self.__class__):
            raise TypeError('Wrong type for task class.')

        current_task = TaskModel.find_by_id(self.id)
        current_task.upsert_next_task(next_task_obj)

    def submit_next_to_queue(self):
        """
        submit next task for execution
        """
        task = TaskModel.find_by_id(self.id)
        next_task_id = task.next_task_id
        if next_task_id:
            self._submit_to_queue_by_id(next_task_id)

    def _submit_to_queue_by_id(self, id, deliver_after_ms=0):
        task = TaskModel.find_by_id(id)
        publish_task(
            task.task_class,
            [],
            json.loads(task.kwargs),
            task.id,
            deliver_after_ms=deliver_after_ms,
        )

    def submit_to_queue(self):
        self._submit_to_queue_by_id(self.id)

    def retry_with_delay(self):
        """
        submit self with a delay to be retried
        """
        self._submit_to_queue_by_id(
            self.id, deliver_after_ms=TASK_RETRY_DELAY_MS
        )

    def execute(self, *args, **kwargs):
        raise NotImplementedError(
            'This method should be implemented in the derived class.'
        )
