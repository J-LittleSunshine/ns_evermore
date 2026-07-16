# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from ..metadata import NsConfigGroupMetadata


@dataclass(frozen=True, slots=True, kw_only=True)
class NsCacheConfig:
    backend: Literal["sqlite", "redis", "valkey", "dummy"] = "sqlite"
    key_prefix: str = "ns_evermore"
    django_namespace: str = "ns_backend"
    cache_url: str = ""
    default_ttl_seconds: int = 300
    none_ttl_means_forever: bool = False
    sqlite_path: str = "data/ns_cache.sqlite3"
    sqlite_busy_timeout_ms: int = 5000
    sqlite_write_max_retries: int = 3
    sqlite_write_retry_base_delay_ms: int = 50
    sqlite_write_retry_max_delay_ms: int = 500
    cleanup_interval_seconds: int = 300
    cleanup_batch_size: int = 500
    metadata: NsConfigGroupMetadata = field(default_factory=NsConfigGroupMetadata)
