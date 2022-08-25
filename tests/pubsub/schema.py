import pulsar
from pulsar.schema import (
    Record,
    String,
    Array,
    Float,
    AvroSchema,
)

from src.configs.app import PulsarConf


class TextItem(Record):
    uuid = String(required=True)
    text = String()
    sequence_id = String()


class TextEmbeddingItem(Record):
    uuid = String(required=True)
    text = String()
    embedding = Array(Float())


class TextSchema(Record):
    items = Array(TextItem)


class TextEmbeddingSchema(Record):
    items = Array(TextEmbeddingItem())


class TaskSchema(Record):
    task_class = String(required=True)
    task_id = String()
    job_id = String()
    args = String()
    kwargs = String()

schema = AvroSchema(TextItem)

breakpoint()


broker_service_url = PulsarConf.client
client = pulsar.Client(broker_service_url)


_producer = client.create_producer(
    'apache/pulsar/text-topic',
    batching_enabled=True,
    batching_max_publish_delay_ms=10,
    schema=schema
)


