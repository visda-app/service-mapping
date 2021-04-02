from time import sleep
from tasks.base_task import BaseTask
from tasks.base_task import record_start_finish_time_in_db


DUMMY_TASK_EXEC_TIME = 0.25


class DummyTask(BaseTask):
    public_description = "Do dumb things."

    @record_start_finish_time_in_db
    def execute(self):
        sleep(DUMMY_TASK_EXEC_TIME)
