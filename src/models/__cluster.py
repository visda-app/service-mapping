"""
The database models that deal with
text segments.
"""
from sqlalchemy.sql import func
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime
)
from sqlalchemy.dialects.postgresql import JSONB
from models.db import (
    Base,
    session
)


class Cluster(Base):
    __tablename__ = 'clusters'

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
