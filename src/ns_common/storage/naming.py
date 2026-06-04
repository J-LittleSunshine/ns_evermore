# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import PurePosixPath
from typing import TYPE_CHECKING
from uuid import uuid4

from ns_common.storage.errors import NsObjectStorageValidationError
from ns_common.storage.utils import normalize_object_name

if TYPE_CHECKING:
    pass

_MODULE_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
_RESOURCE_TYPE_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]{1,127}$")
_RESOURCE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_.:-]{1,128}$")
_EXTENSION_PATTERN = re.compile(r"^[a-z0-9][a-z0-9]{0,15}$")


def normalize_module_code(value: str) -> str:
    """Normalize module code for object key and metadata."""
    if not isinstance(value, str):
        raise NsObjectStorageValidationError("object storage module_code must be str")

    module_code = value.strip().lower()
    if not _MODULE_CODE_PATTERN.fullmatch(module_code):
        raise NsObjectStorageValidationError("object storage module_code is invalid")

    return module_code


def normalize_resource_type(value: str) -> str:
    """Normalize resource type for object key and metadata."""
    if not isinstance(value, str):
        raise NsObjectStorageValidationError("object storage resource_type must be str")

    resource_type = value.strip().lower()
    if not _RESOURCE_TYPE_PATTERN.fullmatch(resource_type):
        raise NsObjectStorageValidationError("object storage resource_type is invalid")

    return resource_type


def normalize_resource_id(value: str | int | None) -> str | None:
    """Normalize optional resource id for object key and metadata."""
    if value is None:
        return None

    resource_id = str(value).strip()
    if not resource_id:
        return None

    if not _RESOURCE_ID_PATTERN.fullmatch(resource_id):
        raise NsObjectStorageValidationError("object storage resource_id is invalid")

    return resource_id


def normalize_original_filename(value: str | None) -> str | None:
    """Normalize original filename for metadata."""
    if value is None:
        return None

    original_filename = str(value).strip()
    if not original_filename:
        return None

    if "/" in original_filename or "\\" in original_filename:
        original_filename = PurePosixPath(original_filename.replace("\\", "/")).name

    if not original_filename:
        return None

    if len(original_filename.encode("utf-8")) > 255:
        raise NsObjectStorageValidationError("object storage original_filename cannot exceed 255 bytes")

    return original_filename


def normalize_object_extension(value: str | None) -> str:
    """Normalize optional object extension without leading dot."""
    if value is None:
        return "bin"

    extension = str(value).strip().lower().lstrip(".")
    if not extension:
        return "bin"

    if not _EXTENSION_PATTERN.fullmatch(extension):
        return "bin"

    return extension


def extract_extension_from_filename(filename: str | None) -> str:
    """Extract safe extension from original filename."""
    original_filename = normalize_original_filename(filename)
    if not original_filename:
        return "bin"

    suffix = PurePosixPath(original_filename).suffix
    return normalize_object_extension(suffix)


def build_object_name(
        *,
        module_code: str,
        resource_type: str,
        original_filename: str | None = None,
        resource_id: str | int | None = None,
        extension: str | None = None,
        now: datetime | None = None,
        unique_id: str | None = None,
) -> str:
    """Build normalized business object name.

    The returned name does not include global storage key_prefix.
    Backend layer applies key_prefix uniformly.
    """
    normalized_module_code = normalize_module_code(module_code)
    normalized_resource_type = normalize_resource_type(resource_type)
    normalized_resource_id = normalize_resource_id(resource_id)

    selected_time: datetime = now or datetime.now(timezone.utc)
    if selected_time.tzinfo is None:
        selected_time = selected_time.replace(tzinfo=timezone.utc)

    selected_extension = normalize_object_extension(extension) if extension else extract_extension_from_filename(original_filename)
    selected_unique_id = str(unique_id or uuid4().hex).strip().lower()
    if not selected_unique_id:
        selected_unique_id = uuid4().hex

    path_parts: list[str] = [
        normalized_module_code,
        normalized_resource_type,
        selected_time.strftime("%Y"),
        selected_time.strftime("%m"),
        selected_time.strftime("%d"),
    ]

    if normalized_resource_id:
        path_parts.append(normalized_resource_id)

    path_parts.append(f"{selected_unique_id}.{selected_extension}")

    return normalize_object_name("/".join(path_parts))
