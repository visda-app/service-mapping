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


class TextEmbedding(Base):
    __tablename__ = 'text_embeddings'

    id = Column(Integer, primary_key=True)
    uuid = Column(String, ForeignKey('raw_texts.uuid'))
    text = Column(Text)
    embedding = Column(ARRAY(Float))

    def __repr__(self):
        return "<TextEmbedding(uuid='%s', text='%s', embedding='%s')>" % (
            self.uuid, self.text, self.embedding
        )

    def save_to_db(self):
        session.add(self)
        session.commit()


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


def load_from_db(sequence_id):
    """load text embeddings by joining tables
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
            'text': text_embedding.text,
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


def load_clustering_from_db(sequence_id):
    q = session.query(
        ClusteredText, RawText
    ).join(
        RawText
    ).filter(
        RawText.sequence_id == sequence_id
    )
    logger.debug(q)
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
