import json

from models.task import Task as TaskModel
from lib.utils import get_module_and_class_from_string
from lib.messaging import publish_task


class BaseTask:
    """
    The base class for tasks.
    """
    def __init__(self, job_id, kwargs):
        task_class = self.__module__ + '.' + self.__class__.__name__
        self._validate_task_class(task_class)
        task = TaskModel(
            job_id=job_id,
            task_class=task_class,
            kwargs=kwargs,
        ).save_to_db()
        self.id = task.id

    def _validate_task_class(self, task_class):
        m, c = get_module_and_class_from_string(task_class)
        if 'execute' not in dir(getattr(m, c)):
            raise ImportError('Invalid Tasks class.')

    def add_next(self, next_task_obj):
        if not isinstance(next_task_obj, self.__class__):
            raise TypeError('Wrong type for task class.')

        current_task = TaskModel.find_by_id(self.id)
        current_task.upsert_next_task(next_task_obj)

    def _submit_next_to_queue(self):
        """
        submit next task for execution
        """
        pass

    def _retry_with_delay(self, delay_ms=0):
        """
        submit self with a delay to be retried
        """
        pass

    def submit_to_queue(self):
        task = TaskModel.find_by_id(self.id)
        publish_task(
            task.task_class,
            [],
            json.loads(task.kwargs),
            task.id
        )

    def execute(self, *args, **kwargs):
        raise NotImplementedError(
            'This method should be implemented in the derived class.'
        )
