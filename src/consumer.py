import time
import json
from chapar.message_broker import MessageBroker, Consumer, Producer
from chapar.schema_repo import TextEmbeddingSchema

from lib.utils import text_tip
from lib.logger import logger
from configs.app import (
    PulsarConf,
)


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

logger.info("Opening the output file...")
FILE_NAME = "tmp/output.json"


logger.info("🔁 Starting the infinite loop ... ")
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
        with open(FILE_NAME, "a") as f:
            f.write(json.dumps(
                {
                    'uuid': msg.value().uuid,
                    'text': msg.value().text,
                    'embedding': msg.value().embedding
                }
            ))
            f.write('\n')

        mb.consumer_acknowledge(msg)
    except Exception as e:
        # Message failed to be processed
        logger.error('❌ message "{}" failed 👎'.format(msg.value().text))
        logger.exception(e)
        mb.consumer_negative_acknowledge(msg)

mb.close()
