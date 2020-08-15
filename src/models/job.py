"""
The database models that deal with
text segments.
"""
import enum
from sqlalchemy import (
    Column,
    Integer,
    String,
    Enum,
)

from models.db import (
    Base,
    session
)


class JobStatus(enum.Enum):
    """
    An enum to keep the stage of a job
    """
    created = 1
    raw_text_received = 2
    embeddings_done = 3
    clustering_done = 4
    done = 5


class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String)
    subtask_count = Column(Integer)
    status = Column(Enum(JobStatus))

    def __repr__(self):
        return "<Job(job_id='%s', subtask_count='%s', status='%s')>" % (
            self.job_id, self.subtask_count, self.status
        )

    def save_to_db(self):
        session.add(self)
        session.commit()
