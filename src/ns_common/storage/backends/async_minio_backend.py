# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_common.config import NsObjectStorageConfig
from ns_common.storage.backends.base import AsyncObjectStorageBackendWrapper
from ns_common.storage.backends.minio_backend import MinioObjectStorageBackend

if TYPE_CHECKING:
    pass

class AsyncMinioObjectStorageBackend(AsyncObjectStorageBackendWrapper):
    """Async MinIO object storage backend through worker-thread adapter."""

    def __init__(self, config: NsObjectStorageConfig) -> None:
        """Initialize async MinIO backend."""
        super().__init__(MinioObjectStorageBackend(config))
