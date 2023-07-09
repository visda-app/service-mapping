import time
from lib.utils import text_tip
from lib.logger import logger
from models.text import Text as TextModel
from models.db import create_all_tables
from lib.messaging import (
    pull_raw_texts_from_queue,
    publish_text_for_embedding,
)


EMPTY_QUEUE_SLEEP_TIME_SEC = 1

create_all_tables()

logger.info("🔁 Starting the infinite loop ... ")
while True:
    raw_texts = pull_raw_texts_from_queue()

    if not raw_texts:
        time.sleep(EMPTY_QUEUE_SLEEP_TIME_SEC)

    for item in raw_texts:
        try:
            logger.debug(
                f"uuid={item.uuid}, "
                f"text='{text_tip(item.text)}' "
                f"sequence_id='{item.sequence_id}' "
                "Received! 🤓"
            )
            text_record = TextModel(
                id=item.uuid,
                text=item.text,
            ).save_or_update()

            publish_text_for_embedding(item)

        except Exception as e:
            # Message failed to be processed
            logger.error(
                "❌ message failed 👎"
                f"uuid={item.uuid}, "
                f"text='{text_tip(item.text)}' "
            )
            logger.exception(e)
