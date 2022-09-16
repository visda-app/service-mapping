import os


class PulsarConf:
    """
    Configurations for Apache Pulsar message broker
    """
    client = os.getenv("BROKER_SERVICE_URL")
    text_topic = os.getenv("PULSAR_TEXT_TOPIC")
    text_embedding_topic = os.getenv("PULSAR_TEXT_EMBEDDING_TOPIC")
    task_topic = os.getenv("PULSAR_TASK_TOPIC")
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
        SQLALCHEMY_DATABASE_URI = f"{DB_DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"  # noqa


class Cache:
    cache_uri = os.environ.get('CACHE_URI')  # e.g., 192.168.59.105:30311
    if cache_uri:
        host = cache_uri.split(':')[0]
        port = cache_uri.split(':')[1]
    else:
        host = os.environ.get('CACHE_HOST')
        port = os.environ.get('CACHE_PORT')


class ThirdParty:
    """
    configurations for the third party apps
    """
    GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')


class AWS:
    access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
    secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
    region = os.environ.get('AWS_REGION')


class Logging:
    log_group_name = os.environ.get('LOG_GROUP_NAME')  # AWS cloud watch log group name
    service_name = os.environ.get('SERVICE_NAME')


k8s_readiness_probe_file = os.getenv('K8S_READINESS_PROBE_FILE')
