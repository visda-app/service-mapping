from chapar.message_broker import MessageBroker, Consumer
from chapar.schema_repo import TextEmbeddingSchema

from lib.utils import text_tip
from lib.logger import logger
from configs.app import (
    PulsarConf,
)
from models.text import Text as TextModel
from models.db import create_all_tables


create_all_tables()


def consumer_loop(message_broker):
    """
    Infinite loop. Consume message and write to DB.
    """
    mb = message_broker
    while True:
        msg = mb.consumer_receive()
        mb.consumer_acknowledge(msg)
        for item in msg.value().items:
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

            except Exception as e:
                # Message failed to be processed
                logger.error('❌ message "{}" failed 👎'.format(item.text))
                logger.exception(e)


def main():
    logger.info("⌛ Connecting to the message broker...")
    mb = MessageBroker(
        broker_service_url=PulsarConf.client,
        consumer=Consumer(
            PulsarConf.text_embedding_topic,
            PulsarConf.subscription_name,
            schema_class=TextEmbeddingSchema
        ),
    )
    logger.info("✅ Connection to the message broker established.")

    logger.info("🔁 Starting the infinite loop ... ")
    consumer_loop(mb)

    mb.close()


main()
