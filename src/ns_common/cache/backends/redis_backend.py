# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any



from ns_common.cache.config import NsCacheConfig
from ns_common.cache.exceptions import NsCacheConfigurationError, NsCacheConnectionError
from ns_common.cache.serializers import BaseCacheSerializer, build_serializer

if TYPE_CHECKING:
    pass
class RedisCacheBackend:
    def __init__(self, config: NsCacheConfig) -> None:
        if config.backend not in {"redis", "valkey"}:
            raise NsCacheConfigurationError(f"unsupported cache backend: {config.backend}")

        self._config: NsCacheConfig = config
        self._key_prefix: str = self._normalize_key_prefix(config.key_prefix)
        self._serializer: BaseCacheSerializer = build_serializer(config.serializer)
        import redis

        try:
            self._pool: redis.ConnectionPool = redis.ConnectionPool.from_url(
                self._normalize_url(config.url),
                max_connections=config.max_connections,
                socket_timeout=config.socket_timeout,
                socket_connect_timeout=config.socket_connect_timeout,
                health_check_interval=config.health_check_interval,
                decode_responses=False,
            )
            self._client: redis.Redis = redis.Redis(connection_pool=self._pool)
        except (TypeError, ValueError) as _error:
            raise NsCacheConfigurationError("invalid cache backend configuration") from _error

    def get(self, key: str, default: object | None = None) -> object | None:
        cache_key = self._make_key(key)
        try:
            payload: Any = self._client.get(cache_key)
        except self._connection_errors() as _error:
            raise self._build_connection_error(_error) from _error

        if payload is None:
            return default

        return self._serializer.loads(payload)

    def set(self, key: str, value: object, timeout: int | None = None) -> bool:
        cache_key = self._make_key(key)
        normalized_timeout = self._normalize_timeout(timeout)

        if normalized_timeout == 0:
            return False
        if normalized_timeout < 0:
            self.delete(key)
            return False

        payload = self._serializer.dumps(value)
        try:
            return bool(self._client.set(name=cache_key, value=payload, ex=normalized_timeout))
        except self._connection_errors() as _error:
            raise self._build_connection_error(_error) from _error

    def add(self, key: str, value: object, timeout: int | None = None) -> bool:
        cache_key = self._make_key(key)
        normalized_timeout = self._normalize_timeout(timeout)

        if normalized_timeout == 0:
            return False
        if normalized_timeout < 0:
            self.delete(key)
            return False

        payload = self._serializer.dumps(value)
        try:
            return bool(self._client.set(name=cache_key, value=payload, ex=normalized_timeout, nx=True))
        except self._connection_errors() as _error:
            raise self._build_connection_error(_error) from _error

    def delete(self, key: str) -> bool:
        cache_key = self._make_key(key)
        try:
            return int(self._client.delete(cache_key)) > 0
        except self._connection_errors() as _error:
            raise self._build_connection_error(_error) from _error

    def exists(self, key: str) -> bool:
        cache_key = self._make_key(key)
        try:
            return int(self._client.exists(cache_key)) > 0
        except self._connection_errors() as _error:
            raise self._build_connection_error(_error) from _error

    def expire(self, key: str, timeout: int) -> bool:
        cache_key = self._make_key(key)
        if timeout <= 0:
            return self.delete(key)

        try:
            return bool(self._client.expire(cache_key, timeout))
        except self._connection_errors() as _error:
            raise self._build_connection_error(_error) from _error

    def ttl(self, key: str) -> int:
        cache_key = self._make_key(key)
        try:
            return int(self._client.ttl(cache_key))
        except self._connection_errors() as _error:
            raise self._build_connection_error(_error) from _error

    def clear(self) -> bool:
        if not self._key_prefix:
            raise NsCacheConfigurationError("cache key_prefix is required when clearing cache")

        pattern = f"{self._key_prefix}:*"
        batch_size = 1000
        batch: list[str] = []

        try:
            for cache_key in self._client.scan_iter(match=pattern, count=batch_size):
                batch.append(cache_key)
                if len(batch) >= batch_size:
                    self._delete_cache_key_batch(batch)
                    batch.clear()

            if batch:
                self._delete_cache_key_batch(batch)

            return True
        except self._connection_errors() as _error:
            raise self._build_connection_error(_error) from _error

    def get_many(self, keys: list[str]) -> dict[str, object]:
        if not keys:
            return {}

        cache_keys = [self._make_key(key) for key in keys]

        try:
            payloads: list[Any] = self._client.mget(cache_keys)
        except self._connection_errors() as _error:
            raise self._build_connection_error(_error) from _error

        result: dict[str, object] = {}
        for key, payload in zip(keys, payloads):
            if payload is None:
                continue
            result[key] = self._serializer.loads(payload)

        return result

    def set_many(self, data: dict[str, object], timeout: int | None = None) -> list[str]:
        if not data:
            return []

        normalized_timeout = self._normalize_timeout(timeout)
        keys = list(data.keys())

        if normalized_timeout == 0:
            return keys
        if normalized_timeout < 0:
            self.delete_many(keys)
            return keys

        entries: list[tuple[str, str, bytes]] = []
        for key, value in data.items():
            entries.append((key, self._make_key(key), self._serializer.dumps(value)))

        try:
            pipeline = self._client.pipeline(transaction=False)
            for _, cache_key, payload in entries:
                pipeline.set(name=cache_key, value=payload, ex=normalized_timeout)
            results: list[Any] = pipeline.execute()
        except self._connection_errors() as _error:
            raise self._build_connection_error(_error) from _error

        return [key for key, result in zip(keys, results) if not bool(result)]

    def delete_many(self, keys: list[str]) -> int:
        if not keys:
            return 0

        cache_keys = [self._make_key(key) for key in keys]

        try:
            return int(self._client.delete(*cache_keys))
        except self._connection_errors() as _error:
            raise self._build_connection_error(_error) from _error

    def close(self) -> None:
        try:
            self._client.close()
        except Exception:
            pass

        try:
            self._pool.disconnect()
        except Exception:
            pass

    def _make_key(self, key: str) -> str:
        if not isinstance(key, str) or not key.strip():
            raise NsCacheConfigurationError("cache key must be a non-empty str")

        normalized_key = key.strip()
        if not self._key_prefix:
            return normalized_key

        if normalized_key == self._key_prefix or normalized_key.startswith(f"{self._key_prefix}:"):
            return normalized_key

        return f"{self._key_prefix}:{normalized_key}"

    def _normalize_timeout(self, timeout: int | None) -> int:
        selected_timeout = self._config.default_timeout if timeout is None else timeout
        if isinstance(selected_timeout, bool) or not isinstance(selected_timeout, int):
            raise NsCacheConfigurationError("cache timeout must be int or None")
        if selected_timeout > 0:
            return selected_timeout
        if selected_timeout == 0:
            return 0
        return -1

    def _delete_cache_key_batch(self, keys: list[str]) -> None:
        if not keys:
            return

        pipeline = self._client.pipeline(transaction=False)
        pipeline.delete(*keys)
        pipeline.execute()

    @staticmethod
    def _normalize_url(url: str) -> str:
        if not isinstance(url, str) or not url.strip():
            raise NsCacheConfigurationError("cache url must be a non-empty str")

        normalized_url = url.strip()
        if normalized_url.lower().startswith("valkey://"):
            return f"redis://{normalized_url[len('valkey://'):]}"
        return normalized_url

    @staticmethod
    def _normalize_key_prefix(key_prefix: str) -> str:
        if key_prefix is None:
            return ""
        if not isinstance(key_prefix, str):
            raise NsCacheConfigurationError("cache key_prefix must be str")
        return key_prefix.strip().strip(":")

    @staticmethod
    def _connection_errors() -> tuple[type[BaseException], ...]:
        from redis import RedisError
        return RedisError, OSError, ConnectionError, TimeoutError

    @staticmethod
    def _build_connection_error(_error: BaseException) -> NsCacheConnectionError:
        return NsCacheConnectionError("cache backend operation failed")
