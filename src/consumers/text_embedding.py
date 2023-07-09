from lib.utils import text_tip
from lib.logger import logger
from models.text import Text as TextModel
from models.db import create_all_tables
from lib.messaging import pull_embeddings_from_queue


create_all_tables()


def consumer_loop():
    """
    Infinite loop. Consume message and write to DB.
    """

    while True:
        embeddings = pull_embeddings_from_queue()
        for item in embeddings:
            try:
                logger.debug(
                    f"uuid={item.uuid}, "
                    f"text='{text_tip(item.text)}' "
                    f"embedding={item.embedding[:1]}... "
                    "Received! 🤓"
                )

                TextModel(
                    id=item.uuid,
                    text=item.text,
                    embedding=item.embedding
                ).save_or_update()

                logger.debug(
                    "✅ Processing the Embedding was successful "
                    f"uuid={item.uuid}, "
                    f"text='{text_tip(item.text)}' "
                    f"embedding={item.embedding}... "
                )

            except Exception as e:
                # Message failed to be processed
                logger.error('❌ message "{}" failed 👎'.format(item.text))
                logger.exception(e)


def main():
    logger.info("🔁 Starting the infinite loop ... ")
    consumer_loop()


main()
