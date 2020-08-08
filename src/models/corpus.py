"""
The database models that deal with
text segments.
"""
from sqlalchemy import Column, Integer, String

from src.models.db import Base


class TextEmbedding(Base):
    __tablename__ = 'text_embeddings'

    id = Column(Integer, primary_key=True)
    uuid = Column(String)
    text = Column(String)
    embedding = Column(String)

    def __repr__(self):
        return "<TextEmbedding(uuid='%s', text='%s', embedding='%s')>" % (
                                self.uuid, self.text, self.embedding)
