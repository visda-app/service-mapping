from models.task import Task as TaskModel


class Task:
    """
    The base class for tasks.
    """
    def __init__(self, job_id, task_class, kwargs):
        self._validate_task_class(task_class)
        task = TaskModel(
            job_id=job_id,
            task_class=task_class,
            kwargs=kwargs,
        )
        saved_task = task.save_to_db()
        self.id = saved_task.id

    def _validate_task_class(self, task_class):
        pass

    def add_next(self, next_task_id):
        next_task = TaskModel.find_by_id(next_task_id)
        if not next_task:
            raise IndexError('task_id do not exist in DB.')
        

    def _submit_next(self):
        """
        submit next task for execution
        """
        pass

    def retry_with_delay(self, delay_ms=0):
        """
        submit self with a delay to be retried
        """
        pass

    def submit_to_queue(self):
        pass

    def execute(self, *args, **kwargs):
        raise NotImplementedError(
            'This method should be implemented in the derived class.'
        )
