# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from ns_common.logging.constants import SENSITIVE_LOG_KEYS

_MAX_STRING_LENGTH = 512


def sanitize_log_context(value: Any):
    if value is None or isinstance(value, (bool, int, float)):
        return value

    if isinstance(value, str):
        return value[:_MAX_STRING_LENGTH]

    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            normalized_key = str(key)
            if normalized_key.lower() in SENSITIVE_LOG_KEYS:
                result[normalized_key] = "***"
                continue
            result[normalized_key] = sanitize_log_context(item)
        return result

    if isinstance(value, (list, tuple, set)):
        return [sanitize_log_context(item) for item in value]

    return str(value)[:_MAX_STRING_LENGTH]


__all__ = ["sanitize_log_context"]

