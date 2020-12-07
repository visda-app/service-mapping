"""
The database models that deal with
text segments.
"""
import enum
import datetime
from sqlalchemy.sql import func
from sqlalchemy import (
    Column,
    Integer,
    String,
    Enum,
    DateTime,
)

from models.db import (
    Base,
    session
)


class JobStatus(enum.Enum):
    """
    An enum to keep the stage of a job
    """
    started = 1
    raw_text_received = 2
    embeddings_done = 3
    mapping_started = 4
    dimension_reduction_started = 5
    clustering_started = 10
    clustering_done = 11
    breaking_down_large_clusters = 12
    formatting_data = 13
    mapping_done = 20
    saving_to_db = 30
    done = 31


class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String)  # same as sequence_id
    status = Column(String)
    time_created = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return "<Job(job_id='%s', status='%s')>" % (
            self.job_id, self.status
        )

    def _save_to_db(self):
        session.add(self)
        session.commit()

    @classmethod
    def get_latest_status(cls, job_id):
        latest_status = session.query(cls).filter(
            cls.job_id == job_id
        ).order_by(cls.time_created.desc()).first()
        if latest_status:
            return latest_status.status

    @classmethod
    def log_status(cls, job_id, status):
        """
        Add an entry to the table with the latest
        job status

        Parameters
        ----------
            job_id : str
                A unique identifier for the job or sequence id
            status : JobStatus
                A status structure

        Returns
        -------
            self
        """
        if type(status) is not JobStatus:
            raise ValueError('status must be of type JobStatus')

        return cls(job_id=job_id, status=status.name)._save_to_db()
