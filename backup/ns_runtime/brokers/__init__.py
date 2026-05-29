# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_runtime.brokers.base import RuntimeBroker
from ns_runtime.brokers.memory import MemoryBroker

if TYPE_CHECKING:
    from ns_runtime.brokers.redis_valkey import (
        RedisValkeyBroker,
        RedisValkeyBrokerConfig,
        StreamMessage,
    )


def __getattr__(name: str) -> Any:
    if name in {"RedisValkeyBroker", "RedisValkeyBrokerConfig", "StreamMessage"}:
        from ns_runtime.brokers.redis_valkey import (  # 局部导入避免包导入阶段强依赖 redis/valkey 客户端
            RedisValkeyBroker,
            RedisValkeyBrokerConfig,
            StreamMessage,
        )

        exported = {
            "RedisValkeyBroker": RedisValkeyBroker,
            "RedisValkeyBrokerConfig": RedisValkeyBrokerConfig,
            "StreamMessage": StreamMessage,
        }
        return exported[name]

    raise AttributeError(name)

__all__ = [
    "RuntimeBroker",
    "MemoryBroker",
    "RedisValkeyBroker",
    "RedisValkeyBrokerConfig",
    "StreamMessage",
]

