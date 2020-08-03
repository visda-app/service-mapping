import pulsar
from pulsar.schema import AvroSchema
import _pulsar


CONSUMER = 'consumer'
PRODUCER = 'producer'


class Consumer:
    def __init__(self, topic, subscription_name, schema_class=None):
        self.topic = topic
        self.subscription_name = subscription_name
        self.schema_class = schema_class


class Producer:
    def __init__(self, topic, schema_class=None):
        self.topic = topic
        self.schema_class = schema_class


class MessageBroker:
    """
    An interface for the message broker service.
    In this case, the message broker is Apache Pulsar
    """
    def __init__(
        self,
        broker_service_url=None,
        consumer=None,
        producer=None,
    ):
        self._consumer = None
        self._producer = None

        if consumer and type(consumer) is not Consumer:
            raise TypeError('Input should be of type Consumer')
        if producer and type(producer) is not Producer:
            raise TypeError('Input should be of type Producer')

        self.client = pulsar.Client(broker_service_url)

        if consumer:
            self._consumer = self.client.subscribe(
                consumer.topic,
                consumer.subscription_name,
                consumer_type=_pulsar.ConsumerType.Shared,
                negative_ack_redelivery_delay_ms=500,
                schema=AvroSchema(consumer.schema_class)
            )

        if producer:
            self._producer = self.client.create_producer(
                producer.topic,
                schema=AvroSchema(producer.schema_class)
            )

    def consumer_receive(self):
        return self._consumer.receive()

    def consumer_acknowledge(self, msg):
        return self._consumer.acknowledge(msg)

    def consumer_negative_acknowledge(self, msg):
        self._consumer.negative_acknowledge(msg)

    def producer_send(self, msg):
        self._producer.send(msg)

    def close(self):
        self.client.close()
