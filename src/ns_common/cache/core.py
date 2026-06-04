# -*- coding: utf-8 -*-
from __future__ import annotations

from threading import RLock
from typing import TYPE_CHECKING, ClassVar

from ns_common.cache.backend import CacheBackend, SqlWalCacheBackend, RedisCompatibleCacheBackend, AsyncCacheBackend, AsyncSqlWalCacheBackend, AsyncRedisCompatibleCacheBackend
from ns_common.cache.constants import DefaultCacheTimeout, NS_CACHE_DEFAULT_TIMEOUT
from ns_common.cache.errors import NsCacheConfigurationError
from ns_common.config import NsCacheConfig

if TYPE_CHECKING:
    pass


class NsCacheClient:
    """Thread-safe process-local singleton cache client.

    Singleton identity is controlled by client name.
    Different config under the same client name is rejected.
    """

    name: str
    config: NsCacheConfig
    _backend: CacheBackend

    _lock: ClassVar[RLock] = RLock()
    _instances: ClassVar[dict[str, "NsCacheClient"]] = {}
    _default_config: ClassVar[NsCacheConfig | None] = None

    def __new__(cls, name: str = "default", config: NsCacheConfig | None = None) -> "NsCacheClient":
        """Create or return named singleton instance."""
        normalized_name = cls._normalize_client_name(name)

        with cls._lock:
            existing_client = cls._instances.get(normalized_name)
            if existing_client is not None:
                if config is not None and config != existing_client.config:
                    raise NsCacheConfigurationError(f"cache client already exists with different config: {normalized_name}")
                return existing_client

            selected_config = config or cls._default_config or cls._load_config_from_ns_config()
            instance = super().__new__(cls)
            instance.name = normalized_name
            instance.config = selected_config
            instance._backend = cls._build_backend(selected_config)
            cls._instances[normalized_name] = instance
            return instance

    def __init__(self, name: str = "default", config: NsCacheConfig | None = None) -> None:
        """Keep __init__ idempotent because singleton construction is handled in __new__."""
        _ = (name, config)

    @classmethod
    def configure_default(cls, config: NsCacheConfig) -> None:
        """Configure default cache config for later default client creation."""
        if not isinstance(config, NsCacheConfig):
            raise NsCacheConfigurationError("default cache config must be NsCacheConfig")

        with cls._lock:
            cls._default_config = config

    @classmethod
    def get_default(cls) -> "NsCacheClient":
        """Get default cache client."""
        return cls("default")

    @classmethod
    def get_or_create(cls, name: str = "default", config: NsCacheConfig | None = None) -> "NsCacheClient":
        """Compatibility helper for named singleton access."""
        return cls(name, config)

    @classmethod
    def close_all(cls) -> None:
        """Close all process-local cache clients."""
        with cls._lock:
            clients = list(cls._instances.values())
            cls._instances.clear()

        for client in clients:
            client.close()

    def get(self, key: str, default: object | None = None) -> object | None:
        """Get cache value."""
        return self._backend.get(key, default)

    def set(self, key: str, value: object, timeout: int | None | DefaultCacheTimeout = NS_CACHE_DEFAULT_TIMEOUT) -> bool:
        """Set cache value."""
        return self._backend.set(key, value, timeout)

    def add(self, key: str, value: object, timeout: int | None | DefaultCacheTimeout = NS_CACHE_DEFAULT_TIMEOUT) -> bool:
        """Set cache value only when key does not exist."""
        return self._backend.add(key, value, timeout)

    def delete(self, key: str) -> bool:
        """Delete cache key."""
        return self._backend.delete(key)

    def exists(self, key: str) -> bool:
        """Check whether key exists."""
        return self._backend.exists(key)

    def expire(self, key: str, timeout: int) -> bool:
        """Update key expiration."""
        return self._backend.expire(key, timeout)

    def persist(self, key: str) -> bool:
        """Remove key expiration."""
        return self._backend.persist(key)

    def ttl(self, key: str) -> int:
        """Return Redis-compatible TTL."""
        return self._backend.ttl(key)

    def clear(self) -> bool:
        """Clear cache keys under current prefix."""
        return self._backend.clear()

    def get_many(self, keys: list[str]) -> dict[str, object]:
        """Batch get cache values."""
        return self._backend.get_many(keys)

    def set_many(self, data: dict[str, object], timeout: int | None | DefaultCacheTimeout = NS_CACHE_DEFAULT_TIMEOUT) -> list[str]:
        """Batch set cache values."""
        return self._backend.set_many(data, timeout)

    def delete_many(self, keys: list[str]) -> int:
        """Batch delete cache keys."""
        return self._backend.delete_many(keys)

    def close(self) -> None:
        """Close cache backend resources and remove singleton reference."""
        with self.__class__._lock:
            existing_client: NsCacheClient | None = self.__class__._instances.get(self.name)
            if existing_client is self:
                self.__class__._instances.pop(self.name, None)

        self._backend.close()

    @staticmethod
    def _normalize_client_name(name: str) -> str:
        """Normalize singleton client name."""
        if not isinstance(name, str) or not name.strip():
            raise NsCacheConfigurationError("cache client name must be a non-empty str")
        return name.strip()

    @staticmethod
    def _load_config_from_ns_config() -> NsCacheConfig:
        """Load default cache config from ns_config."""
        from ns_common.config import ns_config

        return ns_config.cache_config

    @staticmethod
    def _build_backend(config: NsCacheConfig) -> CacheBackend:
        """Build backend by explicit configuration."""
        resolved_backend = config.resolved_backend()
        if resolved_backend == "sql_wal":
            return SqlWalCacheBackend(config)
        if resolved_backend in {"redis", "valkey"}:
            return RedisCompatibleCacheBackend(config)
        raise NsCacheConfigurationError(f"unsupported cache backend: {config.backend}")


class AsyncNsCacheClient:
    """Thread-safe process-local singleton async cache client.

    Singleton identity is controlled by client name.
    Different config under the same client name is rejected.
    """

    name: str
    config: NsCacheConfig
    _backend: AsyncCacheBackend

    _lock: ClassVar[RLock] = RLock()
    _instances: ClassVar[dict[str, "AsyncNsCacheClient"]] = {}
    _default_config: ClassVar[NsCacheConfig | None] = None

    def __new__(cls, name: str = "default", config: NsCacheConfig | None = None) -> "AsyncNsCacheClient":
        """Create or return named singleton instance."""
        normalized_name = cls._normalize_client_name(name)

        with cls._lock:
            existing_client = cls._instances.get(normalized_name)
            if existing_client is not None:
                if config is not None and config != existing_client.config:
                    raise NsCacheConfigurationError(f"async cache client already exists with different config: {normalized_name}")
                return existing_client

            selected_config = config or cls._default_config or cls._load_config_from_ns_config()
            instance = super().__new__(cls)
            instance.name = normalized_name
            instance.config = selected_config
            instance._backend = cls._build_backend(selected_config)
            cls._instances[normalized_name] = instance
            return instance

    def __init__(self, name: str = "default", config: NsCacheConfig | None = None) -> None:
        """Keep __init__ idempotent because singleton construction is handled in __new__."""
        _ = (name, config)

    @classmethod
    def configure_default(cls, config: NsCacheConfig) -> None:
        """Configure default async cache config for later default client creation."""
        if not isinstance(config, NsCacheConfig):
            raise NsCacheConfigurationError("default async cache config must be NsCacheConfig")

        with cls._lock:
            cls._default_config = config

    @classmethod
    def get_default(cls) -> "AsyncNsCacheClient":
        """Get default async cache client."""
        return cls("default")

    @classmethod
    def get_or_create(cls, name: str = "default", config: NsCacheConfig | None = None) -> "AsyncNsCacheClient":
        """Compatibility helper for named singleton access."""
        return cls(name, config)

    @classmethod
    async def close_all(cls) -> None:
        """Close all process-local async cache clients."""
        with cls._lock:
            clients = list(cls._instances.values())
            cls._instances.clear()

        for client in clients:
            await client.close()

    async def get(self, key: str, default: object | None = None) -> object | None:
        """Get cache value."""
        return await self._backend.get(key, default)

    async def set(self, key: str, value: object, timeout: int | None | DefaultCacheTimeout = NS_CACHE_DEFAULT_TIMEOUT) -> bool:
        """Set cache value."""
        return await self._backend.set(key, value, timeout)

    async def add(self, key: str, value: object, timeout: int | None | DefaultCacheTimeout = NS_CACHE_DEFAULT_TIMEOUT) -> bool:
        """Set cache value only when key does not exist."""
        return await self._backend.add(key, value, timeout)

    async def delete(self, key: str) -> bool:
        """Delete cache key."""
        return await self._backend.delete(key)

    async def exists(self, key: str) -> bool:
        """Check whether key exists."""
        return await self._backend.exists(key)

    async def expire(self, key: str, timeout: int) -> bool:
        """Update key expiration."""
        return await self._backend.expire(key, timeout)

    async def persist(self, key: str) -> bool:
        """Remove key expiration."""
        return await self._backend.persist(key)

    async def ttl(self, key: str) -> int:
        """Return Redis-compatible TTL."""
        return await self._backend.ttl(key)

    async def clear(self) -> bool:
        """Clear cache keys under current prefix."""
        return await self._backend.clear()

    async def get_many(self, keys: list[str]) -> dict[str, object]:
        """Batch get cache values."""
        return await self._backend.get_many(keys)

    async def set_many(self, data: dict[str, object], timeout: int | None | DefaultCacheTimeout = NS_CACHE_DEFAULT_TIMEOUT) -> list[str]:
        """Batch set cache values."""
        return await self._backend.set_many(data, timeout)

    async def delete_many(self, keys: list[str]) -> int:
        """Batch delete cache keys."""
        return await self._backend.delete_many(keys)

    async def close(self) -> None:
        """Close cache backend resources and remove singleton reference."""
        with self.__class__._lock:
            existing_client: AsyncNsCacheClient | None = self.__class__._instances.get(self.name)
            if existing_client is self:
                self.__class__._instances.pop(self.name, None)

        await self._backend.close()

    @staticmethod
    def _normalize_client_name(name: str) -> str:
        """Normalize singleton client name."""
        if not isinstance(name, str) or not name.strip():
            raise NsCacheConfigurationError("async cache client name must be a non-empty str")
        return name.strip()

    @staticmethod
    def _load_config_from_ns_config() -> NsCacheConfig:
        """Load default cache config from ns_config."""
        from ns_common.config import ns_config

        return ns_config.cache_config

    @staticmethod
    def _build_backend(config: NsCacheConfig) -> AsyncCacheBackend:
        """Build async backend by explicit configuration."""
        resolved_backend = config.resolved_backend()
        if resolved_backend == "sql_wal":
            return AsyncSqlWalCacheBackend(config)
        if resolved_backend in {"redis", "valkey"}:
            return AsyncRedisCompatibleCacheBackend(config)
        raise NsCacheConfigurationError(f"unsupported async cache backend: {config.backend}")
