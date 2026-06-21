# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class NsObjectStorageError(Exception):
    """Base exception for ns_common object storage."""


class NsObjectStorageConfigurationError(NsObjectStorageError):
    """Raised when object storage configuration is invalid."""


class NsObjectStorageConnectionError(NsObjectStorageError):
    """Raised when object storage backend operation fails due to connectivity or backend errors."""


class NsObjectStorageNotFoundError(NsObjectStorageError):
    """Raised when bucket or object does not exist."""


class NsObjectStorageConflictError(NsObjectStorageError):
    """Raised when object storage operation conflicts with existing backend state."""


class NsObjectStoragePermissionError(NsObjectStorageError):
    """Raised when object storage backend denies the operation."""


class NsObjectStorageValidationError(NsObjectStorageError):
    """Raised when bucket name, object name, metadata, or payload is invalid."""
