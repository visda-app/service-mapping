import pulsar
from pulsar.schema import (
    Record,
    String,
    Array,
    Float,
    AvroSchema,
)
import _pulsar

from src.lib.logger import logger
from src.configs.app import PulsarConf


class TextEmbeddingItem(Record):
    uuid = String(required=True)
    text = String()
    embedding = Array(Float())


class TextEmbeddingSchema(Record):
    items = Array(TextEmbeddingItem())


schema = AvroSchema(TextEmbeddingSchema)

broker_service_url = PulsarConf.client
client = pulsar.Client(broker_service_url)


_consumer = client.subscribe(
    PulsarConf.text_embedding_topic,
    "sub-03",
    consumer_type=_pulsar.ConsumerType.Shared,
    negative_ack_redelivery_delay_ms=500,
    schema=schema
)

def log(msg):
    try:
        # in_text = json.loads(msg.data().decode())
        logger.debug(f"Received message{msg} with data: {msg.data()} ✅")
        for e in msg.value().items:
            logger.debug(f"uuid={e.uuid}, text={e.text}")
    except Exception as e:
        # Message failed to be processed
        logger.info("❌ message '{}' 👎".format(msg.data()))
        logger.exception(e)
        # mb.consumer_negative_acknowledge(msg)


while True:
    try:
        print("Press 'Ctrl + C' to exit")
        msg = _consumer.receive()
        _consumer.acknowledge(msg)
    except KeyboardInterrupt:
        break
    log(msg)


_consumer.close()
