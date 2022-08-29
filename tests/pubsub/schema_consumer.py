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


class TextItem(Record):
    uuid = String(required=True)
    text = String()
    sequence_id = String()


class TextSchema(Record):
    items = Array(TextItem())

schema = AvroSchema(TextSchema)

broker_service_url = PulsarConf.client
client = pulsar.Client(broker_service_url)


_consumer = client.subscribe(
    PulsarConf.text_topic,
    "sub-01",
    consumer_type=_pulsar.ConsumerType.Shared,
    negative_ack_redelivery_delay_ms=500,
    schema=schema
)

def log(msg):
    try:
        # in_text = json.loads(msg.data().decode())
        logger.debug(f"Received message{msg} with data: {msg.data()} ✅")
        for e in msg.value().items:
            logger.debug(f"{e.uuid}, {e.text}")
    except Exception as e:
        # Message failed to be processed
        logger.info("❌ message '{}' 👎".format(msg.data()))
        logger.exception(e)
        # mb.consumer_negative_acknowledge(msg)


while True:
    try:
        msg = _consumer.receive()
        _consumer.acknowledge(msg)
    except KeyboardInterrupt:
        break
    log(msg)


_consumer.close()
