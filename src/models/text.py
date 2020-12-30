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
from lib.logger import logger


class Text(Base):
    __tablename__ = 'texts'

    text_id = Column(String, primary_key=True)
    text = Column(Text, nullable=False)
    embedding = Column(JSON)

    def __repr__(self):
        return "<Text(uuid='%s', text='%s', embedding='%s')>" % (
            self.text_id, self.text, self.embedding
        )

    def save_or_update(self):
        """
        First search for a record with the given text_id
        if the record exists, it updates the record
        """
        # check if the record exits
        text_id = self.text_id
        record = session.query(self.__class__).filter(
            self.__class__.text_id == text_id
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
        except Exception as e:
            logger.exception(str(e))
            session.rollback()
            raise(ValueError(f"Invalid record for Text model. {self}"))

    @classmethod
    def get_by_id(cls, text_id):
        record = session.query(cls).filter(cls.text_id == text_id).first()
        return record

    @classmethod
    def delete_by_id(cls, text_id):
        session.query(cls).filter(
            cls.text_id == text_id
        ).delete(synchronize_session=False)

    # @classmethod
    # def get_count_by_sequence_id(cls, sequence_id):
    #     return session.query(cls).filter(
    #         cls.sequence_id == sequence_id
    #     ).count()


# class TextEmbedding(Base):
#     __tablename__ = 'text_embeddings'

#     id = Column(Integer, primary_key=True)
#     uuid = Column(String)
#     # uuid = Column(String, ForeignKey('raw_texts.uuid'))
#     # embedding is a list of floats
#     embedding = Column(JSON)

#     def __repr__(self):
#         return "<TextEmbedding(uuid='%s', embedding='%s')>" % (
#             self.uuid, self.embedding
#         )

#     def save_to_db(self):
#         session.add(self)
#         session.commit()

    # @classmethod
    # def get_count_by_sequence_id(cls, sequence_id):
    #     """
    #     Check if TextEmbedding has same or more entires than RawText
    #     when compared for the same sequence_id
    #     """
    #     text_emb_count = session.query(cls).join(RawText).filter(
    #         RawText.sequence_id == sequence_id
    #     ).count()
    #     return text_emb_count

    # def has_same_or_more_seq_count_than_rawtext(self):
    #     """
    #     Check if TextEmbedding has same or more entires than RawText
    #     when compared for the same sequence_id
    #     """
    #     q = session.query(RawText).filter(
    #         RawText.uuid == self.uuid)
    #     if q.count() > 1:
    #         raise Exception("More than one record for a uuid!")
    #     sequence_id = q.first().sequence_id
    #     if not sequence_id:
    #         raise Exception('Expected a sequence id!')

    #     raw_text_count = RawText.get_count_by_sequence_id(sequence_id)
    #     text_emb_count = self.get_count_by_sequence_id(sequence_id)

    #     return text_emb_count >= raw_text_count

    # def get_sequence_id(self):
    #     """
    #     Get sequence id by joining tables
    #     """
    #     return session.query(RawText).filter(
    #         RawText.uuid == self.uuid
    #     ).first().sequence_id


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

    @classmethod
    def get_last_by_sequence_id(cls, sequence_id):
        q = session.query(cls).filter(
            cls.sequence_id == sequence_id
        ).order_by(
            cls.time_created.desc()
        )
        results = q.first()
        return results


def load_embeddings_from_db(sequence_id):
    """
    Load text embeddings by joining tables
    """
    q = session.query(TextEmbedding, RawText).join(
        RawText
    ).filter(
        RawText.sequence_id == sequence_id
    )
    db_vals = q.all()

    results = []

    for (text_embedding, raw_text) in db_vals:
        results.append({
            'embedding': text_embedding.embedding,
            'text': raw_text.text,
            'uuid': text_embedding.uuid,
            'sequence_id': raw_text.sequence_id
        })

    return results


def get_query_clustering(sequence_id):
    q = session.query(
        ClusteredText, RawText
    ).join(
        RawText
    ).filter(
        RawText.sequence_id == sequence_id
    )
    logger.debug(q)
    return q


def get_clustering_count(sequence_id):
    q = get_query_clustering(sequence_id)
    return q.count()


def save_clusterings_to_db(sequence_id, clustering):
    ClusteredText(
        sequence_id=sequence_id,
        clustering=clustering
    ).save_to_db()
