"""
The database models that deal with
text segments.
"""
import json
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ARRAY,
    Float,
    Boolean,
    ForeignKey
)

from models.db import (
    Base,
    session
)
from lib.logger import logger


class RawText(Base):
    __tablename__ = 'raw_texts'

    uuid = Column(String, primary_key=True)
    text = Column(Text)
    sequence_id = Column(String)

    def __repr__(self):
        return "<RawText(uuid='%s', text='%s', sequence_id='%s')>" % (
            self.uuid, self.text, self.sequence_id
        )

    def save_to_db(self):
        session.add(self)
        session.commit()

    def get_count_by_sequence_id(self, sequence_id):
        return session.query(self).filter(
            RawText.sequence_id == sequence_id
        ).count()


class TextEmbedding(Base):
    __tablename__ = 'text_embeddings'

    id = Column(Integer, primary_key=True)
    uuid = Column(String, ForeignKey('raw_texts.uuid'))
    # text = Column(Text)
    embedding = Column(Text)

    def __repr__(self):
        return "<TextEmbedding(uuid='%s', embedding='%s')>" % (
            self.uuid, self.embedding
        )

    def save_to_db(self):
        self.embedding = str(self.embedding)
        session.add(self)
        session.commit()

    def has_same_or_more_seq_count_than_rawtext(self):
        """
        Check if TextEmbedding has same or more entires than RawText
        when compared for the same sequence_id
        """
        q = session.query(RawText).filter(
            RawText.uuid == self.uuid)
        if q.count() > 1:
            raise Exception("More than one record for a uuid!")
        sequence_id = q.first().sequence_id
        if not sequence_id:
            raise Exception('Expected a sequence id!')
        raw_text_count = session.query(RawText).filter(
            RawText.sequence_id == sequence_id
        ).count()
        text_emb_count = session.query(self.__class__).join(RawText).filter(
            RawText.sequence_id == sequence_id
        ).count()
        return text_emb_count >= raw_text_count

    def get_sequence_id(self):
        """
        Get sequence id by joining tables
        """
        return session.query(RawText).filter(
            RawText.uuid == self.uuid
        ).first().sequence_id


class ClusteredText(Base):
    __tablename__ = 'clustered_texts'

    id = Column(Integer, primary_key=True)
    x = Column(Float)
    y = Column(Float)
    uuid = Column(String, ForeignKey('raw_texts.uuid'))
    is_cluster_head = Column(Boolean)
    cluster_label = Column(Integer)

    def __repr__(self):
        return "<ClusteredText(uuid='%s', x='%s', y='%s', cluster_label='%s', is_cluster_head='%s')>" % (
            self.uuid, self.x, self.y, self.cluster_label, self.is_cluster_head
        )


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


def save_clustering_to_db(clustering):
    for c in clustering:
        # Remove if already exists
        session.query(ClusteredText).filter(
            ClusteredText.uuid == c['uuid']
        ).delete()

        session.add(
            ClusteredText(
                x=c['x'],
                y=c['y'],
                uuid=c['uuid'],
                is_cluster_head=c['is_cluster_head'],
                cluster_label=c['cluster_label']
            )
        )
    session.commit()


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


def load_clustering_from_db(sequence_id):
    q = get_query_clustering(sequence_id)
    vals = q.all()

    data = []
    for ct, rt in vals:
        entry = {
            'x': ct.x,
            'y': ct.y,
            'uuid': rt.uuid,
            'text': rt.text,
            'cluster_label': ct.cluster_label,
            'is_cluster_head': ct.is_cluster_head,
        }
        data.append(entry)

    result = sorted(
        data, key=lambda x:
            (x['cluster_label'], not x['is_cluster_head'])
    )
    return result
