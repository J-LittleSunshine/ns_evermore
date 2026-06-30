# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from typing import (
    Any,
    Mapping,
    TYPE_CHECKING,
)

from ns_common.exceptions import (
    NsDependencyError,
    NsStateError,
)

if TYPE_CHECKING:
    import httpx as _httpx

_httpx_module: Any | None = None


def _get_httpx() -> Any:
    global _httpx_module

    if _httpx_module is not None:
        return _httpx_module

    try:
        import httpx as imported_httpx
    except ModuleNotFoundError as error:
        raise NsDependencyError(
            "Python package 'httpx' is required for ns_common async HTTP client.",
            details={
                "package": "httpx",
                "component": "ns_common.http_client",
            },
        ) from error

    _httpx_module = imported_httpx
    return _httpx_module


class AsyncHttpClientManager:
    _client: Any | None = None
    _lock: asyncio.Lock | None = None

    _timeout_seconds: float = 10.0
    _connect_timeout_seconds: float = 5.0
    _max_connections: int = 100
    _max_keepalive_connections: int = 20
    _default_headers: dict[str, str] = {}
    _verify: bool = True
    _trust_env: bool = True

    @classmethod
    def configure(cls, *, timeout_seconds: float = 10.0, connect_timeout_seconds: float = 5.0, max_connections: int = 100, max_keepalive_connections: int = 20, default_headers: Mapping[str, str] | None = None, verify: bool = True, trust_env: bool = True) -> None:
        if cls._client is not None and not cls._client.is_closed:
            raise NsStateError(
                "Async HTTP client is already initialized. Close it before reconfiguring.",
                details={
                    "component": "ns_common.http_client",
                },
            )

        cls._validate_positive_number("timeout_seconds", timeout_seconds)
        cls._validate_positive_number("connect_timeout_seconds", connect_timeout_seconds)
        cls._validate_positive_int("max_connections", max_connections)
        cls._validate_positive_int("max_keepalive_connections", max_keepalive_connections)

        if max_keepalive_connections > max_connections:
            raise NsStateError(
                "max_keepalive_connections must not exceed max_connections.",
                details={
                    "max_connections": max_connections,
                    "max_keepalive_connections": max_keepalive_connections,
                },
            )

        cls._timeout_seconds = float(timeout_seconds)
        cls._connect_timeout_seconds = float(connect_timeout_seconds)
        cls._max_connections = int(max_connections)
        cls._max_keepalive_connections = int(max_keepalive_connections)
        cls._default_headers = dict(default_headers or {})
        cls._verify = bool(verify)
        cls._trust_env = bool(trust_env)

    @classmethod
    async def get_client(cls) -> "_httpx.AsyncClient":
        if cls._client is not None and not cls._client.is_closed:
            return cls._client

        lock = cls._get_lock()
        async with lock:
            if cls._client is not None and not cls._client.is_closed:
                return cls._client

            cls._client = cls._build_client()
            return cls._client

    @classmethod
    async def request(cls, method: str, url: str, *, raise_for_status: bool = False, **kwargs: Any) -> "_httpx.Response":
        client = await cls.get_client()
        response = await client.request(method=method, url=url, **kwargs)

        if raise_for_status:
            response.raise_for_status()

        return response

    @classmethod
    async def post_json(cls, url: str, *, json: Any, headers: Mapping[str, str] | None = None, raise_for_status: bool = False, **kwargs: Any) -> "_httpx.Response":
        merged_headers = dict(headers or {})
        merged_headers.setdefault("Content-Type", "application/json")

        return await cls.request(
            "POST",
            url,
            headers=merged_headers,
            json=json,
            raise_for_status=raise_for_status,
            **kwargs,
        )

    @classmethod
    async def close(cls) -> None:
        client = cls._client
        cls._client = None

        if client is not None and not client.is_closed:
            await client.aclose()

    @classmethod
    async def aclose(cls) -> None:
        await cls.close()

    @classmethod
    def _build_client(cls) -> "_httpx.AsyncClient":
        httpx = _get_httpx()

        timeout = httpx.Timeout(
            cls._timeout_seconds,
            connect=cls._connect_timeout_seconds,
        )

        limits = httpx.Limits(
            max_connections=cls._max_connections,
            max_keepalive_connections=cls._max_keepalive_connections,
        )

        return httpx.AsyncClient(
            timeout=timeout,
            limits=limits,
            headers=cls._default_headers,
            verify=cls._verify,
            trust_env=cls._trust_env,
        )

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        if cls._lock is None:
            cls._lock = asyncio.Lock()

        return cls._lock

    @staticmethod
    def _validate_positive_number(field_name: str, value: Any) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or float(value) <= 0:
            raise NsStateError(
                f"{field_name} must be a positive number.",
                details={
                    "field": field_name,
                    "value": value,
                    "actual_type": type(value).__name__,
                },
            )

    @staticmethod
    def _validate_positive_int(field_name: str, value: Any) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise NsStateError(
                f"{field_name} must be a positive integer.",
                details={
                    "field": field_name,
                    "value": value,
                    "actual_type": type(value).__name__,
                },
            )
