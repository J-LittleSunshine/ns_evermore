# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_common.storage.backends.async_local_fs import AsyncLocalFileObjectStorageBackend
from ns_common.storage.backends.async_minio_backend import AsyncMinioObjectStorageBackend
from ns_common.storage.backends.base import BaseObjectStorageBackend, ObjectStorageBackend, AsyncObjectStorageBackend, AsyncObjectStorageBackendWrapper
from ns_common.storage.backends.local_fs import LocalFileObjectStorageBackend
from ns_common.storage.backends.minio_backend import MinioObjectStorageBackend

if TYPE_CHECKING:
    pass

__all__ = [
    "BaseObjectStorageBackend",
    "ObjectStorageBackend",
    "AsyncObjectStorageBackend",
    "AsyncObjectStorageBackendWrapper",
    "LocalFileObjectStorageBackend",
    "MinioObjectStorageBackend",
    "AsyncLocalFileObjectStorageBackend",
    "AsyncMinioObjectStorageBackend",
]
