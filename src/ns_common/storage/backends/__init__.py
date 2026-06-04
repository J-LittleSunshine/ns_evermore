# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_common.storage.backends.base import BaseObjectStorageBackend, ObjectStorageBackend
from ns_common.storage.backends.local_fs import LocalFileObjectStorageBackend
from ns_common.storage.backends.minio_backend import MinioObjectStorageBackend

if TYPE_CHECKING:
    pass

__all__ = [
    "BaseObjectStorageBackend",
    "ObjectStorageBackend",
    "LocalFileObjectStorageBackend",
    "MinioObjectStorageBackend",
]
