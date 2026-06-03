# -*- coding: utf-8 -*-
from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING, ClassVar

from ns_common.cache.backends import RedisCacheBackend
from ns_common.cache.config import NsCacheConfig
from ns_common.cache.exceptions import NsCacheConfigurationError

if TYPE_CHECKING:
    pass

class NsCacheClient:
    _lock: ClassVar[RLock] = RLock()
    _default_config: ClassVar[NsCacheConfig | None] = None
    _instances: ClassVar[dict[str, "NsCacheClient"]] = {}

    def __init__(self, name: str, config: NsCacheConfig) -> None:
        if not isinstance(name, str) or not name.strip():
            raise NsCacheConfigurationError("cache client name must be a non-empty str")

        if config.backend not in {"redis", "valkey"}:
            raise NsCacheConfigurationError(f"unsupported cache backend: {config.backend}")

        self.name: str = name.strip()
        self.config: NsCacheConfig = config
        self._backend: RedisCacheBackend = RedisCacheBackend(config)

    @classmethod
    def configure_default(cls, config: NsCacheConfig) -> None:
        if not isinstance(config, NsCacheConfig):
            raise NsCacheConfigurationError("default cache config must be NsCacheConfig")

        if config.backend not in {"redis", "valkey"}:
            raise NsCacheConfigurationError(f"unsupported cache backend: {config.backend}")

        with cls._lock:
            cls._default_config = config

    @classmethod
    def get_default(cls) -> "NsCacheClient":
        return cls.get_or_create("default", cls._default_config or NsCacheConfig())

    @classmethod
    def get_or_create(cls, name: str = "default", config: NsCacheConfig | None = None) -> "NsCacheClient":
        if not isinstance(name, str) or not name.strip():
            raise NsCacheConfigurationError("cache client name must be a non-empty str")

        normalized_name = name.strip()

        with cls._lock:
            existing_client = cls._instances.get(normalized_name)
            if existing_client is not None:
                return existing_client

            selected_config = config or cls._default_config or NsCacheConfig()
            if selected_config.backend not in {"redis", "valkey"}:
                raise NsCacheConfigurationError(f"unsupported cache backend: {selected_config.backend}")

            client = cls(normalized_name, selected_config)
            cls._instances[normalized_name] = client
            return client

    @classmethod
    def close_all(cls) -> None:
        with cls._lock:
            clients = list(cls._instances.values())
            cls._instances.clear()

        for client in clients:
            client.close()

    def get(self, key: str, default: object | None = None) -> object | None:
        return self._backend.get(key, default)

    def set(self, key: str, value: object, timeout: int | None = None) -> bool:
        return self._backend.set(key, value, timeout)

    def add(self, key: str, value: object, timeout: int | None = None) -> bool:
        return self._backend.add(key, value, timeout)

    def delete(self, key: str) -> bool:
        return self._backend.delete(key)

    def exists(self, key: str) -> bool:
        return self._backend.exists(key)

    def expire(self, key: str, timeout: int) -> bool:
        return self._backend.expire(key, timeout)

    def ttl(self, key: str) -> int:
        return self._backend.ttl(key)

    def clear(self) -> bool:
        return self._backend.clear()

    def get_many(self, keys: list[str]) -> dict[str, object]:
        return self._backend.get_many(keys)

    def set_many(self, data: dict[str, object], timeout: int | None = None) -> list[str]:
        return self._backend.set_many(data, timeout)

    def delete_many(self, keys: list[str]) -> int:
        return self._backend.delete_many(keys)

    def close(self) -> None:
        self._backend.close()
