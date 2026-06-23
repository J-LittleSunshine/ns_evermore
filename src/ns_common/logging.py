# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from logging import Formatter, Handler, LogRecord, Logger
from typing import Any, TYPE_CHECKING

from ns_common import ns_config

if TYPE_CHECKING:
    pass

NS_LOGGER_NAME = "ns_evermore"
_NS_LOGGING_CONFIGURED_ATTR = "_ns_evermore_logging_configured"


class NsJsonFormatter(Formatter):
    def format(self, record: LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": self.format_time(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "process": record.process,
            "thread": record.threadName,
            "file": record.filename,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)

    @staticmethod
    def format_time(record: LogRecord) -> str:
        dt = datetime.fromtimestamp(record.created)
        return dt.strftime(ns_config.log.datefmt)


def _normalize_level(level: str) -> int:
    normalized = level.strip().upper()

    return {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "WARN": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
        "FATAL": logging.CRITICAL,
    }.get(normalized, logging.INFO)


def _build_formatter() -> Formatter:
    if ns_config.log.format_type == "json":
        return NsJsonFormatter()

    return Formatter(
        fmt="%(asctime)s - %(levelname)-8s - %(process)d:%(threadName)s - %(name)s - %(filename)s:%(lineno)d - %(message)s",
        datefmt=ns_config.log.datefmt,
    )


def _clear_handlers(logger: Logger) -> None:
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()


def configure_ns_logging(*, force: bool = False) -> None:
    logger = logging.getLogger(NS_LOGGER_NAME)

    if getattr(logger, _NS_LOGGING_CONFIGURED_ATTR, False) and not force:
        return

    if force:
        _clear_handlers(logger)

    level = _normalize_level(ns_config.log.level)

    logger.setLevel(level)
    logger.propagate = False

    if ns_config.log.console:
        console_handler: Handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(_build_formatter())
        logger.addHandler(console_handler)

    setattr(logger, _NS_LOGGING_CONFIGURED_ATTR, True)


def get_logger(name: str | None = None) -> Logger:
    configure_ns_logging()

    if not name:
        return logging.getLogger(NS_LOGGER_NAME)

    if name == NS_LOGGER_NAME or name.startswith(f"{NS_LOGGER_NAME}."):
        return logging.getLogger(name)

    return logging.getLogger(f"{NS_LOGGER_NAME}.{name}")
