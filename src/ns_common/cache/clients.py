# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from threading import RLock
from typing import (
    Any,
    TYPE_CHECKING
)

from ns_common.cache.backends.base import BaseCacheBackend
from ns_common.cache.backends.dummy import DummyCacheBackend
from ns_common.cache.backends.redis import RedisCacheBackend
from ns_common.cache.backends.sqlite import SQLiteCacheBackend
from ns_common.cache.backends.valkey import ValkeyCacheBackend
from ns_common.cache.keys import (
    build_full_key,
    build_namespace_prefix,
    validate_cache_key_part,
)
from ns_common.cache.serializers import (
    dumps_cache_value,
    loads_cache_value,
)
from ns_common.config import (
    NsCacheConfig,
    ns_config,
)
from ns_common.exceptions import (
    NsRuntimeError,
    NsValidationError,
)
from ns_common.logger import get_ns_logger
from ns_common.paths import ROOT_DIR

if TYPE_CHECKING:
    pass

_TTL_UNSET = object()

_BACKEND_LOCK = RLock()
_BACKEND: BaseCacheBackend | None = None

_CLIENT_LOCK = RLock()
_CLIENTS: dict[str, "CacheClient"] = {}
_ASYNC_CLIENTS: dict[str, "AsyncCacheClient"] = {}

def resolve_sqlite_cache_path(cache_config: NsCacheConfig) -> Path:
    path = Path(cache_config.sqlite_path)

    if path.is_absolute():
        return path

    return ROOT_DIR / path


def build_cache_backend(cache_config: NsCacheConfig | None = None) -> BaseCacheBackend:
    config = cache_config or ns_config.cache

    if config.backend == "sqlite":
        return SQLiteCacheBackend(
            config=config,
            sqlite_path=resolve_sqlite_cache_path(config),
        )

    if config.backend == "redis":
        return RedisCacheBackend(config=config)

    if config.backend == "valkey":
        return ValkeyCacheBackend(config=config)

    if config.backend == "dummy":
        return DummyCacheBackend()

    raise NsRuntimeError(
        "unsupported cache backend.",
        details={
            "backend": config.backend,
        },
    )


def get_cache_backend() -> BaseCacheBackend:
    global _BACKEND

    with _BACKEND_LOCK:
        if _BACKEND is None:
            backend = build_cache_backend(ns_config.cache)
            backend.initialize()
            _BACKEND = backend

        return _BACKEND


def validate_cache_backend() -> None:
    get_cache_backend()


def close_cache_clients() -> None:
    global _BACKEND

    with _CLIENT_LOCK:
        _CLIENTS.clear()
        _ASYNC_CLIENTS.clear()

    with _BACKEND_LOCK:
        if _BACKEND is not None:
            _BACKEND.close()
            _BACKEND = None


async def aclose_cache_clients() -> None:
    global _BACKEND

    with _CLIENT_LOCK:
        _CLIENTS.clear()
        _ASYNC_CLIENTS.clear()

    with _BACKEND_LOCK:
        backend = _BACKEND
        _BACKEND = None

    if backend is not None:
        await backend.aclose()


def get_cache_client(*, namespace: str) -> "CacheClient":
    normalized_namespace = validate_cache_key_part(namespace, "namespace")

    with _CLIENT_LOCK:
        client = _CLIENTS.get(normalized_namespace)
        if client is None:
            client = CacheClient(
                namespace=normalized_namespace,
                backend=get_cache_backend(),
                cache_config=ns_config.cache,
            )
            _CLIENTS[normalized_namespace] = client

        return client


def get_async_cache_client(*, namespace: str) -> "AsyncCacheClient":
    normalized_namespace = validate_cache_key_part(namespace, "namespace")

    with _CLIENT_LOCK:
        client = _ASYNC_CLIENTS.get(normalized_namespace)
        if client is None:
            client = AsyncCacheClient(
                sync_client=get_cache_client(namespace=normalized_namespace),
            )
            _ASYNC_CLIENTS[normalized_namespace] = client

        return client


class CacheClient:
    def __init__(self, *, namespace: str, backend: BaseCacheBackend, cache_config: NsCacheConfig) -> None:
        self._namespace = validate_cache_key_part(namespace, "namespace")
        self._backend = backend
        self._config = cache_config

    @property
    def namespace(self) -> str:
        return self._namespace

    def _full_key(self, key: str) -> str:
        return build_full_key(
            key_prefix=self._config.key_prefix,
            namespace=self._namespace,
            key=key,
        )

    def _namespace_prefix(self) -> str:
        return build_namespace_prefix(
            key_prefix=self._config.key_prefix,
            namespace=self._namespace,
        )

    def _resolve_ttl(self, ttl: Any = _TTL_UNSET) -> int | None:
        if ttl is _TTL_UNSET:
            return int(self._config.default_ttl_seconds)

        if ttl is None:
            if self._config.none_ttl_means_forever:
                return None

            return int(self._config.default_ttl_seconds)

        if isinstance(ttl, bool) or not isinstance(ttl, int):
            raise NsValidationError(
                "ttl must be an integer or None.",
                details={
                    "ttl": ttl,
                    "actual_type": type(ttl).__name__,
                },
            )

        return max(int(ttl), 0)

    @staticmethod
    def _validate_delta(delta: Any) -> int:
        if isinstance(delta, bool) or not isinstance(delta, int):
            raise NsValidationError(
                "delta must be an integer.",
                details={
                    "delta": delta,
                    "actual_type": type(delta).__name__,
                },
            )

        return int(delta)

    def _log_soft_failure(self, operation: str, exc: Exception, *, key: str | None = None) -> None:
        get_ns_logger("ns_common.cache", True).warning(
            "cache operation failed softly",
            exc_info=True,
            extra={
                "operation": operation,
                "namespace": self._namespace,
                "key": key,
                "exception_class": exc.__class__.__name__,
            },
        )

    def get(self, key: str, default: Any = None) -> Any:
        full_key = self._full_key(key)

        try:
            raw_value = self._backend.get(full_key)
            if raw_value is None:
                return default

            return loads_cache_value(raw_value)
        except NsValidationError:
            raise
        except Exception as exc:  # noqa
            self._log_soft_failure("get", exc, key=key)
            return default

    def get_many(self, keys: list[str]) -> dict[str, Any]:
        full_key_map = {
            self._full_key(key): key
            for key in keys
        }

        try:
            raw_values = self._backend.get_many(list(full_key_map.keys()))
            result: dict[str, Any] = {}

            for full_key, raw_value in raw_values.items():
                original_key = full_key_map.get(full_key)
                if original_key is None:
                    continue

                result[original_key] = loads_cache_value(raw_value)

            return result
        except NsValidationError:
            raise
        except Exception as exc:  # noqa
            self._log_soft_failure("get_many", exc)
            return {}

    def set(self, key: str, value: Any, ttl: Any = _TTL_UNSET) -> bool:
        full_key = self._full_key(key)
        raw_value = dumps_cache_value(value)
        resolved_ttl = self._resolve_ttl(ttl)

        try:
            return self._backend.set(full_key, raw_value, resolved_ttl)
        except NsValidationError:
            raise
        except Exception as exc:  # noqa
            self._log_soft_failure("set", exc, key=key)
            return False

    def set_many(self, mapping: dict[str, Any], ttl: Any = _TTL_UNSET) -> bool:
        full_mapping = {
            self._full_key(key): dumps_cache_value(value)
            for key, value in mapping.items()
        }
        resolved_ttl = self._resolve_ttl(ttl)

        try:
            return self._backend.set_many(full_mapping, resolved_ttl)
        except NsValidationError:
            raise
        except Exception as exc:  # noqa
            self._log_soft_failure("set_many", exc)
            return False

    def add(self, key: str, value: Any, ttl: Any = _TTL_UNSET) -> bool:
        full_key = self._full_key(key)
        raw_value = dumps_cache_value(value)
        resolved_ttl = self._resolve_ttl(ttl)

        try:
            return self._backend.add(full_key, raw_value, resolved_ttl)
        except NsValidationError:
            raise
        except Exception as exc:  # noqa
            self._log_soft_failure("add", exc, key=key)
            return False

    def touch(self, key: str, ttl: Any = _TTL_UNSET) -> bool:
        full_key = self._full_key(key)
        resolved_ttl = self._resolve_ttl(ttl)

        try:
            return self._backend.touch(full_key, resolved_ttl)
        except NsValidationError:
            raise
        except Exception as exc:  # noqa
            self._log_soft_failure("touch", exc, key=key)
            return False

    def delete(self, key: str) -> bool:
        full_key = self._full_key(key)

        try:
            return self._backend.delete(full_key)
        except NsValidationError:
            raise
        except Exception as exc:  # noqa
            self._log_soft_failure("delete", exc, key=key)
            return False

    def delete_many(self, keys: list[str]) -> int:
        full_keys = [
            self._full_key(key)
            for key in keys
        ]

        try:
            return self._backend.delete_many(full_keys)
        except NsValidationError:
            raise
        except Exception as exc:  # noqa
            self._log_soft_failure("delete_many", exc)
            return 0

    def exists(self, key: str) -> bool:
        full_key = self._full_key(key)

        try:
            return self._backend.exists(full_key)
        except NsValidationError:
            raise
        except Exception as exc:  # noqa
            self._log_soft_failure("exists", exc, key=key)
            return False

    def clear(self) -> bool:
        try:
            return self._backend.clear(self._namespace_prefix())
        except NsValidationError:
            raise
        except Exception as exc:  # noqa
            self._log_soft_failure("clear", exc)
            return False

    def incr(self, key: str, delta: int = 1) -> int:
        """
        控制类操作严格失败。

        不做软降级，避免限流/计数/幂等控制误判。
        """
        full_key = self._full_key(key)
        return self._backend.incr(full_key, self._validate_delta(delta))

    def decr(self, key: str, delta: int = 1) -> int:
        full_key = self._full_key(key)
        return self._backend.decr(full_key, self._validate_delta(delta))

    def cleanup_expired(self) -> int:
        try:
            return self._backend.cleanup_expired()
        except Exception as exc:  # noqa
            self._log_soft_failure("cleanup_expired", exc)
            return 0


class AsyncCacheClient:
    def __init__(self, *, sync_client: CacheClient) -> None:
        self._sync_client = sync_client

    @property
    def namespace(self) -> str:
        return self._sync_client.namespace

    async def get(self, key: str, default: Any = None) -> Any:
        full_key = self._sync_client._full_key(key)  # noqa

        try:
            raw_value = await self._sync_client._backend.aget(full_key)  # noqa
            if raw_value is None:
                return default

            return loads_cache_value(raw_value)
        except NsValidationError:
            raise
        except Exception as exc:  # noqa
            self._sync_client._log_soft_failure("aget", exc, key=key)  # noqa
            return default

    async def get_many(self, keys: list[str]) -> dict[str, Any]:
        full_key_map = {
            self._sync_client._full_key(key): key  # noqa
            for key in keys
        }

        try:
            raw_values = await self._sync_client._backend.aget_many(list(full_key_map.keys()))  # noqa
            result: dict[str, Any] = {}

            for full_key, raw_value in raw_values.items():
                original_key = full_key_map.get(full_key)
                if original_key is None:
                    continue

                result[original_key] = loads_cache_value(raw_value)

            return result
        except NsValidationError:
            raise
        except Exception as exc:  # noqa
            self._sync_client._log_soft_failure("aget_many", exc)  # noqa
            return {}

    async def set(self, key: str, value: Any, ttl: Any = _TTL_UNSET) -> bool:
        full_key = self._sync_client._full_key(key)  # noqa
        raw_value = dumps_cache_value(value)
        resolved_ttl = self._sync_client._resolve_ttl(ttl)  # noqa

        try:
            return await self._sync_client._backend.aset(full_key, raw_value, resolved_ttl)  # noqa
        except NsValidationError:
            raise
        except Exception as exc:  # noqa
            self._sync_client._log_soft_failure("aset", exc, key=key)  # noqa
            return False

    async def set_many(self, mapping: dict[str, Any], ttl: Any = _TTL_UNSET) -> bool:
        full_mapping = {
            self._sync_client._full_key(key): dumps_cache_value(value)  # noqa
            for key, value in mapping.items()
        }
        resolved_ttl = self._sync_client._resolve_ttl(ttl)  # noqa

        try:
            return await self._sync_client._backend.aset_many(full_mapping, resolved_ttl)  # noqa
        except NsValidationError:
            raise
        except Exception as exc:  # noqa
            self._sync_client._log_soft_failure("aset_many", exc)  # noqa
            return False

    async def add(self, key: str, value: Any, ttl: Any = _TTL_UNSET) -> bool:
        full_key = self._sync_client._full_key(key)  # noqa
        raw_value = dumps_cache_value(value)
        resolved_ttl = self._sync_client._resolve_ttl(ttl)  # noqa

        try:
            return await self._sync_client._backend.aadd(full_key, raw_value, resolved_ttl)  # noqa
        except NsValidationError:
            raise
        except Exception as exc:  # noqa
            self._sync_client._log_soft_failure("aadd", exc, key=key)  # noqa
            return False

    async def touch(self, key: str, ttl: Any = _TTL_UNSET) -> bool:
        full_key = self._sync_client._full_key(key)  # noqa
        resolved_ttl = self._sync_client._resolve_ttl(ttl)  # noqa

        try:
            return await self._sync_client._backend.atouch(full_key, resolved_ttl)  # noqa
        except NsValidationError:
            raise
        except Exception as exc:  # noqa
            self._sync_client._log_soft_failure("atouch", exc, key=key)  # noqa
            return False

    async def delete(self, key: str) -> bool:
        full_key = self._sync_client._full_key(key)  # noqa

        try:
            return await self._sync_client._backend.adelete(full_key)  # noqa
        except NsValidationError:
            raise
        except Exception as exc:  # noqa
            self._sync_client._log_soft_failure("adelete", exc, key=key)  # noqa
            return False

    async def delete_many(self, keys: list[str]) -> int:
        full_keys = [
            self._sync_client._full_key(key)  # noqa
            for key in keys
        ]

        try:
            return await self._sync_client._backend.adelete_many(full_keys)  # noqa
        except NsValidationError:
            raise
        except Exception as exc:  # noqa
            self._sync_client._log_soft_failure("adelete_many", exc)  # noqa
            return 0

    async def exists(self, key: str) -> bool:
        full_key = self._sync_client._full_key(key)  # noqa

        try:
            return await self._sync_client._backend.aexists(full_key)  # noqa
        except NsValidationError:
            raise
        except Exception as exc:  # noqa
            self._sync_client._log_soft_failure("aexists", exc, key=key)  # noqa
            return False

    async def clear(self) -> bool:
        try:
            return await self._sync_client._backend.aclear(self._sync_client._namespace_prefix())  # noqa
        except NsValidationError:
            raise
        except Exception as exc:  # noqa
            self._sync_client._log_soft_failure("aclear", exc)  # noqa
            return False

    async def incr(self, key: str, delta: int = 1) -> int:
        full_key = self._sync_client._full_key(key)  # noqa
        return await self._sync_client._backend.aincr(  # noqa
            full_key,
            self._sync_client._validate_delta(delta),  # noqa
        )

    async def decr(self, key: str, delta: int = 1) -> int:
        full_key = self._sync_client._full_key(key)  # noqa
        return await self._sync_client._backend.adecr(  # noqa
            full_key,
            self._sync_client._validate_delta(delta),  # noqa
        )

    async def cleanup_expired(self) -> int:
        try:
            return await self._sync_client._backend.acleanup_expired()  # noqa
        except Exception as exc:  # noqa
            self._sync_client._log_soft_failure("acleanup_expired", exc)  # noqa
            return 0
