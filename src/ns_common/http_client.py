# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import threading
import weakref
from dataclasses import dataclass, field
from typing import Any, Mapping
from urllib.parse import urljoin

import aiohttp
import requests
from requests.adapters import HTTPAdapter


class NsHttpClientError(Exception):
    """Base error for ns_common HTTP client."""


class NsHttpStatusError(NsHttpClientError):
    """Raised when HTTP status code is not 2xx."""

    def __init__(
            self,
            *,
            method: str,
            url: str,
            status_code: int,
            response_text: str,
    ) -> None:
        """Initialize HTTP status error."""
        self.method = method
        self.url = url
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(f"HTTP {status_code} for {method.upper()} {url}: {response_text[:500]}")


class NsHttpResponseDecodeError(NsHttpClientError):
    """Raised when response JSON decoding fails."""


@dataclass(slots=True, frozen=True, kw_only=True)
class NsHttpClientConfig:
    """Shared HTTP client configuration."""

    base_url: str = ""
    timeout_seconds: float = 3.0
    verify_ssl: bool = True
    trust_env: bool = True
    default_headers: dict[str, str] = field(default_factory=dict)

    # requests / urllib3 connection pool settings.
    sync_pool_connections: int = 32
    sync_pool_maxsize: int = 128
    sync_pool_block: bool = True

    # aiohttp connection pool settings.
    async_pool_limit: int = 128
    async_pool_limit_per_host: int = 32
    async_keepalive_timeout_seconds: float = 30.0

    def normalized_base_url(self) -> str:
        """Return normalized base URL."""
        base_url = str(self.base_url or "").strip()
        if base_url and not base_url.endswith("/"):
            base_url = f"{base_url}/"
        return base_url

    def normalized_timeout_seconds(self) -> float:
        """Return positive timeout seconds."""
        timeout = float(self.timeout_seconds or 0)
        if timeout <= 0:
            raise ValueError("http timeout_seconds must be positive")
        return timeout

    def validate(self) -> None:
        """Validate HTTP client config."""
        self.normalized_timeout_seconds()

        if isinstance(self.sync_pool_connections, bool) or self.sync_pool_connections <= 0:
            raise ValueError("http sync_pool_connections must be positive")

        if isinstance(self.sync_pool_maxsize, bool) or self.sync_pool_maxsize <= 0:
            raise ValueError("http sync_pool_maxsize must be positive")

        if isinstance(self.async_pool_limit, bool) or self.async_pool_limit <= 0:
            raise ValueError("http async_pool_limit must be positive")

        if isinstance(self.async_pool_limit_per_host, bool) or self.async_pool_limit_per_host <= 0:
            raise ValueError("http async_pool_limit_per_host must be positive")

        if self.async_keepalive_timeout_seconds <= 0:
            raise ValueError("http async_keepalive_timeout_seconds must be positive")


@dataclass(slots=True, frozen=True, kw_only=True)
class NsHttpResponse:
    """Normalized HTTP response."""

    status_code: int
    headers: dict[str, str]
    text: str
    url: str

    def json(self) -> Any:
        """Decode response body as JSON."""
        try:
            return json.loads(self.text)
        except json.JSONDecodeError as exc:
            raise NsHttpResponseDecodeError(f"HTTP response is not valid JSON: {self.url}") from exc


class NsHttpClient:
    """Process-wide singleton HTTP client.

    Design:
    - The client object itself is a process-wide singleton implemented by __new__.
    - requests.Session is stored per thread to avoid unsafe cross-thread Session sharing.
    - aiohttp.ClientSession is stored per event loop because aiohttp sessions are loop-bound.
    - Both sync and async sessions use connection pools and keep-alive reuse.
    """

    _instance: NsHttpClient | None = None
    _instance_lock = threading.RLock()

    def __new__(cls, config: NsHttpClientConfig | None = None) -> "NsHttpClient":
        """Create or return process-wide singleton instance."""
        _ = config

        if cls._instance is not None:
            return cls._instance

        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)

        return cls._instance

    def __init__(self, config: NsHttpClientConfig | None = None) -> None:
        """Initialize singleton once."""
        if getattr(self, "_initialized", False):
            return

        with self.__class__._instance_lock:
            if getattr(self, "_initialized", False):
                return

            self._config = config or NsHttpClientConfig()
            self._config.validate()

            self._thread_local = threading.local()
            self._sync_sessions_lock = threading.RLock()
            self._sync_sessions: set[requests.Session] = set()

            self._async_lock = asyncio.Lock()
            self._async_sessions: weakref.WeakKeyDictionary[
                asyncio.AbstractEventLoop,
                aiohttp.ClientSession,
            ] = weakref.WeakKeyDictionary()

            self._initialized = True

    def get(
            self,
            url: str,
            *,
            headers: Mapping[str, str] | None = None,
            params: Mapping[str, Any] | None = None,
            timeout_seconds: float | None = None,
            raise_for_status: bool = True,
    ) -> NsHttpResponse:
        """Send synchronous HTTP GET request."""
        return self.request(
            "GET",
            url,
            headers=headers,
            params=params,
            timeout_seconds=timeout_seconds,
            raise_for_status=raise_for_status,
        )

    def post_json(
            self,
            url: str,
            *,
            json_data: Mapping[str, Any] | None = None,
            headers: Mapping[str, str] | None = None,
            timeout_seconds: float | None = None,
            raise_for_status: bool = True,
    ) -> NsHttpResponse:
        """Send synchronous HTTP POST request with JSON body."""
        return self.request(
            "POST",
            url,
            headers=headers,
            json_data=json_data,
            timeout_seconds=timeout_seconds,
            raise_for_status=raise_for_status,
        )

    def request(
            self,
            method: str,
            url: str,
            *,
            headers: Mapping[str, str] | None = None,
            params: Mapping[str, Any] | None = None,
            json_data: Mapping[str, Any] | None = None,
            timeout_seconds: float | None = None,
            raise_for_status: bool = True,
    ) -> NsHttpResponse:
        """Send synchronous HTTP request through thread-local requests.Session."""
        normalized_method = self._normalize_method(method)
        resolved_url = self._resolve_url(url)
        merged_headers = self._merge_headers(headers)
        timeout = self._resolve_timeout(timeout_seconds)
        session = self._get_sync_session()

        response = session.request(
            method=normalized_method,
            url=resolved_url,
            headers=merged_headers,
            params=dict(params or {}),
            json=dict(json_data or {}) if json_data is not None else None,
            timeout=timeout,
            verify=self._config.verify_ssl,
        )

        normalized_response = NsHttpResponse(
            status_code=int(response.status_code),
            headers={str(key): str(value) for key, value in response.headers.items()},
            text=response.text,
            url=str(response.url),
        )

        if raise_for_status and not self._is_success_status(normalized_response.status_code):
            raise NsHttpStatusError(
                method=normalized_method,
                url=resolved_url,
                status_code=normalized_response.status_code,
                response_text=normalized_response.text,
            )

        return normalized_response

    async def async_get(
            self,
            url: str,
            *,
            headers: Mapping[str, str] | None = None,
            params: Mapping[str, Any] | None = None,
            timeout_seconds: float | None = None,
            raise_for_status: bool = True,
    ) -> NsHttpResponse:
        """Send asynchronous HTTP GET request."""
        return await self.async_request(
            "GET",
            url,
            headers=headers,
            params=params,
            timeout_seconds=timeout_seconds,
            raise_for_status=raise_for_status,
        )

    async def async_post_json(
            self,
            url: str,
            *,
            json_data: Mapping[str, Any] | None = None,
            headers: Mapping[str, str] | None = None,
            timeout_seconds: float | None = None,
            raise_for_status: bool = True,
    ) -> NsHttpResponse:
        """Send asynchronous HTTP POST request with JSON body."""
        return await self.async_request(
            "POST",
            url,
            headers=headers,
            json_data=json_data,
            timeout_seconds=timeout_seconds,
            raise_for_status=raise_for_status,
        )

    async def async_request(
            self,
            method: str,
            url: str,
            *,
            headers: Mapping[str, str] | None = None,
            params: Mapping[str, Any] | None = None,
            json_data: Mapping[str, Any] | None = None,
            timeout_seconds: float | None = None,
            raise_for_status: bool = True,
    ) -> NsHttpResponse:
        """Send asynchronous HTTP request through event-loop-local aiohttp.ClientSession."""
        normalized_method = self._normalize_method(method)
        resolved_url = self._resolve_url(url)
        merged_headers = self._merge_headers(headers)
        timeout = aiohttp.ClientTimeout(total=self._resolve_timeout(timeout_seconds))
        session = await self._get_async_session()

        async with session.request(
                method=normalized_method,
                url=resolved_url,
                headers=merged_headers,
                params=dict(params or {}),
                json=dict(json_data or {}) if json_data is not None else None,
                timeout=timeout,
                ssl=self._config.verify_ssl,
        ) as response:
            text = await response.text()
            normalized_response = NsHttpResponse(
                status_code=int(response.status),
                headers={str(key): str(value) for key, value in response.headers.items()},
                text=text,
                url=str(response.url),
            )

        if raise_for_status and not self._is_success_status(normalized_response.status_code):
            raise NsHttpStatusError(
                method=normalized_method,
                url=resolved_url,
                status_code=normalized_response.status_code,
                response_text=normalized_response.text,
            )

        return normalized_response

    def close(self) -> None:
        """Close all synchronous requests sessions."""
        with self._sync_sessions_lock:
            sessions = list(self._sync_sessions)
            self._sync_sessions.clear()

        for session in sessions:
            session.close()

        if hasattr(self._thread_local, "session"):
            delattr(self._thread_local, "session")

    async def aclose(self) -> None:
        """Close all asynchronous aiohttp sessions."""
        async with self._async_lock:
            sessions = list(self._async_sessions.values())
            self._async_sessions.clear()

        for session in sessions:
            if not session.closed:
                await session.close()

    @classmethod
    async def reset_instance(cls) -> None:
        """Reset singleton instance.

        Intended for tests and controlled shutdown. Do not call this in request
        hot paths because it closes shared connection pools.
        """
        with cls._instance_lock:
            instance = cls._instance
            cls._instance = None

        if instance is not None:
            instance.close()
            await instance.aclose()

    def _get_sync_session(self) -> requests.Session:
        """Return current thread's requests session with HTTPAdapter connection pools."""
        session = getattr(self._thread_local, "session", None)
        if session is not None:
            return session

        session = requests.Session()
        session.trust_env = bool(self._config.trust_env)

        adapter = HTTPAdapter(
            pool_connections=int(self._config.sync_pool_connections),
            pool_maxsize=int(self._config.sync_pool_maxsize),
            pool_block=bool(self._config.sync_pool_block),
            max_retries=0,
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        self._thread_local.session = session

        with self._sync_sessions_lock:
            self._sync_sessions.add(session)

        return session

    async def _get_async_session(self) -> aiohttp.ClientSession:
        """Return current event loop's aiohttp session with TCPConnector pool."""
        loop = asyncio.get_running_loop()

        async with self._async_lock:
            session = self._async_sessions.get(loop)
            if session is not None and not session.closed:
                return session

            connector = aiohttp.TCPConnector(
                limit=int(self._config.async_pool_limit),
                limit_per_host=int(self._config.async_pool_limit_per_host),
                keepalive_timeout=float(self._config.async_keepalive_timeout_seconds),
                ssl=bool(self._config.verify_ssl),
                enable_cleanup_closed=True,
            )

            session = aiohttp.ClientSession(
                connector=connector,
                timeout=aiohttp.ClientTimeout(total=self._config.normalized_timeout_seconds()),
                trust_env=bool(self._config.trust_env),
            )

            self._async_sessions[loop] = session
            return session

    def _resolve_url(self, url: str) -> str:
        """Resolve URL against base_url if relative URL is provided."""
        normalized_url = str(url or "").strip()
        if not normalized_url:
            raise ValueError("http url is required")

        if normalized_url.startswith(("http://", "https://")):
            return normalized_url

        base_url = self._config.normalized_base_url()
        if not base_url:
            raise ValueError("http base_url is required when url is relative")

        return urljoin(base_url, normalized_url.lstrip("/"))

    def _merge_headers(self, headers: Mapping[str, str] | None) -> dict[str, str]:
        """Merge default headers and request-level headers."""
        merged = {
            str(key): str(value)
            for key, value in self._config.default_headers.items()
            if key and value is not None
        }

        for key, value in dict(headers or {}).items():
            if key and value is not None:
                merged[str(key)] = str(value)

        return merged

    def _resolve_timeout(self, timeout_seconds: float | None) -> float:
        """Resolve positive request timeout seconds."""
        if timeout_seconds is None:
            return self._config.normalized_timeout_seconds()

        timeout = float(timeout_seconds)
        if timeout <= 0:
            raise ValueError("http timeout_seconds must be positive")
        return timeout

    @staticmethod
    def _normalize_method(method: str) -> str:
        """Normalize HTTP method."""
        normalized = str(method or "").strip().upper()
        if not normalized:
            raise ValueError("http method is required")
        return normalized

    @staticmethod
    def _is_success_status(status_code: int) -> bool:
        """Return whether status code is 2xx."""
        return 200 <= int(status_code) < 300


def get_http_client(config: NsHttpClientConfig | None = None) -> NsHttpClient:
    """Return process-wide singleton HTTP client."""
    return NsHttpClient(config=config)
