# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Mapping

from ns_common.storage.errors import NsObjectStorageValidationError

if TYPE_CHECKING:
    pass

_BUCKET_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")
_CONTROL_CHAR_PATTERN = re.compile(r"[\x00-\x1f\x7f]")


def normalize_bucket_name(value: str) -> str:
    """Normalize and validate one S3-compatible bucket name."""
    if not isinstance(value, str):
        raise NsObjectStorageValidationError("object storage bucket must be str")

    bucket = value.strip()
    if not bucket:
        raise NsObjectStorageValidationError("object storage bucket cannot be empty")

    if len(bucket) < 3 or len(bucket) > 63:
        raise NsObjectStorageValidationError("object storage bucket length must be between 3 and 63")

    if not _BUCKET_NAME_PATTERN.fullmatch(bucket):
        raise NsObjectStorageValidationError("object storage bucket contains invalid characters")

    if ".." in bucket or ".-" in bucket or "-." in bucket:
        raise NsObjectStorageValidationError("object storage bucket has invalid dot or hyphen sequence")

    return bucket


def normalize_object_name(value: str) -> str:
    """Normalize and validate one object name."""
    if not isinstance(value, str):
        raise NsObjectStorageValidationError("object storage object_name must be str")

    object_name = value.strip()
    if not object_name:
        raise NsObjectStorageValidationError("object storage object_name cannot be empty")

    if object_name.startswith("/"):
        raise NsObjectStorageValidationError("object storage object_name cannot start with slash")

    if "\\" in object_name:
        raise NsObjectStorageValidationError("object storage object_name cannot contain backslash")

    if _CONTROL_CHAR_PATTERN.search(object_name):
        raise NsObjectStorageValidationError("object storage object_name cannot contain control characters")

    path = PurePosixPath(object_name)
    if any(part in {"", ".", ".."} for part in path.parts):
        raise NsObjectStorageValidationError("object storage object_name contains invalid path segments")

    if len(object_name.encode("utf-8")) > 1024:
        raise NsObjectStorageValidationError("object storage object_name cannot exceed 1024 bytes")

    return object_name


def normalize_key_prefix(value: str) -> str:
    """Normalize optional object key prefix."""
    if value is None:
        return ""

    if not isinstance(value, str):
        raise NsObjectStorageValidationError("object storage key_prefix must be str")

    key_prefix = value.strip().strip("/")
    if not key_prefix:
        return ""

    return normalize_object_name(key_prefix)


def apply_object_key_prefix(*, key_prefix: str, object_name: str) -> str:
    """Apply namespace prefix to object name when needed."""
    normalized_object_name = normalize_object_name(object_name)
    normalized_key_prefix = normalize_key_prefix(key_prefix)

    if not normalized_key_prefix:
        return normalized_object_name

    if normalized_object_name == normalized_key_prefix:
        return normalized_object_name

    if normalized_object_name.startswith(f"{normalized_key_prefix}/"):
        return normalized_object_name

    return f"{normalized_key_prefix}/{normalized_object_name}"


def normalize_metadata(metadata: Mapping[str, str] | None) -> dict[str, str]:
    """Normalize metadata to string key/value pairs."""
    if metadata is None:
        return {}

    if not isinstance(metadata, Mapping):
        raise NsObjectStorageValidationError("object storage metadata must be a mapping")

    normalized: dict[str, str] = {}
    for key, value in metadata.items():
        if not isinstance(key, str):
            raise NsObjectStorageValidationError("object storage metadata key must be str")
        if not isinstance(value, str):
            raise NsObjectStorageValidationError("object storage metadata value must be str")

        normalized_key = key.strip()
        normalized_value = value.strip()

        if not normalized_key:
            raise NsObjectStorageValidationError("object storage metadata key cannot be empty")

        if _CONTROL_CHAR_PATTERN.search(normalized_key) or _CONTROL_CHAR_PATTERN.search(normalized_value):
            raise NsObjectStorageValidationError("object storage metadata cannot contain control characters")

        if len(normalized_key.encode("utf-8")) > 128:
            raise NsObjectStorageValidationError("object storage metadata key cannot exceed 128 bytes")

        if len(normalized_value.encode("utf-8")) > 2048:
            raise NsObjectStorageValidationError("object storage metadata value cannot exceed 2048 bytes")

        normalized[normalized_key] = normalized_value

    return normalized


def validate_payload_size(*, size: int, max_object_size: int | None) -> None:
    """Validate payload size against configured limit."""
    if isinstance(size, bool) or not isinstance(size, int):
        raise NsObjectStorageValidationError("object storage payload size must be int")

    if size < 0:
        raise NsObjectStorageValidationError("object storage payload size cannot be negative")

    if max_object_size is not None and size > max_object_size:
        raise NsObjectStorageValidationError("object storage payload exceeds configured max_object_size")
