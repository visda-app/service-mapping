import logging
import logging.config


service_logger = "service_logger"

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
    },
    "loggers": {
        service_logger: {
            "level": "DEBUG",
            "handlers": [
                "console", "rotating_file"
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
