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
    Boolean,
    Float,
    ForeignKey,
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
from models.job import JobTextRelation
from lib.logger import logger


class Text(Base):
    __tablename__ = 'texts'

    id = Column(String, primary_key=True)
    text = Column(Text, nullable=False)
    embedding = Column(JSON)

    def __repr__(self):
        return "<Text(id='%s', text='%s', embedding='%s')>" % (
            self.id, self.text, self.embedding
        )

    def save_or_update(self):
        """
        First search for a record with the given text_id
        if the record exists, it updates the record
        """
        # check if the record exits
        text_id = self.id
        record = session.query(self.__class__).filter(
            self.__class__.id == text_id
        ).first()

        if record:
            if self.embedding:
                record.embedding = self.embedding
            if self.text:
                record.text = self.text
        else:
            session.add(self)

        try:
            session.commit()
            return self
        except Exception as e:
            logger.exception(str(e))
            session.rollback()
            raise(ValueError(f"Invalid record for Text model. {self}"))

    def delete_from_db(self):
        session.query(self.__class__).filter(
            self.__class__.id == self.id
        ).delete()
        session.commit()

    @classmethod
    def get_by_id(cls, text_id):
        record = session.query(cls).filter(cls.id == text_id).first()
        return record

    @classmethod
    def delete_by_id(cls, text_id):
        session.query(cls).filter(
            cls.id == text_id
        ).delete(synchronize_session=False)


class ClusteredText(Base):
    __tablename__ = 'clustered_texts'

    id = Column(Integer, primary_key=True)
    # a list of sequence id's
    sequence_id = Column(String)
    clustering = Column(JSONB)
    time_created = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return "<ClusteredText(sequence_id='%s', clustering='%s')>" % (  # noqa
                self.sequence_id, self.clustering)

    def save_to_db(self):
        session.add(self)
        session.commit()
        return self

    @classmethod
    def get_last_by_sequence_id(cls, sequence_id):
        q = session.query(cls).filter(
            cls.sequence_id == sequence_id
        ).order_by(
            cls.time_created.desc()
        )
        results = q.first()
        return results


def load_embeddings_from_db(job_id):
    q = session.query(Text, JobTextRelation).filter(
        Text.id == JobTextRelation.text_id
    ).filter(
        JobTextRelation.job_id == job_id
    )
    db_vals = q.all()

    results = []

    for (text, job_text_relation) in db_vals:
        results.append({
            'embedding': text.embedding,
            'text': text.text,
            'uuid': text.id,
            'sequence_id': job_id
        })

    return results


def _get_query_clustering(job_id):
    q = session.query(Text, JobTextRelation).filter(
        Text.id == JobTextRelation.text_id
    ).filter(
        JobTextRelation.job_id == job_id
    )
    logger.debug(q)
    return q


def get_clustering_count(sequence_id):
    q = _get_query_clustering(sequence_id)
    return q.count()


def save_clusterings_to_db(sequence_id, clustering):
    ClusteredText(
        sequence_id=sequence_id,
        clustering=clustering
    ).save_to_db()
