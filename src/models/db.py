import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.configs.app import DB
from src.lib.logger import logger


engine = sqlalchemy.create_engine(
    DB.SQLALCHEMY_DATABASE_URI
)
Base = declarative_base()

Session = sessionmaker(bind=engine)
session = Session()

