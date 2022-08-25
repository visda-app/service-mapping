import random
import time
from chapar.message_broker import MessageBroker, Consumer, Producer
from chapar.schema_repo import TextSchema, TextEmbeddingSchema

from lib.logger import logger
from configs.app import PulsarConf


logger.info("⌛ Connecting to the message broker...")
mb = MessageBroker(
    broker_service_url=PulsarConf.client,
    consumer=Consumer(
        PulsarConf.text_topic,
        'mock_embedding_svc',
        schema_class=TextSchema
    ),
    producer=Producer(
        PulsarConf.text_embedding_topic,
        schema_class=TextEmbeddingSchema
    )
)
logger.info("✅ Connection to the message broker established.")

logger.info("🔁 Starting the infinite loop ... ")
while True:
    msg = mb.consumer_receive()
    try:
        embedding = [random.random() for i in range(3)]
        time.sleep(0.05)
        logger.debug(
            f"uuid={msg.value().uuid}, "
            f"text='{msg.value().text}' "
            "was vectorized! 🤓"
        )
        mb.producer_send_async(
            TextEmbeddingSchema(
                uuid=msg.value().uuid,
                text=msg.value().text,
                embedding=embedding
            )
        )
        mb.consumer_acknowledge(msg)
    except Exception as e:
        # Message failed to be processed
        logger.error('❌ message "{}" failed 👎'.format(msg.value().text))
        logger.exception(e)
        mb.consumer_negative_acknowledge(msg)

mb.close()
