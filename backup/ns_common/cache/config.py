# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    pass


@dataclass(slots=True, kw_only=True)
class NsCacheConfig:
    """Unified cache configuration loaded through ns_config."""

    backend: Literal["default", "sql_wal", "redis", "valkey"] = "default"
    location: str = ""
    key_prefix: str = "ns"
    default_timeout_seconds: int | None = 300
    serializer: Literal["pickle", "json", "raw"] = "pickle"

    sql_table: str = "ns_cache"
    sql_timeout_seconds: float = 5.0
    sql_max_entries: int = 10000
    sql_cull_frequency: int = 3

    socket_timeout: float = 3.0
    socket_connect_timeout: float = 3.0
    max_connections: int = 64
    health_check_interval: int = 30

    def resolved_backend(self) -> Literal["sql_wal", "redis", "valkey"]:
        """Resolve default backend to sql_wal without probing external services."""
        if self.backend in {
            "default",
            "sql_wal"
        }:
            return "sql_wal"
        return self.backend
