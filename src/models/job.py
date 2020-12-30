"""
The database models that deal with
text segments.
"""
import enum
from sqlalchemy.sql import func
from sqlalchemy import (
    Column,
    Integer,
    String,
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
    started = 10
    raw_text_received = 20
    third_party_data_acquired = 25
    embeddings_done = 30
    mapping_started = 40
    dimension_reduction_started = 50
    clustering_started = 60
    clustering_done = 70
    breaking_down_large_clusters = 80
    formatting_data = 90
    mapping_done = 100
    saving_to_db = 110
    done = 120


class TextTaskStatus(enum.Enum):
    """
    An enum to keep the progress on a particular text
    """
    embedded = 10


class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String)  # same as sequence_id
    status = Column(String)
    num_items = Column(String)
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
        )._save_to_db()


class JobTextRelation(Base):
    __tablename__ = 'job_text_relations'

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String)
    text_id = Column(String)
    status = Column(String)
    time_created = Column(DateTime(timezone=True), server_default=func.now())

    def save_to_db(self):
        session.add(self)
        session.commit()

    @classmethod
    def find_by_id(cls, job_id, text_id):
        records = session.query(cls).filter(
            cls.text_id == text_id
            and cls.job_id == job_id
        ).all()
        return list(records)

    @classmethod
    def update_status_by_text_id(cls, text_id):
        """
        Find the records with a particular text_id and
        update the status for all of them to processed
        aka embedded
        """
        records = session.query(cls).filter(
            cls.text_id == text_id
        ).all()

        for entry in records:
            entry.status = TextTaskStatus.embedded
            entry.save_to_db()
