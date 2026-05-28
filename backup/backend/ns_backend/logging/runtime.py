# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from ns_backend.logging.django import get_django_logger
from ns_common.logging import NsLogEventData, build_log_context, get_current_pid


def _normalize_level(level: str | None) -> str:
    normalized = str(level or "").strip().upper()
    return normalized or "ERROR"


def short_identifier(value: str | None, edge: int = 8) -> str | None:
    if not isinstance(value, str):
        return None

    normalized = value.strip()
    if not normalized:
        return None

    if len(normalized) <= edge * 2:
        return normalized

    return f"{normalized[:edge]}...{normalized[-edge:]}"


def emit_log_event(
    *,
    event: str,
    message: str,
    level: str = "ERROR",
    log_name: str | None = None,
    component: str | None = None,
    trace_id: str | None = None,
    request_id: str | None = None,
    connection_id: str | None = None,
    user_id: int | str | None = None,
    session_id: str | None = None,
    error_code: int | None = None,
    context: dict[str, Any] | None = None,
    exc_info: bool = False,
) -> None:
    try:
        logger = get_django_logger(log_name=log_name, component=component)
        event_level = _normalize_level(level)
        event_context = build_log_context(
            trace_id=trace_id,
            request_id=request_id,
            connection_id=connection_id,
            user_id=user_id,
            session_id=session_id,
            **(context or {}),
        )

        event_data = NsLogEventData(
            event=event,
            message=message,
            component=component or "ns_backend",
            log_name=log_name,
            trace_id=trace_id,
            request_id=request_id,
            connection_id=connection_id,
            user_id=user_id,
            session_id=session_id,
            error_code=error_code,
            level=event_level,
            pid=get_current_pid(),
            context=event_context,
        )

        payload = {
            "event": event_data.event,
            "message": event_data.message,
            "component": event_data.component,
            "log_name": event_data.log_name,
            "trace_id": event_data.trace_id,
            "request_id": event_data.request_id,
            "connection_id": event_data.connection_id,
            "user_id": event_data.user_id,
            "session_id": event_data.session_id,
            "error_code": event_data.error_code,
            "level": event_data.level,
            "pid": event_data.pid,
            "context": event_data.context,
        }

        log_method = getattr(logger, event_level.lower(), logger.error)
        log_method("%s", payload, exc_info=exc_info)
    except Exception:  # noqa
        pass


__all__ = ["emit_log_event", "short_identifier"]

