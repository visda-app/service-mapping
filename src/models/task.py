"""
The database models that deal with
text segments.
"""
import json
from uuid import uuid4
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


class Task(Base):
    __tablename__ = 'tasks'

    id = Column(String, primary_key=True)
    job_id = Column(String)
    task_class = Column(String)
    kwargs = Column(JSON)
    next_task_id = Column(String)
    events = Column(JSON)
    created = Column(DateTime(timezone=True), server_default=func.now())
    started = Column(DateTime(timezone=True))
    finished = Column(DateTime(timezone=True))
    progress = Column(String)

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "task_class": self.task_class,
            "kwargs": self.kwargs,
            "next_task_id": self.next_task_id,
            "events": self.events,
            "created": self.created,
            "started": self.started,
            "finished": self.finished,
            "progress": self.get_progress(),
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
    def get_by_id(cls, id):
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
        next_task = self.__class__.get_by_id(next_task_obj.id)
        self.next_task_id = next_task.id
        self.save_to_db()

    # def load_self_from_db(self):
    #     record = session.query(self).filter(
    #         self.__class__.id == self.id
    #     ).first()
    #     return record

    def save_start_time(self, utc_time):
        if self.started is None:
            self.started = utc_time
            self.save_to_db()

    def save_finish_time(self, utc_time):
        self.finished = utc_time
        self.save_to_db()

    def save_progress(self, done, total):
        int(done)
        int(total)
        self.progress = f"{done}/{total}"
        self.save_to_db()

    def get_progress(self):
        progress = self.progress
        if progress:
            done = int(progress.split('/')[0])
            total = int(progress.split('/')[1])
        else:
            done = 0
            total = 0
        return {'done': done, 'total': total}

    def append_an_event(self, event):
        """
        self.event is a list
        """
        if self.events is None:
            self.events = []
        events = list(self.events)
        events.append(event)
        self.events = events
        self.save_to_db()
        return self

    def get_events(self):
        events = []
        if self.events:
            events = list(self.events)
        return events
