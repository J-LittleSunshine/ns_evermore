# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from enum import Enum
from threading import RLock
from typing import (
    Any,
    Callable,
    Collection,
    Mapping,
)
from urllib.parse import unquote, unquote_plus

import httpx

from ns_common.exceptions import (
    NsDependencyError,
    NsStateError,
    NsValidationError,
)
from ns_common.logger import get_ns_logger
from ns_common.security import REDACTED, Sanitizer

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
    safe_url: str | None = field(default=None, repr=False, compare=False)
    safe_body_summary: Mapping[str, object] | None = field(
        default=None,
        repr=False,
        compare=False,
    )

    @property
    def ok(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> Any:
        if not self.text:
            return None

        try:
            return json.loads(self.text)
        except json.JSONDecodeError:
            pass

        sanitizer = Sanitizer()
        raise NsDependencyError(
            "HTTP response body is not valid JSON.",
            details={
                "method": self.method,
                "url": sanitizer.sanitize_url(self.safe_url or self.url),
                "status_code": self.status_code,
                "body_summary": _safe_body_summary_for_error(
                    text=self.text,
                    headers=self.headers,
                    supplied_summary=self.safe_body_summary,
                    sanitizer=sanitizer,
                ),
            },
        )


# A response sanitizer is synchronous and returns only structured diagnostic
# fields. The common Sanitizer processes the returned mapping once more.
NsHttpResponseSanitizer = Callable[
    [NsHttpResponse],
    Mapping[str, object] | None,
]


def _default_safe_body_summary(
        *,
        text: str,
        headers: Mapping[str, str],
) -> dict[str, object]:
    summary: dict[str, object] = {
        "present": bool(text),
        "text_length": len(text),
    }
    content_type = next(
        (
            value
            for name, value in headers.items()
            if name.casefold() == "content-type"
        ),
        "",
    )
    if isinstance(content_type, str) and content_type:
        media_type = content_type.partition(";")[0].strip().casefold()
        if media_type == "application/json" or media_type.endswith("+json"):
            summary["body_format"] = "json"
        elif media_type.startswith("text/"):
            summary["body_format"] = "text"
        elif media_type == "application/octet-stream":
            summary["body_format"] = "binary"
        else:
            summary["body_format"] = "other"
    return summary


def _safe_body_summary_for_error(
        *,
        text: str,
        headers: Mapping[str, str],
        supplied_summary: Mapping[str, object] | None,
        sanitizer: Sanitizer,
) -> dict[str, object]:
    default_summary = _default_safe_body_summary(
        text=text,
        headers=headers,
    )
    if supplied_summary is None:
        return default_summary

    sanitized_summary = sanitizer.sanitize(
        supplied_summary,
        field_name="body_summary",
    )
    if not isinstance(sanitized_summary, Mapping):
        default_summary["response_sanitizer"] = "failed_closed"
        return default_summary

    return dict(sanitized_summary)


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
            max_keepalive_connections: int = _DEFAULT_MAX_KEEPALIVE_CONNECTIONS,
            response_sanitizer: NsHttpResponseSanitizer | None = None,
    ) -> None:
        self.name: str = name
        self.base_url: str = base_url.rstrip("/")
        self.timeout_seconds: float = timeout_seconds
        self.default_headers: dict[str, str] = dict(default_headers or {})
        self.verify: bool = verify
        self.max_connections: int = max_connections
        self.max_keepalive_connections: int = max_keepalive_connections
        self.response_sanitizer = response_sanitizer

        self._sanitizer = Sanitizer()
        self._logger = get_ns_logger(
            f"ns_http_client.{self.name}",
            sanitizer=self._sanitizer,
        )
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
        self._request_base_url = self._client.base_url
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
            response_sanitizer: NsHttpResponseSanitizer | None = None,
    ) -> NsHttpResponse:
        self._ensure_open()

        method_text = method.upper().strip()
        request_params = (
            httpx.QueryParams(params)
            if params is not None
            else None
        )
        self._ensure_bearer_token_header_only(
            url=url,
            params=request_params,
            bearer_token=bearer_token,
        )
        request_headers = self._build_headers(
            headers=headers,
            bearer_token=bearer_token,
            trace_id=trace_id,
        )

        response: httpx.Response
        failure: tuple[str, str | None] | None = None
        try:
            response = await self._client.request(
                method_text,
                url,
                params=request_params,
                headers=request_headers,
                json=json_data,
                data=data,
            )
        except httpx.TimeoutException:
            failure = ("timeout", None)
        except httpx.RequestError as error:
            failure = ("request", type(error).__name__)

        if failure is not None and failure[0] == "timeout":
            raise NsDependencyError(
                "HTTP request timed out.",
                details={
                    "client": self.name,
                    "method": method_text,
                    "url": self._safe_url(url),
                    "timeout_seconds": self.timeout_seconds,
                },
            )
        if failure is not None:
            raise NsDependencyError(
                "HTTP request failed.",
                details={
                    "client": self.name,
                    "method": method_text,
                    "url": self._safe_url(url),
                    "error_type": failure[1],
                },
            )

        result = NsHttpResponse(
            status_code=response.status_code,
            headers=dict(response.headers),
            text=response.text,
            url=str(response.url),
            method=method_text,
            safe_url=self._safe_response_url(
                str(response.url),
                bearer_token=bearer_token,
            ),
        )
        result.safe_body_summary = self._build_safe_body_summary(
            response=result,
            response_sanitizer=(
                response_sanitizer
                if response_sanitizer is not None
                else self.response_sanitizer
            ),
        )

        self._logger.info(
            "HTTP request completed.",
            extra={
                "client": self.name,
                "method": method_text,
                "url": result.safe_url,
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
            response_sanitizer: NsHttpResponseSanitizer | None = None,
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
            response_sanitizer=response_sanitizer,
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
            response_sanitizer: NsHttpResponseSanitizer | None = None,
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
            response_sanitizer=response_sanitizer,
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
            response_sanitizer: NsHttpResponseSanitizer | None = None,
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
            response_sanitizer=response_sanitizer,
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
            response_sanitizer: NsHttpResponseSanitizer | None = None,
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
            response_sanitizer=response_sanitizer,
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
                        "url": response.safe_url,
                        "status_code": response.status_code,
                        "expected_statuses": sorted(allowed_statuses),
                        "body_summary": response.safe_body_summary,
                    },
                )
            return

        if raise_for_status and not response.ok:
            raise NsDependencyError(
                "HTTP response status indicates failure.",
                details={
                    "client": self.name,
                    "method": response.method,
                    "url": response.safe_url,
                    "status_code": response.status_code,
                    "body_summary": response.safe_body_summary,
                },
            )

    def _safe_url(self, url: str) -> str:
        return self._sanitizer.sanitize_url(self._resolve_url(url))

    def _safe_response_url(
            self,
            url: str,
            *,
            bearer_token: str | None,
    ) -> str:
        safe_url = self._sanitizer.sanitize_url(url)
        if bearer_token and bearer_token in unquote(safe_url):
            return REDACTED
        return safe_url

    def _resolve_url(self, url: str) -> str:
        return str(self._request_base_url.join(url))

    def _ensure_bearer_token_header_only(
            self,
            *,
            url: str,
            params: Mapping[str, Any] | None,
            bearer_token: str | None,
    ) -> None:
        if bearer_token is None:
            return
        if not isinstance(bearer_token, str):
            raise NsValidationError(
                "bearer_token must be a string.",
                details={
                    "client": self.name,
                    "field": "bearer_token",
                    "actual_type": type(bearer_token).__name__,
                },
            )
        if not bearer_token:
            return

        raw_url = self._resolve_url(url)
        request_targets = [raw_url, unquote(raw_url)]
        if params:
            raw_query = str(httpx.QueryParams(params))
            request_targets.extend((raw_query, unquote_plus(raw_query)))
        if any(bearer_token in target for target in request_targets):
            raise NsValidationError(
                "Bearer token must only be sent in the Authorization header.",
                details={
                    "client": self.name,
                    "field": "bearer_token",
                    "action": "remove_bearer_token_from_url",
                },
            )

    def _build_safe_body_summary(
            self,
            *,
            response: NsHttpResponse,
            response_sanitizer: NsHttpResponseSanitizer | None,
    ) -> dict[str, object]:
        summary = _default_safe_body_summary(
            text=response.text,
            headers=response.headers,
        )
        if response_sanitizer is None:
            return summary

        try:
            custom_summary = response_sanitizer(NsHttpResponse(
                status_code=response.status_code,
                headers=dict(response.headers),
                text=response.text,
                url=response.url,
                method=response.method,
                safe_url=response.safe_url,
                safe_body_summary=dict(summary),
            ))
        except Exception:
            summary["response_sanitizer"] = "failed_closed"
            return summary

        if custom_summary is None:
            summary["response_sanitizer"] = "omitted"
            return summary
        if not isinstance(custom_summary, Mapping):
            summary["response_sanitizer"] = "failed_closed"
            return summary

        sanitized_summary = self._sanitizer.sanitize(
            custom_summary,
            field_name="response_summary",
        )
        if not isinstance(sanitized_summary, Mapping):
            summary["response_sanitizer"] = "failed_closed"
            return summary

        summary["response_sanitizer"] = "applied"
        summary["sanitized"] = dict(sanitized_summary)
        return summary


class NsHttpClientOwnerState(str, Enum):
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"


class _NsHttpClientAuthorityBinding:
    """Opaque owner-issued proof for one unmodified production HTTP client."""

    __slots__ = (
        "_owner", "_client", "_composition", "_httpx_client",
        "_transport", "_transport_handler", "_mounts", "_mount_entries",
        "_mount_handlers",
    )

    def __init__(
        self,
        *,
        owner: "NsHttpClientOwner",
        client: NsAsyncHttpClient,
        composition: object,
        _token: object,
    ) -> None:
        if not owner._consume_authority_binding_token(_token):
            raise NsValidationError(
                "HTTP client authority binding issuer is invalid.",
                details={"component": "http_client_owner", "field": "authority_binding"},
            )
        self._owner = owner
        self._client = client
        self._composition = composition
        self._httpx_client = client._client
        self._transport = client._client._transport
        self._transport_handler = _transport_handler(self._transport)
        self._mounts = client._client._mounts
        self._mount_entries = tuple(client._client._mounts.items())
        self._mount_handlers = tuple(
            None if value is None else _transport_handler(value)
            for _, value in self._mount_entries
        )

    def is_current(
        self,
        *,
        owner: "NsHttpClientOwner",
        client: NsAsyncHttpClient,
        composition: object,
    ) -> bool:
        if (
            type(self) is not _NsHttpClientAuthorityBinding
            or self._owner is not owner
            or self._client is not client
            or self._composition is not composition
            or type(owner) is not NsHttpClientOwner
            or type(owner.factory) is not NsHttpClientFactory
            or type(client) is not NsAsyncHttpClient
            or getattr(client, "_client", None) is not self._httpx_client
            or type(self._httpx_client) is not httpx.AsyncClient
            or getattr(self._httpx_client, "_transport", None)
            is not self._transport
            or getattr(self._httpx_client, "_mounts", None) is not self._mounts
            or client not in owner.clients
            or not owner._owns_authority_binding(client, self)
            or owner.state is not NsHttpClientOwnerState.OPEN
            or client.is_closed
            or self._httpx_client.is_closed
        ):
            return False
        client_substitutions = {
            "request", "get", "post", "put", "delete",
        }.intersection(vars(client))
        transport = self._httpx_client
        transport_substitutions = {
            "request", "send", "stream",
        }.intersection(vars(transport))
        current_mount_entries = tuple(self._mounts.items())
        if (
            len(current_mount_entries) != len(self._mount_entries)
            or any(
                current_key is not expected_key
                or current_value is not expected_value
                for (current_key, current_value), (
                    expected_key, expected_value,
                ) in zip(current_mount_entries, self._mount_entries)
            )
            or _transport_handler(self._transport)
            is not self._transport_handler
        ):
            return False
        for offset, (_, mounted) in enumerate(current_mount_entries):
            expected_handler = self._mount_handlers[offset]
            if mounted is None:
                if expected_handler is not None:
                    return False
                continue
            if (
                expected_handler is None
                or _transport_handler(mounted) is not expected_handler
                or "handle_async_request" in vars(mounted)
            ):
                return False
        return bool(
            not client_substitutions
            and not transport_substitutions
            and NsAsyncHttpClient.request is getattr(type(client), "request", None)
            and NsAsyncHttpClient.post is getattr(type(client), "post", None)
            and NsAsyncHttpClient.get is getattr(type(client), "get", None)
            and NsAsyncHttpClient.put is getattr(type(client), "put", None)
            and NsAsyncHttpClient.delete is getattr(type(client), "delete", None)
            and httpx.AsyncClient.request
            is getattr(type(transport), "request", None)
            and httpx.AsyncClient.send is getattr(type(transport), "send", None)
            and httpx.AsyncClient.stream
            is getattr(type(transport), "stream", None)
            and "handle_async_request" not in vars(self._transport)
            and NsHttpClientFactory.create
            is getattr(type(owner.factory), "create", None)
        )

    async def post(
        self,
        path: str,
        *,
        json_data: object,
        bearer_token: str,
        trace_id: str,
        expected_statuses: Collection[int],
    ) -> NsHttpResponse:
        if not self.is_current(
            owner=self._owner,
            client=self._client,
            composition=self._composition,
        ):
            raise NsValidationError(
                "HTTP authority provenance is no longer valid.",
                details={
                    "component": "http_client_owner",
                    "field": "authority_transport",
                },
            )
        result = await self._client.post(
            path,
            json_data=json_data,
            bearer_token=bearer_token,
            trace_id=trace_id,
            expected_statuses=expected_statuses,
        )
        if not self.is_current(
            owner=self._owner,
            client=self._client,
            composition=self._composition,
        ):
            raise NsValidationError(
                "HTTP authority provenance changed during request.",
                details={
                    "component": "http_client_owner",
                    "field": "authority_transport",
                },
            )
        return result


class _NsHttpClientAuthorityHandle:
    """Narrow IAM HTTP handle without a public mutable client reference."""

    __slots__ = ("__binding",)

    def __init__(
        self,
        *,
        binding: _NsHttpClientAuthorityBinding,
        _token: object,
        owner: "NsHttpClientOwner",
    ) -> None:
        if (
            type(self) is not _NsHttpClientAuthorityHandle
            or type(binding) is not _NsHttpClientAuthorityBinding
            or not owner._consume_authority_handle_token(_token)
        ):
            raise NsValidationError(
                "HTTP authority handle issuer is invalid.",
                details={
                    "component": "http_client_owner",
                    "field": "authority_handle",
                },
            )
        self.__binding = binding

    def is_current(self) -> bool:
        binding = self.__binding
        return binding.is_current(
            owner=binding._owner,
            client=binding._client,
            composition=binding._composition,
        )

    async def post(
        self,
        path: str,
        *,
        json_data: object,
        bearer_token: str,
        trace_id: str,
        expected_statuses: Collection[int],
    ) -> NsHttpResponse:
        return await self.__binding.post(
            path,
            json_data=json_data,
            bearer_token=bearer_token,
            trace_id=trace_id,
            expected_statuses=expected_statuses,
        )

    def __copy__(self) -> "_NsHttpClientAuthorityHandle":
        raise NsValidationError(
            "HTTP authority handle cannot be copied.",
            details={"component": "http_client_owner", "field": "copy"},
        )

    def __deepcopy__(
        self,
        memo: dict[int, object],
    ) -> "_NsHttpClientAuthorityHandle":
        del memo
        raise NsValidationError(
            "HTTP authority handle cannot be copied.",
            details={"component": "http_client_owner", "field": "copy"},
        )


def _transport_handler(transport: object) -> object:
    handler = getattr(type(transport), "handle_async_request", None)
    if not callable(handler):
        raise NsValidationError(
            "HTTP transport handler is invalid.",
            details={
                "component": "http_client_owner",
                "field": "transport_handler",
            },
        )
    return handler


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
            response_sanitizer: NsHttpResponseSanitizer | None = None,
    ) -> NsAsyncHttpClient:
        return NsAsyncHttpClient(
            name=name,
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            default_headers=default_headers,
            verify=verify,
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
            response_sanitizer=response_sanitizer,
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
        self._pending_authority_binding_token: object | None = None
        self._pending_authority_handle_token: object | None = None
        self._authority_bindings: dict[
            NsAsyncHttpClient, _NsHttpClientAuthorityBinding
        ] = {}

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
            response_sanitizer: NsHttpResponseSanitizer | None = None,
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
                response_sanitizer=response_sanitizer,
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

    def _create_authority_handle(
        self,
        *,
        client: NsAsyncHttpClient,
        composition: object,
    ) -> _NsHttpClientAuthorityHandle:
        """Bind one owned client and return only a narrow IAM request handle."""

        with self._state_lock:
            self._ensure_open()
            if (
                type(self) is not NsHttpClientOwner
                or type(self._factory) is not NsHttpClientFactory
                or type(client) is not NsAsyncHttpClient
                or not any(client is current for current in self._clients)
                or client in self._authority_bindings
                or composition is None
            ):
                raise NsValidationError(
                    "HTTP client authority binding is invalid.",
                    details={
                        "component": "http_client_owner",
                        "field": "authority_client",
                    },
                )
            token = object()
            self._pending_authority_binding_token = token
            try:
                binding = _NsHttpClientAuthorityBinding(
                    owner=self,
                    client=client,
                    composition=composition,
                    _token=token,
                )
            finally:
                self._pending_authority_binding_token = None
            self._authority_bindings[client] = binding
            handle_token = object()
            self._pending_authority_handle_token = handle_token
            try:
                return _NsHttpClientAuthorityHandle(
                    binding=binding,
                    _token=handle_token,
                    owner=self,
                )
            finally:
                self._pending_authority_handle_token = None

    def _consume_authority_binding_token(self, token: object) -> bool:
        return (
            token is not None
            and self._pending_authority_binding_token is token
        )

    def _consume_authority_handle_token(self, token: object) -> bool:
        return (
            token is not None
            and self._pending_authority_handle_token is token
        )

    def _owns_authority_binding(
        self,
        client: NsAsyncHttpClient,
        binding: _NsHttpClientAuthorityBinding,
    ) -> bool:
        with self._state_lock:
            return self._authority_bindings.get(client) is binding

    def __copy__(self) -> "NsHttpClientOwner":
        raise NsValidationError(
            "HTTP client owner cannot be copied.",
            details={"component": "http_client_owner", "field": "copy"},
        )

    def __deepcopy__(
        self,
        memo: dict[int, object],
    ) -> "NsHttpClientOwner":
        del memo
        raise NsValidationError(
            "HTTP client owner cannot be copied.",
            details={"component": "http_client_owner", "field": "copy"},
        )

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
        max_keepalive_connections: int = _DEFAULT_MAX_KEEPALIVE_CONNECTIONS,
        response_sanitizer: NsHttpResponseSanitizer | None = None,
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
            response_sanitizer=response_sanitizer,
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
    "NsHttpResponseSanitizer",
    "aclose_http_clients",
    "get_async_http_client",
]
