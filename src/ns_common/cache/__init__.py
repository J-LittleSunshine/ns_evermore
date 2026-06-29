# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_common.cache.clients import (
    AsyncCacheClient,
    CacheClient,
    close_cache_clients,
    get_async_cache_client,
    get_cache_client,
    validate_cache_backend,
)

if TYPE_CHECKING:
    pass

__all__ = [
    "AsyncCacheClient",
    "CacheClient",
    "close_cache_clients",
    "get_async_cache_client",
    "get_cache_client",
    "validate_cache_backend",
]