# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
from typing import (
    Any,
    Literal,
    TYPE_CHECKING,
)
from urllib.parse import (
    urlparse,
    urlunparse,
)

from ns_common.cache.backends.redis import RedisCacheBackend
from ns_common.config import NsCacheConfig
from ns_common.exceptions import NsDependencyError

if TYPE_CHECKING:
    pass


class ValkeyCacheBackend(RedisCacheBackend):
    def __init__(self, config: NsCacheConfig) -> None:
        super().__init__(config=config)

    def initialize(self) -> None:
        valkey_module = self._load_valkey_module()
        async_valkey_module = self._load_async_valkey_module()
        cache_url = self._normalize_valkey_url(self._config.cache_url)

        self._client = valkey_module.from_url(
            cache_url,
            decode_responses=True,
        )

        self._client.ping()

        self._async_client = async_valkey_module.from_url(
            cache_url,
            decode_responses=True,
        )

    @staticmethod
    def _load_valkey_module() -> Any:
        try:
            return importlib.import_module("valkey")
        except ImportError as exc:
            raise NsDependencyError(
                "Python package 'valkey' is required.",
                details={
                    "package": "valkey",
                },
            ) from exc

    @staticmethod
    def _load_async_valkey_module() -> Any:
        try:
            return importlib.import_module("valkey.asyncio")
        except ImportError as exc:
            raise NsDependencyError(
                "Python package 'valkey' with asyncio support is required.",
                details={
                    "package": "valkey.asyncio",
                },
            ) from exc

    @staticmethod
    def _normalize_valkey_url(cache_url: str) -> Literal[b""] | str:
        parsed = urlparse(cache_url)

        if parsed.scheme == "redis":
            return urlunparse(parsed._replace(scheme="valkey"))

        if parsed.scheme == "rediss":
            return urlunparse(parsed._replace(scheme="valkeys"))

        return cache_url
