from time import sleep

from src.lib.logger import logger
from src.models.db import engine
from src.models.db import Base
from src.models.corpus import TextEmbedding



logger.info('Creating tables...')
Base.metadata.create_all(engine)

logger.debug(TextEmbedding.__table__)

new_embedding = TextEmbedding(
    uuid='a unique id',
    text='some text here',
    embedding='[1.0, 3.1, 0.01]'
)

TextEmbedding.save_to_db()
