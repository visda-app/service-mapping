"""
The database models that deal with
text segments.
"""
from copy import deepcopy
from dataclasses import dataclass
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


@dataclass
class TokenItem:
    text: str
    relevance: float


class Text(Base):
    __tablename__ = 'texts'

    id = Column(String, primary_key=True)
    text = Column(Text, nullable=False, index=True)
    embedding = Column(Text)
    tokens = Column(Text)
    created = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id": self.id,
            "text": self.text,
            "embedding": self.embedding,
            "tokens": self.tokens,
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

        if self.embedding and type(self.embedding) is not str:
            serialized_embedding = json.dumps(self.embedding)
            self.embedding = serialized_embedding

        if self.tokens and type(self.tokens) is not str:
            serialized_tokens = json.dumps(self.tokens)
            self.tokens = serialized_tokens

        if record:
            if self.embedding:
                record.embedding = self.embedding
            if self.text:
                record.text = self.text
            if self.tokens:
                record.tokens = self.tokens
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
        record_copy = deepcopy(record)
        if record_copy and record_copy.embedding:
            record_copy.embedding = json.loads(record_copy.embedding)
        if record_copy and record_copy.tokens:
            record_copy.tokens = json.loads(record_copy.tokens)
        return record_copy

    @classmethod
    def get_embedding_by_text(cls, text):
        record = session.query(cls).filter(cls.text == text).first()
        deserialized_embedding = None
        if record and record.embedding:
            deserialized_embedding = json.loads(record.embedding)
        return deserialized_embedding

    @classmethod
    def delete_by_id(cls, text_id):
        session.query(cls).filter(
            cls.id == text_id
        ).delete(synchronize_session=False)
        session.commit()
