import sqlalchemy
from sqlalchemy.ext.declarative import declarative_base

from src.configs.app import DB


engine = sqlalchemy.create_engine(
    DB.SQLALCHEMY_DATABASE_URI
)
Base = declarative_base()
