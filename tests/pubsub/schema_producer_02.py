import pulsar
from pulsar.schema import (
    Record,
    String,
    Array,
    Float,
    AvroSchema,
)

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

_producer = client.create_producer(
    PulsarConf.text_embedding_topic,
    batching_enabled=True,
    batching_max_publish_delay_ms=10,
    schema=schema
)


obj01 = TextEmbeddingItem(
    uuid="qut3qgohog",
    text="-=< test embedding >=-",
    embedding=[1.0, 1.3],
)
obj02 = TextEmbeddingItem(
    uuid="q4t9theog",
    text="-=< another text to test embedding >=-",
    embedding=[1.0, 1.3],
)
msg = TextEmbeddingSchema(items=[obj01, obj02])




_producer.send(msg)

client.close()
