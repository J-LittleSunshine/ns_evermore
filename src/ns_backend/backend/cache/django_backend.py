# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
from typing import TYPE_CHECKING, Any, Mapping, Literal

from django.core.cache.backends.base import BaseCache, DEFAULT_TIMEOUT

from ns_common.cache import NsCacheConfig, NsCacheClient, NsCacheConfigurationError, NsCacheConnectionError
from ns_common.cache.backends import RedisCacheBackend

if TYPE_CHECKING:
    pass


class NsCommonCacheBackend(BaseCache):
    def __init__(self, location: str, params: dict[str, Any]) -> None:
        super().__init__(params)

        options = self._get_options(params)
        self._config: NsCacheConfig = self._build_config(location, options)
        self._client_name: str = self._build_client_name(self._config, options)
        self._client: NsCacheClient = NsCacheClient.get_or_create(self._client_name, self._config)

    def get(self, key: str, default: object | None = None, version: int | None = None) -> object | None:
        cache_key = self.make_and_validate_key(key, version=version)
        return self._client.get(cache_key, default)

    def set(self, key: str, value: object, timeout: object = DEFAULT_TIMEOUT, version: int | None = None) -> bool:
        cache_key = self.make_and_validate_key(key, version=version)
        normalized_timeout = self._resolve_timeout(timeout)

        if normalized_timeout is None:
            return self._set_forever(cache_key, value)

        if normalized_timeout <= 0:
            self._client.delete(cache_key)
            return False

        return self._client.set(cache_key, value, normalized_timeout)

    def add(self, key: str, value: object, timeout: object = DEFAULT_TIMEOUT, version: int | None = None) -> bool:
        cache_key = self.make_and_validate_key(key, version=version)
        normalized_timeout = self._resolve_timeout(timeout)

        if normalized_timeout is None:
            return self._add_forever(cache_key, value)

        if normalized_timeout <= 0:
            return False

        return self._client.add(cache_key, value, normalized_timeout)

    def delete(self, key: str, version: int | None = None) -> bool:
        cache_key = self.make_and_validate_key(key, version=version)
        return self._client.delete(cache_key)

    def clear(self) -> bool:
        return self._client.clear()

    def get_many(self, keys: list[str], version: int | None = None) -> dict[str, object]:
        if not keys:
            return {}

        cache_key_map: dict[str, str] = {}
        for key in keys:
            cache_key_map[self.make_and_validate_key(key, version=version)] = key

        raw_result = self._client.get_many(list(cache_key_map.keys()))
        result: dict[str, object] = {}
        for cache_key, value in raw_result.items():
            original_key = cache_key_map.get(cache_key)
            if original_key is not None:
                result[original_key] = value

        return result

    def set_many(self, data: dict[str, object], timeout: object = DEFAULT_TIMEOUT, version: int | None = None) -> list[str]:
        if not data:
            return []

        normalized_timeout = self._resolve_timeout(timeout)

        cache_key_map: dict[str, str] = {}
        cache_data: dict[str, object] = {}
        for key, value in data.items():
            cache_key = self.make_and_validate_key(key, version=version)
            cache_key_map[cache_key] = key
            cache_data[cache_key] = value

        if normalized_timeout is None:
            failed_cache_keys = self._set_many_forever(cache_data)
            return [cache_key_map[cache_key] for cache_key in failed_cache_keys if cache_key in cache_key_map]

        if normalized_timeout <= 0:
            self._client.delete_many(list(cache_data.keys()))
            return list(data.keys())

        failed_cache_keys = self._client.set_many(cache_data, normalized_timeout)
        return [cache_key_map[cache_key] for cache_key in failed_cache_keys if cache_key in cache_key_map]

    def delete_many(self, keys: list[str], version: int | None = None) -> int:
        if not keys:
            return 0

        cache_keys = [self.make_and_validate_key(key, version=version) for key in keys]
        return self._client.delete_many(cache_keys)

    def has_key(self, key: str, version: int | None = None) -> bool:
        cache_key = self.make_and_validate_key(key, version=version)
        return self._client.exists(cache_key)

    def touch(self, key: str, timeout: object = DEFAULT_TIMEOUT, version: int | None = None) -> bool:
        cache_key = self.make_and_validate_key(key, version=version)
        normalized_timeout = self._resolve_timeout(timeout)

        if normalized_timeout is None:
            return self._persist(cache_key)

        if normalized_timeout <= 0:
            return self._client.delete(cache_key)

        return self._client.expire(cache_key, normalized_timeout)

    def close(self) -> None:
        self._client.close()

    def _resolve_timeout(self, timeout: object) -> int | None:
        if timeout is DEFAULT_TIMEOUT:
            selected_timeout = self.default_timeout
        else:
            selected_timeout = timeout

        if selected_timeout is None:
            return None

        if isinstance(selected_timeout, bool):
            raise NsCacheConfigurationError("django cache timeout must be int or None")

        try:
            return int(selected_timeout)
        except (TypeError, ValueError) as _error:
            raise NsCacheConfigurationError("django cache timeout must be int or None") from _error

    def _set_forever(self, cache_key: str, value: object) -> bool:
        backend = self._get_redis_backend()
        payload = backend._serializer.dumps(value)
        redis_key = backend._make_key(cache_key)

        try:
            return bool(backend._client.set(name=redis_key, value=payload))
        except backend._connection_errors() as _error:
            raise self._build_connection_error(_error) from _error

    def _add_forever(self, cache_key: str, value: object) -> bool:
        backend = self._get_redis_backend()
        payload = backend._serializer.dumps(value)
        redis_key = backend._make_key(cache_key)

        try:
            return bool(backend._client.set(name=redis_key, value=payload, nx=True))
        except backend._connection_errors() as _error:
            raise self._build_connection_error(_error) from _error

    def _set_many_forever(self, data: dict[str, object]) -> list[str]:
        if not data:
            return []

        backend = self._get_redis_backend()
        entries: list[tuple[str, str, bytes]] = []
        for cache_key, value in data.items():
            entries.append((cache_key, backend._make_key(cache_key), backend._serializer.dumps(value)))

        try:
            pipeline = backend._client.pipeline(transaction=False)
            for _, redis_key, payload in entries:
                pipeline.set(name=redis_key, value=payload)
            results: list[Any] = pipeline.execute()
        except backend._connection_errors() as _error:
            raise self._build_connection_error(_error) from _error

        return [cache_key for cache_key, result in zip(data.keys(), results) if not bool(result)]

    def _persist(self, cache_key: str) -> bool:
        backend = self._get_redis_backend()
        redis_key = backend._make_key(cache_key)

        try:
            if int(backend._client.exists(redis_key)) <= 0:
                return False
            backend._client.persist(redis_key)
            return True
        except backend._connection_errors() as _error:
            raise self._build_connection_error(_error) from _error

    def _get_redis_backend(self) -> RedisCacheBackend:
        backend = self._client._backend
        if not isinstance(backend, RedisCacheBackend):
            raise NsCacheConfigurationError("django cache backend only supports redis-compatible ns_common cache backend")
        return backend

    @staticmethod
    def _get_options(params: dict[str, Any]) -> dict[str, Any]:
        raw_options = params.get("OPTIONS", {})
        if raw_options is None:
            return {}
        if not isinstance(raw_options, dict):
            raise NsCacheConfigurationError("django cache OPTIONS must be a dict")
        return dict(raw_options)

    def _build_config(self, location: str, options: Mapping[str, Any]) -> NsCacheConfig:
        url = str(options.get("url") or options.get("URL") or location or "").strip()
        if not url:
            raise NsCacheConfigurationError("django cache LOCATION or OPTIONS.url is required")

        backend = str(options.get("backend") or options.get("BACKEND_TYPE") or self._infer_backend(url)).strip().lower()
        if backend not in {"redis", "valkey"}:
            raise NsCacheConfigurationError(f"unsupported django cache backend type: {backend}")

        config_default_timeout = self.default_timeout if isinstance(self.default_timeout, int) and self.default_timeout > 0 else 300

        return NsCacheConfig(
            backend=backend,
            url=url,
            key_prefix=self._get_str_option(options, "ns_key_prefix", "NS_KEY_PREFIX", default="ns-django-cache"),
            default_timeout=config_default_timeout,
            socket_timeout=self._get_float_option(options, "socket_timeout", "SOCKET_TIMEOUT", default=3.0),
            socket_connect_timeout=self._get_float_option(options, "socket_connect_timeout", "SOCKET_CONNECT_TIMEOUT", default=3.0),
            max_connections=self._get_int_option(options, "max_connections", "MAX_CONNECTIONS", default=64),
            health_check_interval=self._get_int_option(options, "health_check_interval", "HEALTH_CHECK_INTERVAL", default=30),
            serializer=self._get_str_option(options, "serializer", "SERIALIZER", default="pickle"),
            decode_responses=False,
        )

    @classmethod
    def _build_client_name(cls, config: NsCacheConfig, options: Mapping[str, Any]) -> str:
        explicit_name = str(options.get("client_name") or options.get("CLIENT_NAME") or "").strip()
        if explicit_name:
            return explicit_name

        fingerprint_source = (
            f"{config.backend}|{config.url}|{config.key_prefix}|{config.serializer}|"
            f"{config.default_timeout}|{config.socket_timeout}|{config.socket_connect_timeout}|"
            f"{config.max_connections}|{config.health_check_interval}"
        )
        fingerprint = hashlib.sha1(fingerprint_source.encode("utf-8")).hexdigest()[:16]
        return f"django-cache-{fingerprint}"

    @staticmethod
    def _infer_backend(url: str) -> str:
        normalized_url = url.strip().lower()
        if normalized_url.startswith("valkey://"):
            return "valkey"
        return "redis"

    @staticmethod
    def _get_str_option(options: Mapping[str, Any], *keys: str, default: Literal["pickle", "json", "raw"]) -> Literal["pickle", "json", "raw"]:
        for key in keys:
            value = options.get(key)
            if value is None:
                continue
            text: Literal["pickle", "json", "raw"] = str(value).strip()
            if text:
                return text
        return default

    @staticmethod
    def _get_int_option(options: Mapping[str, Any], *keys: str, default: int) -> int:
        for key in keys:
            value = options.get(key)
            if value is None:
                continue
            if isinstance(value, bool):
                raise NsCacheConfigurationError(f"django cache option {key} must be int")
            try:
                parsed_value = int(value)
            except (TypeError, ValueError) as _error:
                raise NsCacheConfigurationError(f"django cache option {key} must be int") from _error
            if parsed_value <= 0:
                raise NsCacheConfigurationError(f"django cache option {key} must be positive int")
            return parsed_value
        return default

    @staticmethod
    def _get_float_option(options: Mapping[str, Any], *keys: str, default: float) -> float:
        for key in keys:
            value = options.get(key)
            if value is None:
                continue
            if isinstance(value, bool):
                raise NsCacheConfigurationError(f"django cache option {key} must be float")
            try:
                parsed_value = float(value)
            except (TypeError, ValueError) as _error:
                raise NsCacheConfigurationError(f"django cache option {key} must be float") from _error
            if parsed_value <= 0:
                raise NsCacheConfigurationError(f"django cache option {key} must be positive float")
            return parsed_value
        return default

    @staticmethod
    def _build_connection_error(_error: BaseException) -> NsCacheConnectionError:
        return NsCacheConnectionError("cache backend operation failed")
