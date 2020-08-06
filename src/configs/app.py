import os


class PulsarConf:
    """
    Configurations for Apache Pulsar message broker
    """
    client = os.getenv("BROKER_SERVICE_URL")
    text_embedding_topic = os.getenv("PULSAR_TEXT_EMBEDDING_TOPIC")
    subscription_name = os.getenv("SUBSCRIPTION_NAME")
