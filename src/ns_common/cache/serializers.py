# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import (
    Any,
    TYPE_CHECKING
)

from ns_common.exceptions import NsValidationError

if TYPE_CHECKING:
    pass

JsonValue = str | int | float | bool | None | list["JsonValue"] | dict[str, "JsonValue"]


def dumps_cache_value(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise NsValidationError(
            "cache value must be JSON serializable.",
            details={
                "actual_type": type(value).__name__,
            },
        ) from exc


def loads_cache_value(raw_value: str) -> JsonValue:
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError as exc:
        raise NsValidationError(
            "cached value is not valid JSON.",
            details={
                "line": exc.lineno,
                "column": exc.colno,
            },
        ) from exc
