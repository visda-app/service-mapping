import pulsar
from pulsar.schema import (
    Record,
    String,
    Array,
    AvroSchema,
)

from src.configs.app import PulsarConf


class TextItem(Record):
    uuid = String(required=True)
    text = String()
    sequence_id = String()


class TextSchema(Record):
    items = Array(TextItem(), required=True)


schema = AvroSchema(TextSchema)
breakpoint()


broker_service_url = PulsarConf.client
client = pulsar.Client(broker_service_url)

_producer = client.create_producer(
    PulsarConf.text_topic,
    batching_enabled=True,
    batching_max_publish_delay_ms=10,
    schema=schema
)


obj01 = TextItem(
    uuid="4thq3o4t",
    text="a test is here",
    sequence_id="a seq id jq304tu",
)
obj02 = TextItem(
    uuid="8943ty934ty0",
    text="a second test",
    sequence_id="a seq id q0tu",
)
msg = TextSchema(items=[obj01, obj02])

_producer.send(msg)



client.close()
