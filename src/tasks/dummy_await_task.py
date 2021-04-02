from tasks.base_task import BaseTask
from tasks.base_task import record_start_finish_time_in_db
from random import random
from lib.exceptions import ExternalDependencyNotCompleted


class DummyAwaitTask(BaseTask):
    public_description = "Wait for dummy things."

    @record_start_finish_time_in_db
    def execute(self):
        r = random()
        self.record_progress(int(100 * r), 100)
        if r < 0.8:
            raise ExternalDependencyNotCompleted
