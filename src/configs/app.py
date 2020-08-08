import os


class PulsarConf:
    """
    Configurations for Apache Pulsar message broker
    """
    client = os.getenv("BROKER_SERVICE_URL")
    text_embedding_topic = os.getenv("PULSAR_TEXT_EMBEDDING_TOPIC")
    subscription_name = os.getenv("SUBSCRIPTION_NAME")


class DB:
    """
    Configurations for database engine
    """
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # SQLALCHEMY_DATABASE_URI = 'sqlite:///app.db'
    DB_DRIVER = os.environ.get('DB_DRIVER')
    DB_USER = os.environ.get('DB_USER')
    DB_PASSWORD = os.environ.get('DB_PASSWORD')
    DB_HOST = os.environ.get('DB_HOST')
    DB_PORT = os.environ.get('DB_PORT')
    DB_NAME = os.environ.get('DB_DATABASENAME')

    # SQLALCHEMY_DATABASE_URI =
    # dialect+driver://username:password@host:port/database
    if os.environ.get('SQLALCHEMY_DATABASE_URI'):
        SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    else:
        SQLALCHEMY_DATABASE_URI = f"{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
