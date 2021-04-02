"""
The database models that deal with
text segments.
"""
import json
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


class JobTextMapping(Base):
    __tablename__ = 'job_text_mappings'

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String)
    text_id = Column(String)
    created = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            'id': self.id,
            'job_id': self.job_id,
            'text_id': self.text_id,
            'created': self.created,
        }

    def __repr__(self):
        return (
            "<Task("
            f"{json.dumps(self.to_dict(), default=str)}"
            ")>"
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
