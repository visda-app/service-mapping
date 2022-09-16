import logging
import logging.config
import boto3

from configs.app import AWS as aws_configs
from configs.app import Logging as logging_configs


boto3_logs_client = boto3.client(
    'logs',
    aws_access_key_id=aws_configs.access_key_id,
    aws_secret_access_key=aws_configs.secret_access_key,
    region_name=aws_configs.region,
)

service_logger = logging_configs.service_name

d = {
    "version": 1,
    "formatters": {
        "simple": {
            "format": "[%(asctime)s] [%(funcName)s] "
            "[%(levelname)s] - %(message)s"
        },
        "detailed": {
            "format": "[%(asctime)s] [%(levelname)s] "
                      "[%(pathname)s:%(lineno)d] "
                      "%(message)s "
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "stream": "ext://sys.stdout"
        },
        "rotating_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "INFO",
            "formatter": "detailed",
            "filename": "/var/log/service.log",
            "maxBytes": 16777216,
            "backupCount": 10,
            "encoding": "utf8"
        },
        "watchtower": {
            "class": "watchtower.CloudWatchLogHandler",
            "boto3_client": boto3_logs_client,
            "log_group_name": logging_configs.log_group_name,
            # Decrease the verbosity level here to send only those logs to watchtower,
            # but still see more verbose logs in the console. See the watchtower
            # documentation for other parameters that can be set here.
            "level": "DEBUG",
            "send_interval": 5,
            "create_log_group": False,
            "log_stream_name": "{logger_name}/{strftime:%y-%m-%d}",
            "formatter": "detailed",
        },
    },
    "loggers": {
        service_logger: {
            "level": "INFO",
            "handlers": [
                "console", "rotating_file", "watchtower",
            ],
            "propagate": False
        }
    },
    "root": {
        "level": "WARNING",
        "handlers": [
            "console"
        ]
    }
}

logging.config.dictConfig(d)

logger = logging.getLogger(service_logger)
