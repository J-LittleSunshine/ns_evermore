# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_common.config import NsObjectStorageConfig
from ns_common.storage.backends.base import AsyncObjectStorageBackendWrapper
from ns_common.storage.backends.local_fs import LocalFileObjectStorageBackend

if TYPE_CHECKING:
    pass

class AsyncLocalFileObjectStorageBackend(AsyncObjectStorageBackendWrapper):
    """Async local filesystem object storage backend through worker-thread adapter."""

    def __init__(self, config: NsObjectStorageConfig) -> None:
        """Initialize async local filesystem backend."""
        super().__init__(LocalFileObjectStorageBackend(config))
