# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_common.storage.client import NsObjectStorageClient, AsyncNsObjectStorageClient
from ns_common.storage.errors import (
    NsObjectStorageError,
    NsObjectStorageConfigurationError,
    NsObjectStorageConnectionError,
    NsObjectStorageConflictError,
    NsObjectStorageNotFoundError,
    NsObjectStoragePermissionError,
    NsObjectStorageValidationError
)
from ns_common.storage.hashing import (
    calculate_sha256_bytes,
    calculate_sha256_file,
    calculate_sha256_stream
)
from ns_common.storage.models import (
    NsObjectInfo,
    NsPresignedUrl,
    NsPutObjectResult,
    NsObjectRef,
    NsObjectUploadResult
)
from ns_common.storage.naming import (
    build_object_name,
    extract_extension_from_filename,
    normalize_module_code,
    normalize_object_extension,
    normalize_original_filename,
    normalize_resource_id,
    normalize_resource_type
)
from ns_common.storage.refs import build_object_ref, build_standard_metadata

if TYPE_CHECKING:
    pass

__all__ = [
    "NsObjectStorageClient",
    "AsyncNsObjectStorageClient",
    "NsObjectInfo",
    "NsObjectRef",
    "NsPresignedUrl",
    "NsPutObjectResult",
    "NsObjectStorageError",
    "NsObjectStorageConfigurationError",
    "NsObjectStorageConnectionError",
    "NsObjectStorageConflictError",
    "NsObjectStorageNotFoundError",
    "NsObjectStoragePermissionError",
    "NsObjectStorageValidationError",
    "calculate_sha256_bytes",
    "calculate_sha256_file",
    "calculate_sha256_stream",
    "build_object_name",
    "extract_extension_from_filename",
    "normalize_module_code",
    "normalize_object_extension",
    "normalize_original_filename",
    "normalize_resource_id",
    "normalize_resource_type",
    "build_object_ref",
    "build_standard_metadata",
    "NsObjectUploadResult",
]
