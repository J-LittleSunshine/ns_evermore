# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_common.storage.client import NsObjectStorageClient
from ns_common.storage.errors import (
    NsObjectStorageError,
    NsObjectStorageConfigurationError,
    NsObjectStorageConnectionError,
    NsObjectStorageConflictError,
    NsObjectStorageNotFoundError,
    NsObjectStoragePermissionError,
    NsObjectStorageValidationError
)
from ns_common.storage.models import NsObjectInfo, NsPresignedUrl, NsPutObjectResult

if TYPE_CHECKING:
    pass

__all__ = [
    "NsObjectStorageClient",
    "NsObjectInfo",
    "NsPresignedUrl",
    "NsPutObjectResult",
    "NsObjectStorageError",
    "NsObjectStorageConfigurationError",
    "NsObjectStorageConnectionError",
    "NsObjectStorageConflictError",
    "NsObjectStorageNotFoundError",
    "NsObjectStoragePermissionError",
    "NsObjectStorageValidationError",
]
