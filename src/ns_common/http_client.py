# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from threading import RLock
from typing import (
    Any,
    Collection,
    Mapping,
)

import httpx

from ns_common.exceptions import (
    NsDependencyError,
    NsStateError,
)
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

    @property
    def is_closed(self) -> bool:
        return self._closed

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


class NsHttpClientOwnerState(str, Enum):
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"


class NsHttpClientFactory:
    """Create independent HTTP clients without registering global state.

    A client returned by this factory is owned by its caller. Use
    :class:`NsHttpClientOwner` when a composition root needs to own and close
    several clients as one lifecycle resource.
    """

    def create(
            self,
            *,
            name: str,
            base_url: str = "",
            timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
            default_headers: Mapping[str, str] | None = None,
            verify: bool = True,
            max_connections: int = _DEFAULT_MAX_CONNECTIONS,
            max_keepalive_connections: int = _DEFAULT_MAX_KEEPALIVE_CONNECTIONS,
    ) -> NsAsyncHttpClient:
        return NsAsyncHttpClient(
            name=name,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            default_headers=default_headers,
            verify=verify,
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )


class NsHttpClientOwner:
    """Own explicitly created HTTP clients and close them in reverse order.

    The owner is intentionally local to a process composition root. It never
    reads or mutates the compatibility client map used by
    :func:`get_async_http_client`.
    """

    def __init__(
            self,
            *,
            factory: NsHttpClientFactory | None = None,
    ) -> None:
        self._factory = factory if factory is not None else NsHttpClientFactory()
        self._state = NsHttpClientOwnerState.OPEN
        self._clients: list[NsAsyncHttpClient] = []
        self._state_lock = RLock()
        self._loop: asyncio.AbstractEventLoop | None = None
        self._close_lock: asyncio.Lock | None = None

    @property
    def factory(self) -> NsHttpClientFactory:
        return self._factory

    @property
    def state(self) -> NsHttpClientOwnerState:
        with self._state_lock:
            return self._state

    @property
    def clients(self) -> tuple[NsAsyncHttpClient, ...]:
        with self._state_lock:
            return tuple(self._clients)

    def create(
            self,
            *,
            name: str,
            base_url: str = "",
            timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
            default_headers: Mapping[str, str] | None = None,
            verify: bool = True,
            max_connections: int = _DEFAULT_MAX_CONNECTIONS,
            max_keepalive_connections: int = _DEFAULT_MAX_KEEPALIVE_CONNECTIONS,
    ) -> NsAsyncHttpClient:
        with self._state_lock:
            self._ensure_open()
            client = self._factory.create(
                name=name,
                base_url=base_url,
                timeout_seconds=timeout_seconds,
                default_headers=default_headers,
                verify=verify,
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive_connections,
            )
            if any(client is owned_client for owned_client in self._clients):
                raise NsStateError(
                    "HTTP client factory returned an instance already owned.",
                    details={
                        "client": client.name,
                        "owner_state": self._state.value,
                        "action": "create_http_client",
                    },
                )
            self._clients.append(client)
            return client

    async def aclose(self) -> None:
        loop = asyncio.get_running_loop()
        with self._state_lock:
            if self._state is NsHttpClientOwnerState.CLOSED:
                return
            self._bind_loop(loop)
            if self._close_lock is None:
                self._close_lock = asyncio.Lock()
            close_lock = self._close_lock
            self._state = NsHttpClientOwnerState.CLOSING

        async with close_lock:
            with self._state_lock:
                if self._state is NsHttpClientOwnerState.CLOSED:
                    return
                clients = tuple(reversed(self._clients))

            failures: list[tuple[NsAsyncHttpClient, Exception]] = []
            try:
                for client in clients:
                    try:
                        await client.aclose()
                    except Exception as error:
                        failures.append((client, error))
                    else:
                        self._forget_client(client)
            finally:
                with self._state_lock:
                    if not self._clients:
                        self._state = NsHttpClientOwnerState.CLOSED

            if failures:
                raise NsDependencyError(
                    "One or more owned HTTP clients failed to close.",
                    details={
                        "action": "close_http_clients",
                        "failed_clients": [
                            {
                                "client": client.name,
                                "error_type": type(error).__name__,
                            }
                            for client, error in failures
                        ],
                    },
                ) from failures[0][1]

    async def __aenter__(self) -> "NsHttpClientOwner":
        with self._state_lock:
            self._ensure_open()
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        await self.aclose()

    def _ensure_open(self) -> None:
        if self._state is not NsHttpClientOwnerState.OPEN:
            raise NsStateError(
                "HTTP client owner is not accepting new clients.",
                details={
                    "owner_state": self._state.value,
                    "action": "create_http_client",
                },
            )

    def _bind_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        if self._loop is None:
            self._loop = loop
            return
        if self._loop is not loop:
            raise NsStateError(
                "HTTP client owner cannot be shared across event loops.",
                details={
                    "owner_state": self._state.value,
                    "action": "close_http_clients",
                },
            )

    def _forget_client(self, client: NsAsyncHttpClient) -> None:
        with self._state_lock:
            for index, owned_client in enumerate(self._clients):
                if owned_client is client:
                    del self._clients[index]
                    return


_COMPATIBILITY_FACTORY = NsHttpClientFactory()


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

        client = _COMPATIBILITY_FACTORY.create(
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


__all__ = [
    "NsAsyncHttpClient",
    "NsHttpClientFactory",
    "NsHttpClientOwner",
    "NsHttpClientOwnerState",
    "NsHttpResponse",
    "aclose_http_clients",
    "get_async_http_client",
]
