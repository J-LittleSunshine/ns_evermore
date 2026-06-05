# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

from ns_common.runtime.config import NsRuntimeConfig
from ns_common.runtime.constants import (
    RUNTIME_BACKEND_MEMORY,
    RUNTIME_BACKEND_REDIS,
    RUNTIME_BACKEND_VALKEY,
)
from ns_common.runtime.errors import NsRuntimeBrokerError, NsRuntimeConfigurationError


@dataclass(slots=True, frozen=True, kw_only=True)
class NsRuntimeBrokerMessage:
    """Decoded broker message envelope.

    This is intentionally small. Runtime message serialization remains owned by
    protocol/message layers. Broker only transports bytes by channel.
    """

    channel: str
    payload: bytes


class MemoryRuntimeBroker:
    """In-process async pub/sub broker.

    Scope:
    - development and single-process runtime diagnostics
    - no cross-process delivery
    - no persistence
    - no delivery after subscriber disconnect

    Runtime reliability is still provided by SQL WAL outbox + ACK/retry.
    """

    def __init__(self) -> None:
        """Initialize memory broker state."""
        self._lock = asyncio.Lock()
        self._closed = False
        self._subscribers: dict[str, set[asyncio.Queue[bytes | None]]] = {}

    async def publish(self, channel: str, payload: bytes) -> None:
        """Publish encoded runtime message to one local memory channel."""
        normalized_channel = self._normalize_channel(channel)
        normalized_payload = self._normalize_payload(payload)

        async with self._lock:
            self._ensure_open()
            queues = list(self._subscribers.get(normalized_channel, set()))

        for queue in queues:
            await queue.put(normalized_payload)

    async def subscribe(self, channel: str) -> AsyncIterator[bytes]:
        """Subscribe to one local memory channel and yield payload bytes."""
        normalized_channel = self._normalize_channel(channel)
        queue: asyncio.Queue[bytes | None] = asyncio.Queue()

        async with self._lock:
            self._ensure_open()
            self._subscribers.setdefault(normalized_channel, set()).add(queue)

        try:
            while True:
                item = await queue.get()
                if item is None:
                    break

                yield item
        finally:
            async with self._lock:
                queues = self._subscribers.get(normalized_channel)
                if queues is not None:
                    queues.discard(queue)
                    if not queues:
                        self._subscribers.pop(normalized_channel, None)

    async def close(self) -> None:
        """Close broker and release all memory subscribers."""
        async with self._lock:
            if self._closed:
                return

            self._closed = True
            queues: list[asyncio.Queue[bytes | None]] = []
            for channel_queues in self._subscribers.values():
                queues.extend(channel_queues)

            self._subscribers.clear()

        for queue in queues:
            await queue.put(None)

    def _ensure_open(self) -> None:
        """Ensure broker is open."""
        if self._closed:
            raise NsRuntimeBrokerError("runtime memory broker is closed")

    @staticmethod
    def _normalize_channel(channel: str) -> str:
        """Normalize broker channel."""
        normalized = str(channel or "").strip()
        if not normalized:
            raise NsRuntimeBrokerError("runtime broker channel is required")
        return normalized

    @staticmethod
    def _normalize_payload(payload: bytes) -> bytes:
        """Normalize broker payload."""
        if isinstance(payload, bytes):
            return payload

        if isinstance(payload, bytearray):
            return bytes(payload)

        raise NsRuntimeBrokerError("runtime broker payload must be bytes")


class RedisRuntimeBroker:
    """Redis/ValKey async pub/sub broker.

    Redis and ValKey are both accessed through redis-py asyncio client because
    ValKey preserves Redis protocol compatibility for this pub/sub use case.
    """

    def __init__(self, *, url: str, socket_timeout: float = 3.0, health_check_interval: int = 30) -> None:
        """Initialize Redis/ValKey broker."""
        normalized_url = str(url or "").strip()
        if not normalized_url:
            raise NsRuntimeConfigurationError("runtime_broker_location is required for redis/valkey broker")

        self._url = normalized_url
        self._socket_timeout = float(socket_timeout)
        self._health_check_interval = int(health_check_interval)
        self._client: Any | None = None
        self._client_lock = asyncio.Lock()
        self._closed = False

    async def publish(self, channel: str, payload: bytes) -> None:
        """Publish encoded runtime message through Redis/ValKey PubSub."""
        normalized_channel = self._normalize_channel(channel)
        normalized_payload = self._normalize_payload(payload)
        client = await self._get_client()

        try:
            await client.publish(normalized_channel, normalized_payload)
        except Exception as exc:
            raise NsRuntimeBrokerError(f"runtime redis broker publish failed: {exc}") from exc

    async def subscribe(self, channel: str) -> AsyncIterator[bytes]:
        """Subscribe to one Redis/ValKey PubSub channel and yield payload bytes."""
        normalized_channel = self._normalize_channel(channel)
        client = await self._get_client()
        pubsub = client.pubsub()

        try:
            await pubsub.subscribe(normalized_channel)

            async for message in pubsub.listen():
                if self._closed:
                    break

                if not isinstance(message, dict):
                    continue

                message_type = str(message.get("type") or "").strip()
                if message_type != "message":
                    continue

                data = message.get("data")
                if isinstance(data, bytes):
                    yield data
                elif isinstance(data, bytearray):
                    yield bytes(data)
                elif isinstance(data, str):
                    yield data.encode("utf-8")
        except Exception as exc:
            if self._closed:
                return
            raise NsRuntimeBrokerError(f"runtime redis broker subscribe failed: {exc}") from exc
        finally:
            with contextlib_suppress():
                await pubsub.unsubscribe(normalized_channel)
            with contextlib_suppress():
                await pubsub.close()

    async def close(self) -> None:
        """Close Redis/ValKey broker resources."""
        async with self._client_lock:
            self._closed = True
            client = self._client
            self._client = None

        if client is not None:
            with contextlib_suppress():
                await client.aclose()

    async def _get_client(self) -> Any:
        """Return initialized redis asyncio client."""
        async with self._client_lock:
            if self._closed:
                raise NsRuntimeBrokerError("runtime redis broker is closed")

            if self._client is not None:
                return self._client

            try:
                import redis.asyncio as redis
            except ImportError as exc:
                raise NsRuntimeConfigurationError("redis package is required for redis/valkey runtime broker") from exc

            self._client = redis.Redis.from_url(
                self._url,
                socket_timeout=self._socket_timeout,
                socket_connect_timeout=self._socket_timeout,
                health_check_interval=self._health_check_interval,
                decode_responses=False,
            )
            return self._client

    @staticmethod
    def _normalize_channel(channel: str) -> str:
        """Normalize broker channel."""
        normalized = str(channel or "").strip()
        if not normalized:
            raise NsRuntimeBrokerError("runtime broker channel is required")
        return normalized

    @staticmethod
    def _normalize_payload(payload: bytes) -> bytes:
        """Normalize broker payload."""
        if isinstance(payload, bytes):
            return payload

        if isinstance(payload, bytearray):
            return bytes(payload)

        raise NsRuntimeBrokerError("runtime broker payload must be bytes")


class contextlib_suppress:
    """Small async-compatible suppress context manager.

    Avoid importing contextlib only for two cleanup calls while keeping cleanup
    failures explicitly ignored.
    """

    def __init__(self, *exceptions: type[BaseException]) -> None:
        """Initialize suppress context manager."""
        self._exceptions = exceptions or (Exception,)

    def __enter__(self) -> None:
        """Enter context manager."""

    def __exit__(self, exc_type, exc, traceback) -> bool:
        """Suppress configured exception types."""
        _ = exc, traceback
        return exc_type is not None and issubclass(exc_type, self._exceptions)


def build_runtime_broker(config: NsRuntimeConfig | None = None):
    """Build runtime broker from runtime config.

    P13-A provides:
    - memory broker for local development and single-process diagnostics
    - redis/valkey broker for cluster pub/sub transport

    MQ remains a reserved extension point.
    """
    if config is None:
        from ns_common.config import ns_config

        config = ns_config.runtime_config

    backend = str(config.resolved_runtime_broker_backend() or RUNTIME_BACKEND_MEMORY).strip().lower()
    config.ensure_runtime_broker_backend_implemented()

    if backend == RUNTIME_BACKEND_MEMORY:
        return MemoryRuntimeBroker()

    if backend in {RUNTIME_BACKEND_REDIS, RUNTIME_BACKEND_VALKEY}:
        return RedisRuntimeBroker(
            url=str(config.runtime_broker_location or "").strip(),
        )

    raise NsRuntimeConfigurationError(f"runtime broker backend is not implemented yet: {backend}")
