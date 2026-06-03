# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    pass

@dataclass(frozen=True, slots=True)
class NsCacheConfig:
    backend: Literal["redis", "valkey"] = "redis"
    url: str = "redis://127.0.0.1:6379/0"
    key_prefix: str = "ns"
    default_timeout: int = 300
    socket_timeout: float = 3.0
    socket_connect_timeout: float = 3.0
    max_connections: int = 64
    health_check_interval: int = 30
    serializer: Literal["pickle", "json", "raw"] = "pickle"
    decode_responses: bool = False
