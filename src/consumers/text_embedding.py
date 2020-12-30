import json
from chapar.message_broker import MessageBroker, Consumer
from chapar.schema_repo import TextEmbeddingSchema

from lib.utils import text_tip
from lib.logger import logger
from configs.app import (
    PulsarConf,
)
from models.text import TextEmbedding
from models.job import JobTextRelation
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
        try:
            text_id = msg.value().uuid
            logger.debug(
                f"uuid={text_id}, "
                f"text='{text_tip(msg.value().text)}' "
                f"embedding='{msg.value().embedding}'"
                "Received! 🤓"
            )

            txt_emb = TextEmbedding(
                uuid=text_id,
                embedding=msg.value().embedding
            )
            txt_emb.save_to_db()
            JobTextRelation.update_status_by_text_id(text_id)

            # if txt_emb.has_same_or_more_seq_count_than_rawtext():
            #     publish_clustering_task(txt_emb)

        except Exception as e:
            # Message failed to be processed
            logger.error('❌ message "{}" failed 👎'.format(msg.value().text))
            logger.exception(e)
            mb.consumer_negative_acknowledge(msg)


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
