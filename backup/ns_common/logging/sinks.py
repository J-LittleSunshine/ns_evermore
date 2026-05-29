# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import os
from typing import Protocol

from ns_common.logging.event import NsLogEventData
from ns_common.logging.sanitizer import sanitize_log_context


class NsLogSink(Protocol):
    def emit(self, event: NsLogEventData) -> None:
        ...


class DatabaseLogSinkProtocol(Protocol):
    """Database sink contract to be implemented outside ns_common.

    ORM-backed sinks should live in ns_backend or concrete application modules.
    """

    def emit(self, event: NsLogEventData) -> None:
        ...


class NullLogSink:
    def emit(self, event: NsLogEventData) -> None:
        return None


class StdLoggerSink:
    _ALLOWED_LEVELS = {"debug", "info", "warning", "error", "critical"}

    def __init__(self, logger: logging.Logger):
        self._logger = logger

    @staticmethod
    def _resolve_level(level: str) -> str:
        normalized = str(level or "").strip().lower()
        if normalized in StdLoggerSink._ALLOWED_LEVELS:
            return normalized
        return "info"

    @staticmethod
    def _build_payload(event: NsLogEventData) -> dict[str, object]:
        payload: dict[str, object] = {
            "event": event.event,
            "message": event.message,
            "component": event.component,
            "log_name": event.log_name,
            "trace_id": event.trace_id,
            "request_id": event.request_id,
            "connection_id": event.connection_id,
            "user_id": event.user_id,
            "session_id": event.session_id,
            "error_code": event.error_code,
            "level": event.level,
            "pid": event.pid or os.getpid(),
            "context": sanitize_log_context(event.context or {}),
        }
        return {key: value for key, value in payload.items() if value is not None}

    def emit(self, event: NsLogEventData) -> None:
        try:
            payload = self._build_payload(event)
            method_name = self._resolve_level(event.level)
            log_method = getattr(self._logger, method_name, self._logger.info)
            log_method("%s", payload)
        except Exception:  # noqa
            # Sink failures must never break caller flow.
            pass


__all__ = ["NsLogSink", "DatabaseLogSinkProtocol", "NullLogSink", "StdLoggerSink"]

