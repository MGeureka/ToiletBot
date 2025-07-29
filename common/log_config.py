import logging
from logging.config import dictConfig
import pathlib

BASE_DIR = pathlib.Path(__file__).parent.parent

LOGS_DIR = BASE_DIR / "logs"

LOGGING_CONFIG = {
    "version": 1,
    "disabled_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "%(levelname)-10s - %(asctime)s - %(module)-15s : %(message)s"
        },
        "standard": {"format": "%(levelname)-10s - %(name)-15s : %(message)s"},
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "console2": {
            "level": "WARNING",
            "class": "logging.StreamHandler",
            "formatter": "standard",
        },
        "BOT_LOG": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": f"{LOGS_DIR}/bot_log.log",
            "mode": "w",
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        "SCH_LOG": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": f"{LOGS_DIR}/sch_log.log",
            "mode": "w",
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        "DB_LOG": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": f"{LOGS_DIR}/db_log.log",
            "mode": "w",
            "formatter": "verbose",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "bot": {
            "handlers": ["BOT_LOG"],
            "level": "DEBUG",
            "propagate": False
        },
        "discord": {
            "handlers": ["BOT_LOG"],
            "level": "INFO",
            "propagate": False,
        },
        "sch": {
            "handlers": ["SCH_LOG"],
            "level": "DEBUG",
            "propagate": False
        },
        "db": {
            "handlers": ["DB_LOG"],
            "level": "DEBUG",
            "propagate": False
        },
    },
}

dictConfig(LOGGING_CONFIG)
