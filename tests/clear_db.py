from time import sleep
import json
from time import sleep

from lib.logger import logger
from models.db import (
    engine,
    Base,
    session
)
from models.text import (
    TextEmbedding,
    RawText,
    ClusteredText
)


# Base.metadata.create_all(engine)

logger.info('Deleting entries...')
session.query(TextEmbedding).delete(synchronize_session=False)
# session.query(ClusteredText).delete(synchronize_session=False)
session.query(RawText).delete(synchronize_session=False)

print(session.query(RawText).count())
print(session.query(TextEmbedding).count())
# print(session.query(ClusteredText).count())


# logger.info('Dropping tables...')
# Base.metadata.drop_all(bind=engine, tables=[
#     TextEmbedding.__table__,
#     RawText.__table__,
#     TextMetadata.__table__
# ])
# TextEmbedding.__table__.drop(engine)
# .drop(engine)
# .drop(engine)
