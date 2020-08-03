import time
import tensorflow_hub as hub


from repo.schemas import TextSchema, TextEmbeddingSchema
from lib.utils import text_tip
from lib.logger import logger
from configs.app import (
    PulsarConf,
    PATH_TO_NLP_MODEL
)
from message_broker import MessageBroker, Consumer, Producer


logger.info("⌛ Loading model...")

start_time = time.time()
embed = hub.load(PATH_TO_NLP_MODEL)
logger.info("✅ Model '{}' loaded in ⏱ {:.1f} secs.".format(
    PATH_TO_NLP_MODEL, time.time() - start_time
))

mb = MessageBroker(
    broker_service_url=PulsarConf.client,
    consumer=Consumer(
        PulsarConf.text_topic,
        PulsarConf.subscription_name,
        schema_class=TextSchema
    ),
    producer=Producer(
        PulsarConf.text_embedding_topic,
        schema_class=TextEmbeddingSchema
    )
)

logger.info("🔁 Starting the infinite loop ... ")
while True:
    try:
        msg = mb.consumer_receive()
    except KeyboardInterrupt:
        break
    try:
        embedding = embed([msg.value().text])
        logger.debug(
            f"uuid={msg.value().uuid}, "
            f"text='{text_tip(msg.value().text)}' "
            "was vectorized! 🤓"
        )
        mb.producer_send(
            TextEmbeddingSchema(
                uuid=msg.value().uuid,
                text=msg.value().text,
                embedding=embedding.numpy().tolist()[0]
            )
        )
        mb.consumer_acknowledge(msg)
    except Exception as e:
        # Message failed to be processed
        logger.error('❌ message "{}" failed 👎'.format(msg.value().text))
        logger.exception(e)
        mb.consumer_negative_acknowledge(msg)

mb.close()
