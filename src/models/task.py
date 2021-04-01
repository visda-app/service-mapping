"""
The database models that deal with
text segments.
"""
import json
from uuid import uuid4
from enum import Enum
from sqlalchemy.sql import func
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
)
from sqlalchemy.dialects.postgresql import JSON

from models.db import (
    Base,
    session
)
# from models.text import Text as TextModel


class TaskStatus(Enum):
    """
    An enum to keep the stage of a job
    """
    started = 10
    done = 20


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(String, primary_key=True)
    job_id = Column(String)
    task_class = Column(String)
    kwargs = Column(JSON)
    next_task_id = Column(String)
    created = Column(DateTime(timezone=True), server_default=func.now())
    started = Column(DateTime(timezone=True))
    finished = Column(DateTime(timezone=True))
    progress = Column(Integer)

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "task_class": self.task_class,
            "kwargs": self.kwargs,
            "next_task_id": self.next_task_id,
            "created": self.created,
            "started": self.started,
            "finished": self.finished,
            "progress": self.progress,
        }

    def __repr__(self):
        return (
            "<Task("
            f"{json.dumps(self.to_dict(), default=str)}"
            ")>"
        )

    def save_to_db(self):
        if not self.id:
            self.id = str(uuid4())
        session.add(self)
        session.commit()
        return self

    @classmethod
    def find_by_id(cls, id):
        q = session.query(cls).filter(cls.id == id)
        return q.first()

    @classmethod
    def get_by_job_id(cls, job_id):
        tasks = session.query(cls).filter(
            cls.job_id == job_id
        ).all()
        return [
            t.to_dict() for t in tasks
        ]

    @classmethod
    def delete_by_id(cls, id):
        q = session.query(cls).filter(
            cls.id == id
        )
        ret_val = [e.to_dict() for e in q.all()]
        q.delete(synchronize_session=False)
        session.commit()
        return ret_val

    def upsert_next_task(self, next_task_obj):
        next_task = self.__class__.find_by_id(next_task_obj.id)
        self.next_task_id = next_task.id
        self.save_to_db()

    def load_self_from_db(self):
        record = session.query(self).filter(
            self.__class__.id == self.id
        ).first()
        return record

    def record_start_time(self):
        time = func.now()
        record = self.load_self_from_db()
        record.started = time
        record.save_to_db()

    def record_finish_time(self):
        time = func.now()
        record = self.load_self_from_db()
        record.finished = time
        record.save_to_db()

    def get_progress(self):
        pass

    @classmethod
    def log_status(cls, job_id, status, num_items=None):
        """
        Add an entry to the table with the latest
        job status

        Parameters
        ----------
            job_id : str
                A unique identifier for the job or sequence id
            status : JobStatus
                A status structure
            num_items: int
                The number of items or tasks in the job

        Returns
        -------
            self
        """
        if type(status) is not JobStatus:
            raise ValueError('status must be of type JobStatus')

        return cls(
            job_id=job_id,
            status=status.name,
            num_items=num_items
        ).save_to_db()
