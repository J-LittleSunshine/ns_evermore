# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


class NsCacheError(Exception):
    """Base cache error."""


class NsCacheConnectionError(NsCacheError):
    """Cache connection error."""


class NsCacheSerializationError(NsCacheError):
    """Cache serialization error."""


class NsCacheConfigurationError(NsCacheError):
    """Cache configuration error."""
