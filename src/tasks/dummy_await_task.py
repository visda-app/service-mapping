from tasks.base_task import BaseTask
from random import random


class DummyAwaitTask(BaseTask):
    def execute(self):
        if random() > 0.75:
            return True
