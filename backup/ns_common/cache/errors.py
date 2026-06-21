# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class NsCacheError(Exception):
    """Base exception for ns_common cache."""


class NsCacheConfigurationError(NsCacheError):
    """Raised when cache configuration is invalid."""


class NsCacheConnectionError(NsCacheError):
    """Raised when cache backend operation fails."""


class NsCacheSerializationError(NsCacheError):
    """Raised when cache serialization or deserialization fails."""
