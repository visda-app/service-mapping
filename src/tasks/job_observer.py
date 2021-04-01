import json
from models.task import Task as TaskModel


class JobObserver:
    """
    """
    @classmethod
    def get_job_details(self, job_id):
        return TaskModel.get_by_job_id(job_id)
