# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from ns_backend.logger import get_logger
from ns_common.logging.event import NsLogEventData
from ns_common.logging.sanitizer import sanitize_log_context


def log_event(
    *,
    event: str,
    message: str,
    trace_id: str | None = None,
    user_id: int | None = None,
    error_code: int | None = None,
    context: dict[str, Any] | None = None,
    level: str = "warning",
    log_name: str = "ns_backend",
) -> None:
    logger = get_logger(log_name)
    data = NsLogEventData(
        event=event,
        message=message,
        trace_id=trace_id,
        user_id=user_id,
        error_code=error_code,
        context=sanitize_log_context(context or {}),
    )

    payload = {
        "event": data.event,
        "message": data.message,
        "trace_id": data.trace_id,
        "user_id": data.user_id,
        "error_code": data.error_code,
        "context": data.context,
    }

    log_method = getattr(logger, level, logger.warning)
    log_method("%s", payload)


__all__ = ["log_event"]

