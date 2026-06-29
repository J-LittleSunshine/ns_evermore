# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from typing import (
    Any,
    TYPE_CHECKING
)

from ns_common.exceptions import NsValidationError

if TYPE_CHECKING:
    pass

_CACHE_KEY_PART_PATTERN = re.compile(r"^[a-zA-Z0-9_.:-]+$")


def validate_cache_key_part(value: Any, field_name: str) -> str:
    if not isinstance(value, str):
        raise NsValidationError(
            f"{field_name} must be a string.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )

    text = value.strip()
    if not text:
        raise NsValidationError(
            f"{field_name} must not be empty.",
            details={
                "field": field_name,
            },
        )

    if _CACHE_KEY_PART_PATTERN.fullmatch(text) is None:
        raise NsValidationError(
            f"{field_name} contains invalid characters.",
            details={
                "field": field_name,
                "value": value,
                "allowed_pattern": _CACHE_KEY_PART_PATTERN.pattern,
            },
        )

    return text


def build_full_key(*, key_prefix: str, namespace: str, key: str) -> str:
    normalized_key_prefix = validate_cache_key_part(key_prefix, "key_prefix")
    normalized_namespace = validate_cache_key_part(namespace, "namespace")
    normalized_key = validate_cache_key_part(key, "key")

    return f"{normalized_key_prefix}:{normalized_namespace}:{normalized_key}"


def build_namespace_prefix(*, key_prefix: str, namespace: str) -> str:
    normalized_key_prefix = validate_cache_key_part(key_prefix, "key_prefix")
    normalized_namespace = validate_cache_key_part(namespace, "namespace")

    return f"{normalized_key_prefix}:{normalized_namespace}:"
