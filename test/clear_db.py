from time import sleep
import json

from src.lib.logger import logger
from src.models.db import (
    engine,
    Base,
    session
)
from src.models.text import (
    TextEmbedding,
    RawText,
    ClusteredText
)


# Base.metadata.create_all(engine)

logger.info('Deleting entries...')
session.query(TextEmbedding).delete()
session.query(ClusteredText).delete()
session.query(RawText).delete()

print(session.query(RawText).count())
print(session.query(TextEmbedding).count())
print(session.query(ClusteredText).count())


# logger.info('Dropping tables...')
# Base.metadata.drop_all(bind=engine, tables=[
#     TextEmbedding.__table__,
#     RawText.__table__,
#     TextMetadata.__table__
# ])
# TextEmbedding.__table__.drop(engine)
# .drop(engine)
# .drop(engine)
