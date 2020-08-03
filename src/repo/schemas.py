from pulsar.schema import (
    Record,
    String,
    Array,
    Float,
)

class TextEmbeddingSchema(Record):
    uuid = String()
    text = String()
    embedding = Array(Float())
