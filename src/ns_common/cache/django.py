# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING
)

from django.core.cache.backends.base import (
    BaseCache,
    DEFAULT_TIMEOUT
)

from ns_common.cache.clients import (
    _TTL_UNSET,
    get_cache_client,
)
from ns_common.exceptions import NsStateError

if TYPE_CHECKING:
    pass


class NsDjangoCacheBackend(BaseCache):
    def __init__(self, location: str, params: dict[str, Any]) -> None:
        from ns_common.config import ns_config

        super().__init__(params)

        self._location = location
        self._client = get_cache_client(
            namespace=ns_config.cache.django_namespace,
        )

    def _build_django_key(self, key: str, version: int | None = None) -> str:
        resolved_version = self.version if version is None else version
        return f"v{resolved_version}:{key}"

    @staticmethod
    def _convert_timeout(timeout: Any) -> Any:
        if timeout is DEFAULT_TIMEOUT:
            return _TTL_UNSET

        return timeout

    def add(self, key: str, value: Any, timeout: Any = DEFAULT_TIMEOUT, version: int | None = None) -> bool:
        return self._client.add(
            self._build_django_key(key, version),
            value,
            ttl=self._convert_timeout(timeout),
        )

    def get(self, key: str, default: Any = None, version: int | None = None) -> Any:
        return self._client.get(
            self._build_django_key(key, version),
            default=default,
        )

    def set(self, key: str, value: Any, timeout: Any = DEFAULT_TIMEOUT, version: int | None = None) -> bool:
        return self._client.set(
            self._build_django_key(key, version),
            value,
            ttl=self._convert_timeout(timeout),
        )

    def touch(self, key: str, timeout: Any = DEFAULT_TIMEOUT, version: int | None = None) -> bool:
        return self._client.touch(
            self._build_django_key(key, version),
            ttl=self._convert_timeout(timeout),
        )

    def delete(self, key: str, version: int | None = None) -> bool:
        return self._client.delete(
            self._build_django_key(key, version),
        )

    def clear(self) -> bool:
        return self._client.clear()

    def get_many(self, keys: list[str], version: int | None = None) -> dict[str, Any]:
        django_key_map = {
            self._build_django_key(key, version): key
            for key in keys
        }

        values = self._client.get_many(list(django_key_map.keys()))

        return {
            django_key_map[django_key]: value
            for django_key, value in values.items()
            if django_key in django_key_map
        }

    def set_many(self, data: dict[str, Any], timeout: Any = DEFAULT_TIMEOUT, version: int | None = None) -> list[str]:
        mapping = {
            self._build_django_key(key, version): value
            for key, value in data.items()
        }

        ok = self._client.set_many(
            mapping,
            ttl=self._convert_timeout(timeout),
        )

        return [] if ok else list(data.keys())

    def delete_many(self, keys: list[str], version: int | None = None) -> None:
        self._client.delete_many(
            [
                self._build_django_key(key, version)
                for key in keys
            ]
        )

    def incr(self, key: str, delta: int = 1, version: int | None = None) -> int:
        try:
            return self._client.incr(
                self._build_django_key(key, version),
                delta=delta,
            )
        except NsStateError as exc:
            raise ValueError(f"Key '{key}' not found or is not an integer.") from exc

    def decr(self, key: str, delta: int = 1, version: int | None = None) -> int:
        try:
            return self._client.decr(
                self._build_django_key(key, version),
                delta=delta,
            )
        except NsStateError as exc:
            raise ValueError(f"Key '{key}' not found or is not an integer.") from exc
