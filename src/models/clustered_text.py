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
    DateTime
)
from sqlalchemy.dialects.postgresql import (JSONB)

from models.db import (
    Base,
    session
)
from lib.logger import logger


class ClusteredText(Base):
    __tablename__ = 'clustered_texts'

    id = Column(Integer, primary_key=True)
    # a list of sequence id's
    sequence_id = Column(String)
    clustering = Column(JSONB)
    created = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "sequence_id": self.sequence_id,
            "clustering": self.clustering,
            "created": self.created,
        }

    def __repr__(self):
        return (
            "<ClusteredText("
            f"{json.dumps(self.to_dict(), default=str)}"
            ")>"
        )

    def save_to_db(self):
        session.add(self)
        session.commit()
        return self

    @classmethod
    def _get_last_by_sequence_id(cls, sequence_id):
        q = session.query(cls).filter(
            cls.sequence_id == sequence_id
        ).order_by(
            cls.created.desc()
        )
        results = q.first()
        return results

    @classmethod
    def get_last_by_sequence_id(cls, sequence_id):
        results = cls._get_last_by_sequence_id(sequence_id)
        if results:
            return results.clustering

    @classmethod
    def delete_by_sequence_id(cls, sequence_id):
        session.query(cls).filter(
            cls.sequence_id == sequence_id
        ).delete()
        session.commit()
