from models.task import Task as TaskModel
from lib.utils import get_class_from_string


class JobAuditor:
    """
    """
    def _find_head(self, tasks):
        heads = []
        tails = {
            task['next_task_id'] for task in tasks if 'next_task_id' in task
        }
        for task in tasks:
            if task['id'] not in tails:
                heads.append(task)
        if len(heads) != 1:
            raise ValueError('Circular chain?')
        return heads[0]

    def _find_next(self, tasks, target_task):
        next_tasks = []
        for task in tasks:
            if task['id'] == target_task['next_task_id']:
                next_tasks.append(task)
        if len(next_tasks) > 1:
            raise ValueError('More than one next task')
        if len(next_tasks) == 1:
            return next_tasks[0]

    def _get_ordered_tasks(self, tasks):
        if not tasks or len(tasks) == 0:
            return []
        head = self._find_head(tasks)
        ordered_tasks = [head]
        next = self._find_next(tasks, ordered_tasks[-1])
        while next:
            ordered_tasks.append(next)
            next = self._find_next(tasks, ordered_tasks[-1])
        return ordered_tasks

    def _insert_task_public_description(self, tasks):
        for task in tasks:
            task_class = get_class_from_string(task['task_class'])
            if task_class and 'public_description' in dir(task_class):
                task['description'] = task_class.public_description

    @classmethod
    def get_job_details(cls, job_id):
        tasks_ = TaskModel.get_by_job_id(job_id)
        ordered_tasks = cls()._get_ordered_tasks(tasks_)
        cls()._insert_task_public_description(ordered_tasks)
        return ordered_tasks
