import json
from chapar.message_broker import MessageBroker, Consumer
from chapar.schema_repo import TextEmbeddingSchema

from lib.utils import text_tip
from lib.logger import logger
from configs.app import (
    PulsarConf,
)
from models.text import (
    TextEmbedding,
    RawText
)
from clusterer import load_cluster_save


def start_next_task(text_embedding):
    """
    Start the next task, dimension reduction and clustering.
    """
    sequence_id = text_embedding.get_sequence_id()
    load_cluster_save([sequence_id])


def consumer_loop(message_broker):
    """
    Infinite loop. Consume message, write to DB, and
    trigger next action if all records have been received.
    """
    mb = message_broker
    while True:
        try:
            msg = mb.consumer_receive()
        except KeyboardInterrupt:
            break
        try:
            logger.debug(
                f"uuid={msg.value().uuid}, "
                f"text='{text_tip(msg.value().text)}' "
                f"embedding='{msg.value().embedding}'"
                "Received! 🤓"
            )
            txt_emb = TextEmbedding(
                uuid=msg.value().uuid,
                embedding=msg.value().embedding
            )
            txt_emb.save_to_db()
            if txt_emb.has_same_or_more_seq_count_than_rawtext():
                start_next_task(txt_emb)

            mb.consumer_acknowledge(msg)
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
