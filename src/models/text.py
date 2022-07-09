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
    Text,
    DateTime
)
from sqlalchemy.dialects.postgresql import (
    JSON,
    JSONB
)

from models.db import (
    Base,
    session
)
from lib.logger import logger


class Text(Base):
    __tablename__ = 'texts'

    id = Column(String, primary_key=True)
    text = Column(Text, nullable=False, index=True)
    embedding = Column(Text)
    created = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "embedding": self.embedding,
            "created": self.created,
        }

    def __repr__(self):
        return (
            "<Text("
            f"{json.dumps(self.to_dict(), default=str)}"
            ")>"
        )

    def save_or_update(self):
        """
        First search for a record with the given text_id
        if the record exists, it updates the record
        """
        # check if the record exits
        text_id = self.id
        record = session.query(self.__class__).filter(
            self.__class__.id == text_id).first()

        if self.embedding:
            self.embedding = json.dumps(self.embedding)
        if record:
            if self.embedding:
                record.embedding = self.embedding
            if self.text:
                record.text = self.text
        else:
            record = self

        try:
            session.add(record)
            session.commit()
            return record
        except Exception as e:
            logger.exception(str(e))
            session.rollback()
            raise(ValueError(f"Invalid record for Text model. {self}"))

    def delete_from_db(self):
        session.query(self.__class__).filter(
            self.__class__.id == self.id
        ).delete(synchronize_session=False)
        session.commit()

    @classmethod
    def get_by_id(cls, text_id):
        record = session.query(cls).filter(cls.id == text_id).first()
        if record and record.embedding:
            record.embedding = json.loads(record.embedding)
        return record

    @classmethod
    def get_embedding_by_text(cls, text):
        record = session.query(cls).filter(cls.text == text).first()
        if record and record.embedding:
            record.embedding = json.loads(record.embedding)
            return record

    @classmethod
    def delete_by_id(cls, text_id):
        session.query(cls).filter(
            cls.id == text_id
        ).delete(synchronize_session=False)
        session.commit()
