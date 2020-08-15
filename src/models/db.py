import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from configs.app import DB


engine = sqlalchemy.create_engine(
    DB.SQLALCHEMY_DATABASE_URI
)
Base = declarative_base()

Session = sessionmaker(bind=engine)
session = Session()


def create_all_tables():
    Base.metadata.create_all(engine)
