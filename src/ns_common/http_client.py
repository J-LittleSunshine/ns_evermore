# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from dataclasses import dataclass
from threading import RLock
from typing import (
    Any,
    Collection,
    Mapping,
)

import httpx

from ns_common.exceptions import NsDependencyError
from ns_common.logger import get_ns_logger

_DEFAULT_TIMEOUT_SECONDS = 10.0
_DEFAULT_MAX_CONNECTIONS = 100
_DEFAULT_MAX_KEEPALIVE_CONNECTIONS = 20

_CLIENT_LOCK: RLock = RLock()
_CLIENT_MAP: dict[str, "NsAsyncHttpClient"] = {}


@dataclass(slots=True, kw_only=True)
class NsHttpResponse:
    status_code: int
    headers: dict[str, str]
    text: str
    url: str
    method: str

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> Any:
        if not self.text:
            return None

        try:
            return json.loads(self.text)
        except json.JSONDecodeError as exc:
            raise NsDependencyError(
                "HTTP response body is not valid JSON.",
                details={
                    "method": self.method,
                    "url": self.url,
                    "status_code": self.status_code,
                    "body_preview": self.text[:500],
                },
            ) from exc


class NsAsyncHttpClient:
    def __init__(
            self,
            *,
            name: str,
            base_url: str = "",
            timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
            default_headers: Mapping[str, str] | None = None,
            verify: bool = True,
            max_connections: int = _DEFAULT_MAX_CONNECTIONS,
            max_keepalive_connections: int = _DEFAULT_MAX_KEEPALIVE_CONNECTIONS
    ) -> None:
        self.name: str = name
        self.base_url: str = base_url.rstrip("/")
        self.timeout_seconds: float = timeout_seconds
        self.default_headers: dict[str, str] = dict(default_headers or {})
        self.verify: bool = verify
        self.max_connections: int = max_connections
        self.max_keepalive_connections: int = max_keepalive_connections

        self._logger = get_ns_logger(f"ns_http_client.{self.name}")
        self._client: httpx.AsyncClient = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(timeout_seconds),
            headers=self.default_headers,
            verify=verify,
            limits=httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive_connections,
            ),
        )
        self._closed: bool = False

    async def request(
            self,
            method: str,
            url: str,
            *,
            params: Mapping[str, Any] | None = None,
            headers: Mapping[str, str] | None = None,
            json_data: Any = None,
            data: Any = None,
            bearer_token: str | None = None,
            trace_id: str | None = None,
            expected_statuses: Collection[int] | None = None,
            raise_for_status: bool = True,
    ) -> NsHttpResponse:
        self._ensure_open()

        method_text = method.upper().strip()
        request_headers = self._build_headers(
            headers=headers,
            bearer_token=bearer_token,
            trace_id=trace_id,
        )

        try:
            response = await self._client.request(
                method_text,
                url,
                params=params,
                headers=request_headers,
                json=json_data,
                data=data,
            )
        except httpx.TimeoutException as exc:
            raise NsDependencyError(
                "HTTP request timed out.",
                details={
                    "client": self.name,
                    "method": method_text,
                    "url": self._safe_url(url),
                    "timeout_seconds": self.timeout_seconds,
                },
            ) from exc
        except httpx.RequestError as exc:
            raise NsDependencyError(
                "HTTP request failed.",
                details={
                    "client": self.name,
                    "method": method_text,
                    "url": self._safe_url(url),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            ) from exc

        result = NsHttpResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            text=response.text,
            url=str(response.url),
            method=method_text,
        )

        self._logger.info(
            "HTTP request completed.",
            extra={
                "client": self.name,
                "method": method_text,
                "url": str(response.url),
                "status_code": response.status_code,
            },
        )

        self._validate_response_status(
            response=result,
            expected_statuses=expected_statuses,
            raise_for_status=raise_for_status,
        )

        return result

    async def get(
            self,
            url: str,
            *,
            params: Mapping[str, Any] | None = None,
            headers: Mapping[str, str] | None = None,
            bearer_token: str | None = None,
            trace_id: str | None = None,
            expected_statuses: Collection[int] | None = None,
            raise_for_status: bool = True,
    ) -> NsHttpResponse:
        return await self.request(
            "GET",
            url,
            params=params,
            headers=headers,
            bearer_token=bearer_token,
            trace_id=trace_id,
            expected_statuses=expected_statuses,
            raise_for_status=raise_for_status,
        )

    async def post(
            self,
            url: str,
            *,
            params: Mapping[str, Any] | None = None,
            headers: Mapping[str, str] | None = None,
            json_data: Any = None,
            data: Any = None,
            bearer_token: str | None = None,
            trace_id: str | None = None,
            expected_statuses: Collection[int] | None = None,
            raise_for_status: bool = True,
    ) -> NsHttpResponse:
        return await self.request(
            "POST",
            url,
            params=params,
            headers=headers,
            json_data=json_data,
            data=data,
            bearer_token=bearer_token,
            trace_id=trace_id,
            expected_statuses=expected_statuses,
            raise_for_status=raise_for_status,
        )

    async def put(
            self,
            url: str,
            *,
            params: Mapping[str, Any] | None = None,
            headers: Mapping[str, str] | None = None,
            json_data: Any = None,
            data: Any = None,
            bearer_token: str | None = None,
            trace_id: str | None = None,
            expected_statuses: Collection[int] | None = None,
            raise_for_status: bool = True,
    ) -> NsHttpResponse:
        return await self.request(
            "PUT",
            url,
            params=params,
            headers=headers,
            json_data=json_data,
            data=data,
            bearer_token=bearer_token,
            trace_id=trace_id,
            expected_statuses=expected_statuses,
            raise_for_status=raise_for_status,
        )

    async def delete(
            self,
            url: str,
            *,
            params: Mapping[str, Any] | None = None,
            headers: Mapping[str, str] | None = None,
            bearer_token: str | None = None,
            trace_id: str | None = None,
            expected_statuses: Collection[int] | None = None,
            raise_for_status: bool = True,
    ) -> NsHttpResponse:
        return await self.request(
            "DELETE",
            url,
            params=params,
            headers=headers,
            bearer_token=bearer_token,
            trace_id=trace_id,
            expected_statuses=expected_statuses,
            raise_for_status=raise_for_status,
        )

    async def aclose(self) -> None:
        if self._closed:
            return

        await self._client.aclose()
        self._closed = True

    async def __aenter__(self) -> "NsAsyncHttpClient":
        self._ensure_open()
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        await self.aclose()

    def _ensure_open(self) -> None:
        if self._closed:
            raise NsDependencyError(
                "HTTP client is already closed.",
                details={
                    "client": self.name,
                },
            )

    @staticmethod
    def _build_headers(
            *,
            headers: Mapping[str, str] | None,
            bearer_token: str | None,
            trace_id: str | None,
    ) -> dict[str, str]:
        result: dict[str, str] = dict(headers or {})

        if bearer_token:
            result["Authorization"] = f"Bearer {bearer_token}"

        if trace_id:
            result["X-Trace-Id"] = trace_id

        return result

    def _validate_response_status(
            self,
            *,
            response: NsHttpResponse,
            expected_statuses: Collection[int] | None,
            raise_for_status: bool,
    ) -> None:
        if expected_statuses is not None:
            allowed_statuses = set(expected_statuses)
            if response.status_code not in allowed_statuses:
                raise NsDependencyError(
                    "HTTP response status is unexpected.",
                    details={
                        "client": self.name,
                        "method": response.method,
                        "url": response.url,
                        "status_code": response.status_code,
                        "expected_statuses": sorted(allowed_statuses),
                        "body_preview": response.text[:1000],
                    },
                )
            return

        if raise_for_status and not response.ok:
            raise NsDependencyError(
                "HTTP response status indicates failure.",
                details={
                    "client": self.name,
                    "method": response.method,
                    "url": response.url,
                    "status_code": response.status_code,
                    "body_preview": response.text[:1000],
                },
            )

    def _safe_url(self, url: str) -> str:
        if self.base_url and url.startswith("/"):
            return f"{self.base_url}{url}"

        return url


def get_async_http_client(
        name: str = "default",
        *,
        base_url: str = "",
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
        default_headers: Mapping[str, str] | None = None,
        verify: bool = True,
        max_connections: int = _DEFAULT_MAX_CONNECTIONS,
        max_keepalive_connections: int = _DEFAULT_MAX_KEEPALIVE_CONNECTIONS
) -> NsAsyncHttpClient:
    with _CLIENT_LOCK:
        client = _CLIENT_MAP.get(name)
        if client is not None:
            return client

        client = NsAsyncHttpClient(
            name=name,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            default_headers=default_headers,
            verify=verify,
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )
        _CLIENT_MAP[name] = client
        return client


async def aclose_http_clients() -> None:
    with _CLIENT_LOCK:
        clients = list(_CLIENT_MAP.values())
        _CLIENT_MAP.clear()

    for client in clients:
        await client.aclose()
