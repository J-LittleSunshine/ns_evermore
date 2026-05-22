# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from ns_common.logging.sanitizer import sanitize_log_context


def _drop_none(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            normalized = _drop_none(item)
            if normalized is not None:
                result[str(key)] = normalized
        return result

    if isinstance(value, (list, tuple, set)):
        result = []
        for item in value:
            normalized = _drop_none(item)
            if normalized is not None:
                result.append(normalized)
        return result

    return value


def build_log_context(
    *,
    trace_id: str | None = None,
    request_id: str | None = None,
    connection_id: str | None = None,
    user_id: int | str | None = None,
    session_id: str | None = None,
    **context,
) -> dict[str, Any]:
    raw: dict[str, Any] = {
        "trace_id": trace_id,
        "request_id": request_id,
        "connection_id": connection_id,
        "user_id": user_id,
        "session_id": session_id,
        **context,
    }

    compact = _drop_none(raw)
    if not isinstance(compact, dict):
        return {}

    sanitized = sanitize_log_context(compact)
    return sanitized if isinstance(sanitized, dict) else {}


__all__ = ["build_log_context"]

