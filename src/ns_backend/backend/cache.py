# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
from dataclasses import replace
from typing import Any, Literal, cast

from django.core.cache.backends.base import BaseCache, DEFAULT_TIMEOUT

from ns_common.cache import NS_CACHE_DEFAULT_TIMEOUT, NsCacheClient, NsCacheConfigurationError, _DefaultCacheTimeout
from ns_common.config import _NsCacheConfig, ns_config


class NsDjangoCacheBackend(BaseCache):
    """Django cache backend adapter for NsCacheClient."""

    def __init__(self, location: str, params: dict[str, Any]) -> None:
        """Initialize Django cache backend."""
        super().__init__(params)

        options: dict[str, Any] = self._get_options(params)
        base_config: _NsCacheConfig = ns_config.cache_config
        config: _NsCacheConfig = self._build_config(base_config, location, options)
        client_name: str = self._build_client_name(config, options)

        self._client: NsCacheClient = NsCacheClient(client_name, config)

    def get(self, key: str, default: object | None = None, version: int | None = None) -> object | None:
        """Get value from NsCacheClient."""
        cache_key: str = self.make_and_validate_key(key, version=version)
        return self._client.get(cache_key, default)

    def set(self, key: str, value: object, timeout: object = DEFAULT_TIMEOUT, version: int | None = None) -> bool:
        """Set value through NsCacheClient."""
        cache_key: str = self.make_and_validate_key(key, version=version)
        resolved_timeout: int | None | _DefaultCacheTimeout = self._resolve_django_timeout(timeout)

        if isinstance(resolved_timeout, int) and resolved_timeout <= 0:
            self._client.delete(cache_key)
            return False

        return self._client.set(cache_key, value, resolved_timeout)

    def add(self, key: str, value: object, timeout: object = DEFAULT_TIMEOUT, version: int | None = None) -> bool:
        """Add value only when key does not exist."""
        cache_key: str = self.make_and_validate_key(key, version=version)
        resolved_timeout: int | None | _DefaultCacheTimeout = self._resolve_django_timeout(timeout)

        if isinstance(resolved_timeout, int) and resolved_timeout <= 0:
            return False

        return self._client.add(cache_key, value, resolved_timeout)

    def delete(self, key: str, version: int | None = None) -> bool:
        """Delete value."""
        cache_key: str = self.make_and_validate_key(key, version=version)
        return self._client.delete(cache_key)

    def clear(self) -> bool:
        """Clear cache entries under current ns key prefix."""
        return self._client.clear()

    def get_many(self, keys: list[str], version: int | None = None) -> dict[str, object]:
        """Get many values."""
        if not keys:
            return {}

        cache_key_map: dict[str, str] = {}
        for key in keys:
            cache_key_map[self.make_and_validate_key(key, version=version)] = key

        raw_result: dict[str, object] = self._client.get_many(list(cache_key_map.keys()))

        result: dict[str, object] = {}
        for cache_key, value in raw_result.items():
            original_key: str | None = cache_key_map.get(cache_key)
            if original_key is not None:
                result[original_key] = value

        return result

    def set_many(self, data: dict[str, object], timeout: object = DEFAULT_TIMEOUT, version: int | None = None) -> list[str]:
        """Set many values."""
        if not data:
            return []

        resolved_timeout: int | None | _DefaultCacheTimeout = self._resolve_django_timeout(timeout)

        cache_key_map: dict[str, str] = {}
        cache_data: dict[str, object] = {}

        for key, value in data.items():
            cache_key: str = self.make_and_validate_key(key, version=version)
            cache_key_map[cache_key] = key
            cache_data[cache_key] = value

        if isinstance(resolved_timeout, int) and resolved_timeout <= 0:
            self._client.delete_many(list(cache_data.keys()))
            return list(data.keys())

        failed_cache_keys: list[str] = self._client.set_many(cache_data, resolved_timeout)
        return [cache_key_map[cache_key] for cache_key in failed_cache_keys if cache_key in cache_key_map]

    def delete_many(self, keys: list[str], version: int | None = None) -> int:
        """Delete many values."""
        if not keys:
            return 0

        cache_keys: list[str] = [self.make_and_validate_key(key, version=version) for key in keys]
        return self._client.delete_many(cache_keys)

    def has_key(self, key: str, version: int | None = None) -> bool:
        """Check whether key exists."""
        cache_key: str = self.make_and_validate_key(key, version=version)
        return self._client.exists(cache_key)

    def touch(self, key: str, timeout: object = DEFAULT_TIMEOUT, version: int | None = None) -> bool:
        """Update key timeout."""
        cache_key: str = self.make_and_validate_key(key, version=version)
        resolved_timeout: int | None | _DefaultCacheTimeout = self._resolve_django_timeout(timeout)

        selected_timeout: int | None
        if isinstance(resolved_timeout, _DefaultCacheTimeout):
            selected_timeout = self._client.config.default_timeout_seconds
        else:
            selected_timeout = resolved_timeout

        if selected_timeout is None:
            return self._client.persist(cache_key)

        if selected_timeout <= 0:
            return self._client.delete(cache_key)

        return self._client.expire(cache_key, selected_timeout)

    def close(self) -> None:
        """Close cache backend."""
        self._client.close()

    @staticmethod
    def _resolve_django_timeout(timeout: object) -> int | None | _DefaultCacheTimeout:
        """Resolve Django timeout semantics."""
        if timeout is DEFAULT_TIMEOUT:
            return NS_CACHE_DEFAULT_TIMEOUT

        if timeout is None:
            return None

        if isinstance(timeout, bool):
            raise NsCacheConfigurationError("django cache timeout must be int or None")

        try:
            return int(str(timeout))
        except (TypeError, ValueError) as _error:
            raise NsCacheConfigurationError("django cache timeout must be int or None") from _error

    def _build_config(self, base_config: _NsCacheConfig, location: str, options: dict[str, Any]) -> _NsCacheConfig:
        """Build NsCacheClient config from Django cache settings."""
        selected_location: str = str(location or base_config.location or "").strip()
        selected_key_prefix: str = self._get_str_option(options, "ns_key_prefix", "NS_KEY_PREFIX", default=base_config.key_prefix)

        selected_backend = cast(
            Literal["default", "sql_wal", "redis", "valkey"],
            self._get_str_option(options, "ns_backend", "NS_BACKEND", default=base_config.backend),
        )

        selected_serializer = cast(
            Literal["pickle", "json", "raw"],
            self._get_str_option(options, "ns_serializer", "NS_SERIALIZER", default=base_config.serializer),
        )

        return replace(
            base_config,
            backend=selected_backend,
            location=selected_location,
            key_prefix=selected_key_prefix,
            default_timeout_seconds=self._resolve_base_cache_default_timeout(base_config.default_timeout_seconds),
            serializer=selected_serializer,
        )

    def _resolve_base_cache_default_timeout(self, default: int | None) -> int | None:
        """Resolve Django TIMEOUT as NsCacheClient default timeout."""
        value: object = getattr(self, "default_timeout", default)

        if value is None:
            return None

        if isinstance(value, bool):
            raise NsCacheConfigurationError("django cache TIMEOUT must be int or None")

        try:
            parsed_value: int = int(str(value))
        except (TypeError, ValueError) as _error:
            raise NsCacheConfigurationError("django cache TIMEOUT must be int or None") from _error

        if parsed_value < 0:
            raise NsCacheConfigurationError("django cache TIMEOUT must be >= 0 or None")

        return parsed_value

    @classmethod
    def _build_client_name(cls, config: _NsCacheConfig, options: dict[str, Any]) -> str:
        """Build stable process-local cache client name."""
        explicit_name: str = str(options.get("client_name") or options.get("CLIENT_NAME") or "").strip()
        if explicit_name:
            return explicit_name

        fingerprint_source: str = (
            f"{config.backend}|{config.location}|{config.key_prefix}|{config.serializer}|"
            f"{config.default_timeout_seconds}|{config.sql_table}|{config.socket_timeout}|"
            f"{config.socket_connect_timeout}|{config.max_connections}|{config.health_check_interval}"
        )
        fingerprint: str = hashlib.sha1(fingerprint_source.encode("utf-8")).hexdigest()[:16]
        return f"django-cache-{fingerprint}"

    @staticmethod
    def _get_options(params: dict[str, Any]) -> dict[str, Any]:
        """Get Django cache OPTIONS."""
        raw_options: object = params.get("OPTIONS", {})
        if raw_options is None:
            return {}
        if not isinstance(raw_options, dict):
            raise NsCacheConfigurationError("django cache OPTIONS must be a dict")
        return dict(raw_options)

    @staticmethod
    def _get_str_option(options: dict[str, Any], *keys: str, default: str) -> str:
        """Get string option."""
        for key in keys:
            value: object = options.get(key)
            if value is None:
                continue

            text: str = str(value).strip()
            if text:
                return text

        return str(default or "").strip()
