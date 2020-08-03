from src.lib.logger import logger
from src.message_broker import MessageBroker, Consumer
from src.configs.app import PulsarConf
import pulsar, _pulsar
import json
from src.repo.schemas import TextEmbeddingSchema



mb = MessageBroker(
    broker_service_url=PulsarConf.client,
    consumer=Consumer(
        PulsarConf.text_embedding_topic, "sub-02",
        schema_class=TextEmbeddingSchema
    )
)


while True:
    try:
        msg = mb.consumer_receive()
    except KeyboardInterrupt:
        break
    try:
        logger.debug(
            f"uuid={msg.value().uuid}, text={msg.value().text}, embedding={msg.value().embedding} ✅"
        )
        mb.consumer_acknowledge(msg)
    except Exception as e:
        # Message failed to be processed
        logger.info("❌ message '{}' 👎".format(msg.data()))
        logger.exception(e)
        # mb.consumer_negative_acknowledge(msg)
    mb.consumer_acknowledge(msg)

mb.close()
