from lib.logger import logger
from models.db import (
    create_all_tables
)


logger.debug('Creating tables...')
create_all_tables()

def init_tables():
    pass