# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
from typing import (
    Any,
    TYPE_CHECKING
)

from ns_common.cache.backends.base import BaseCacheBackend
from ns_common.config import NsCacheConfig
from ns_common.exceptions import (
    NsDependencyError,
    NsRuntimeError,
    NsStateError,
)

if TYPE_CHECKING:
    pass


class RedisCacheBackend(BaseCacheBackend):
    SCAN_BATCH_SIZE = 500

    def __init__(self, config: NsCacheConfig) -> None:
        self._config = config
        self._client: Any | None = None

    def initialize(self) -> None:
        redis_module = self._load_redis_module()
        self._client = redis_module.Redis.from_url(
            self._config.cache_url,
            decode_responses=True,
        )

        self._client.ping()

    @staticmethod
    def _load_redis_module() -> Any:
        try:
            return importlib.import_module("redis")
        except ImportError as exc:
            raise NsDependencyError(
                "Python package 'redis' is required.",
                details={
                    "package": "redis",
                },
            ) from exc

    @property
    def client(self) -> Any:
        if self._client is None:
            raise NsRuntimeError("redis cache backend is not initialized.")
        return self._client

    def close(self) -> None:
        if self._client is None:
            return

        close = getattr(self._client, "close", None)
        if callable(close):
            close()

        self._client = None

    def get(self, key: str) -> str | None:
        value = self.client.get(key)
        return None if value is None else str(value)

    def get_many(self, keys: list[str]) -> dict[str, str]:
        if not keys:
            return {}

        values = self.client.mget(keys)
        result: dict[str, str] = {}

        for key, value in zip(keys, values):
            if value is not None:
                result[key] = str(value)

        return result

    def set(self, key: str, value: str, ttl: int | None) -> bool:
        if ttl == 0:
            self.delete(key)
            return False

        return bool(self.client.set(key, value, ex=ttl))

    def set_many(self, mapping: dict[str, str], ttl: int | None) -> bool:
        if not mapping:
            return True

        if ttl == 0:
            self.delete_many(list(mapping.keys()))
            return False

        pipeline = self.client.pipeline(transaction=True)
        for key, value in mapping.items():
            pipeline.set(key, value, ex=ttl)

        pipeline.execute()
        return True

    def add(self, key: str, value: str, ttl: int | None) -> bool:
        if ttl == 0:
            return False

        return bool(self.client.set(key, value, ex=ttl, nx=True))

    def touch(self, key: str, ttl: int | None) -> bool:
        if not self.exists(key):
            return False

        if ttl == 0:
            return self.delete(key)

        if ttl is None:
            return bool(self.client.persist(key))

        return bool(self.client.expire(key, int(ttl)))

    def delete(self, key: str) -> bool:
        return bool(self.client.delete(key))

    def delete_many(self, keys: list[str]) -> int:
        if not keys:
            return 0

        return int(self.client.delete(*keys))

    def exists(self, key: str) -> bool:
        return bool(self.client.exists(key))

    def clear(self, namespace_prefix: str) -> bool:
        batch: list[str] = []

        for key in self.client.scan_iter(match=f"{namespace_prefix}*", count=self.SCAN_BATCH_SIZE):
            batch.append(str(key))

            if len(batch) >= self.SCAN_BATCH_SIZE:
                self.client.delete(*batch)
                batch.clear()

        if batch:
            self.client.delete(*batch)

        return True

    def incr(self, key: str, delta: int = 1) -> int:
        if not self.exists(key):
            raise NsStateError(
                "cache key does not exist.",
                details={
                    "key": key,
                },
            )

        return int(self.client.incrby(key, int(delta)))
