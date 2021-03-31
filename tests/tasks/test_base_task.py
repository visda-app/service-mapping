from tasks.task import Task
from lib.utils import generate_random_job_id
from models.db import create_all_tables
from models.task import Task as TaskModel


create_all_tables()


def test_delete_task():
    t = TaskModel.find_by_id(2)
    t.delete_from_db()


def test_add_task():
    job_id = generate_random_job_id()
    t1 = Task(job_id, "", "")
    assert int(t1.id) > 0
