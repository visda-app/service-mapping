"""
The database models that deal with
text segments.
"""
import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base

from src.configs.app import DB


print(DB.SQLALCHEMY_DATABASE_URI)

Base = declarative_base()
engine = sqlalchemy.create_engine(
    DB.SQLALCHEMY_DATABASE_URI
)

print(f"sqlalchemy version= {sqlalchemy.__version__}")


from sqlalchemy import Column, Integer, String
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    fullname = Column(String)
    nickname = Column(String)

    def __repr__(self):
        return "<User(name='%s', fullname='%s', nickname='%s')>" % (
                                self.name, self.fullname, self.nickname)


Base.metadata.create_all(engine)
