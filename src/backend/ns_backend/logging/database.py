# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Callable

from ns_backend.logging.django import get_django_logger
from ns_common.logging import NsLogEvent, NsLogEventData, sanitize_log_context
from ns_common.logging.database import DatabaseLogSink


class DjangoDatabaseLogSink(DatabaseLogSink):
    """Django-side database sink skeleton for structured log events.

    This class intentionally does not use ORM models or create tables.
    A concrete writer callable can be injected later when a storage model exists.
    """

    _DISALLOWED_CONTEXT_KEYS = {
        "request_data",
        "request_body",
        "payload",
        "raw_payload",
    }

    def __init__(
        self,
        *,
        enabled: bool = False,
        writer: Callable[[dict[str, Any]], None] | None = None,
        fallback_to_logger: bool = True,
        fallback_log_name: str = "ns_backend.db_sink",
        component: str = "ns_backend",
    ):
        self._enabled = bool(enabled)
        self._writer = writer
        self._fallback_logger = (
            get_django_logger(log_name=fallback_log_name, component=component)
            if fallback_to_logger
            else None
        )
        self._in_fallback = False

    @staticmethod
    def _coerce_bool(value: Any, default: bool = False) -> bool:
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "y", "on"}:
                return True
            if normalized in {"0", "false", "no", "n", "off"}:
                return False

        if isinstance(value, int):
            if value == 1:
                return True
            if value == 0:
                return False

        return default

    @classmethod
    def from_settings(
        cls,
        *,
        writer: Callable[[dict[str, Any]], None] | None = None,
    ) -> DjangoDatabaseLogSink:
        from django.conf import settings

        config = getattr(settings, "NS_LOGGING", None)
        if not isinstance(config, dict):
            config = {}

        db_sink = config.get("db_sink", {})
        if not isinstance(db_sink, dict):
            db_sink = {}

        return cls(
            enabled=cls._coerce_bool(db_sink.get("enabled"), default=False),
            writer=writer,
            fallback_to_logger=cls._coerce_bool(db_sink.get("fallback_to_logger"), default=True),
            fallback_log_name=str(db_sink.get("fallback_log_name") or "ns_backend.db_sink"),
            component=str(config.get("component") or "ns_backend"),
        )

    @property
    def enabled(self) -> bool:
        return self._enabled

    def _build_payload(self, event: NsLogEventData) -> dict[str, Any]:
        context = dict(event.context or {})
        for key in self._DISALLOWED_CONTEXT_KEYS:
            context.pop(key, None)

        payload: dict[str, Any] = {
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
            "pid": event.pid,
            "context": sanitize_log_context(context),
        }
        return {key: value for key, value in payload.items() if value is not None}

    def _fallback(self, event_payload: dict[str, Any], exc: Exception) -> None:
        if self._fallback_logger is None or self._in_fallback:
            return

        self._in_fallback = True
        try:
            self._fallback_logger.error(
                "%s",
                {
                    "event": NsLogEvent.DATABASE_LOG_SINK_FAILED,
                    "message": "database sink emit failed",
                    "level": "ERROR",
                    "context": {
                        "original_event": event_payload.get("event"),
                        "error_type": exc.__class__.__name__,
                    },
                },
                exc_info=True,
            )
        except Exception:  # noqa
            pass
        finally:
            self._in_fallback = False

    def emit(self, event: NsLogEventData) -> None:
        if not self._enabled:
            return

        if self._writer is None:
            return

        payload = self._build_payload(event)
        try:
            self._writer(payload)
        except Exception as exc:  # noqa
            self._fallback(payload, exc)


__all__ = ["DjangoDatabaseLogSink"]

