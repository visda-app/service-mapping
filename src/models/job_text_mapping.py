"""
The database models that deal with
text segments.
"""
from enum import Enum
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
from models.text import Text as TextModel


class TaskStatus(Enum):
    """
    An enum to keep the stage of a job
    """
    started = 10
    done = 20


class JobTextMapping(Base):
    __tablename__ = 'job_text_mappings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String)
    text_id = Column(String)
    status = Column(String)
    time_created = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return "<JobTextRelation(job_id='%s', text_id='%s', status='%s')>" % (
            self.job_id, self.text_id, self.status
        )

    def save_to_db(self):
        session.add(self)
        session.commit()
        return self

    def delete_from_db(self):
        session.query(self.__class__).filter(
            self.__class__.id == self.id
        ).delete()
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
            entry.status = TextTaskStatus.embedded.name
            entry.save_to_db()

    @classmethod
    def _get_unprocessed_texts_query(cls, job_id):
        return session.query(
            cls, TextModel
        ).filter(
            cls.text_id == TextModel.id
        ).filter(
            TextModel.embedding == None
        )

    @classmethod
    def get_unprocessed_texts_count_by_job_id(cls, job_id):
        qu = cls._get_unprocessed_texts_query(job_id)
        result = qu.count()
        return result
