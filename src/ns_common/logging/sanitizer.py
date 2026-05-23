# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from ns_common.logging.constants import SENSITIVE_LOG_KEYS

_MAX_STRING_LENGTH = 512


def _truncate_string(value: str) -> str:
    return value[:_MAX_STRING_LENGTH]


def _safe_to_string(value: Any) -> str:
    try:
        return _truncate_string(str(value))
    except Exception:  # noqa
        return "<unserializable>"


def _normalize_sensitive_key(key: Any) -> str:
    return _safe_to_string(key).strip().lower()


def _compact_sensitive_key(key: Any) -> str:
    normalized = _normalize_sensitive_key(key)
    return "".join(ch for ch in normalized if ch not in {"_", "-", ".", " "})


def _is_sensitive_key(key: Any) -> bool:
    normalized = _normalize_sensitive_key(key)
    compact = _compact_sensitive_key(key)
    return normalized in SENSITIVE_LOG_KEYS or compact in SENSITIVE_LOG_KEYS


def sanitize_log_context(value: Any):
    try:
        if value is None or isinstance(value, (bool, int, float)):
            return value

        if isinstance(value, str):
            return _truncate_string(value)

        if isinstance(value, dict):
            result: dict[str, Any] = {}
            for key, item in value.items():
                normalized_key = _safe_to_string(key)
                if _is_sensitive_key(key):
                    result[normalized_key] = "***"
                    continue
                result[normalized_key] = sanitize_log_context(item)
            return result

        if isinstance(value, (list, tuple, set)):
            return [sanitize_log_context(item) for item in value]

        return _safe_to_string(value)
    except Exception:  # noqa
        return "<sanitize_error>"


__all__ = ["sanitize_log_context"]

