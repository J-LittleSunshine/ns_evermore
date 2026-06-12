# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import contextlib
import json
import time
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any

from ns_common.runtime.config import NsRuntimeConfig
from ns_common.runtime.constants import (
    RUNTIME_BACKEND_MEMORY,
    RUNTIME_BACKEND_REDIS,
    RUNTIME_BACKEND_VALKEY,
)
from ns_common.runtime.errors import NsRuntimeBrokerError, NsRuntimeConfigurationError, NsRuntimeValidationError

RUNTIME_BROKER_DEFAULT_NAMESPACE = "ns_runtime"
RUNTIME_BROKER_CLUSTER_CHANNEL = "cluster"
RUNTIME_BROKER_NODE_CHANNEL_PREFIX = "node"

RUNTIME_BROKER_EVENT_NODE_HEALTH = "runtime.node.health"
RUNTIME_BROKER_EVENT_NODE_ANNOUNCE = "runtime.node.announce"
RUNTIME_BROKER_EVENT_NODE_PING = "runtime.node.ping"
RUNTIME_BROKER_EVENT_NODE_PONG = "runtime.node.pong"
RUNTIME_BROKER_EVENT_MESSAGE_FORWARD = "runtime.message.forward"

RUNTIME_BROKER_EVENT_TYPES: tuple[str, ...] = (
    RUNTIME_BROKER_EVENT_NODE_HEALTH,
    RUNTIME_BROKER_EVENT_NODE_ANNOUNCE,
    RUNTIME_BROKER_EVENT_NODE_PING,
    RUNTIME_BROKER_EVENT_NODE_PONG,
    RUNTIME_BROKER_EVENT_MESSAGE_FORWARD,
)


@dataclass(slots=True, frozen=True, kw_only=True)
class NsRuntimeBrokerMessage:
    """Decoded broker message envelope.

    This is intentionally small. Runtime message serialization remains owned by
    protocol/message layers. Broker only transports bytes by channel.
    """

    channel: str
    payload: bytes


@dataclass(slots=True, frozen=True, kw_only=True)
class NsRuntimeBrokerEnvelope:
    """Runtime broker payload envelope.

    P13-B only defines a stable transport envelope. Runtime core does not yet
    use broker messages for cross-node routing, so this class is intentionally
    generic and transport-oriented.
    """

    event_type: str
    source_node_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    target_node_id: str | None = None
    message_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    trace_id: str | None = None
    created_at_epoch_ms: int = field(default_factory=lambda: int(time.time() * 1000))

    def normalized(self) -> "NsRuntimeBrokerEnvelope":
        """Return normalized broker envelope."""
        event_type = normalize_runtime_broker_event_type(self.event_type)

        source_node_id = str(self.source_node_id or "").strip()
        if not source_node_id:
            raise NsRuntimeValidationError("runtime broker envelope source_node_id is required")

        target_node_id = str(self.target_node_id).strip() if self.target_node_id is not None and str(self.target_node_id).strip() else None
        message_id = str(self.message_id or "").strip() or uuid.uuid4().hex
        trace_id = str(self.trace_id).strip() if self.trace_id is not None and str(self.trace_id).strip() else None

        return NsRuntimeBrokerEnvelope(
            event_type=event_type,
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            message_id=message_id,
            trace_id=trace_id,
            created_at_epoch_ms=int(self.created_at_epoch_ms or int(time.time() * 1000)),
            payload=dict(self.payload or {}),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize broker envelope to dict."""
        normalized = self.normalized()
        return {
            "event_type": normalized.event_type,
            "source_node_id": normalized.source_node_id,
            "target_node_id": normalized.target_node_id,
            "message_id": normalized.message_id,
            "trace_id": normalized.trace_id,
            "created_at_epoch_ms": int(normalized.created_at_epoch_ms),
            "payload": dict(normalized.payload),
        }

    def to_bytes(self) -> bytes:
        """Serialize broker envelope to compact UTF-8 JSON bytes."""
        return json.dumps(self.to_dict(), ensure_ascii=False, separators=(",", ":")).encode("utf-8")

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "NsRuntimeBrokerEnvelope":
        """Deserialize broker envelope from dict."""
        if not isinstance(data, dict):
            raise NsRuntimeValidationError("runtime broker envelope must be a JSON object")

        payload_raw: Any = data.get("payload") or {}
        if not isinstance(payload_raw, dict):
            raise NsRuntimeValidationError("runtime broker envelope payload must be a JSON object")

        return cls(
            event_type=str(data.get("event_type") or "").strip(),
            source_node_id=str(data.get("source_node_id") or "").strip(),
            target_node_id=str(data.get("target_node_id")).strip() if data.get("target_node_id") is not None and str(data.get("target_node_id")).strip() else None,
            message_id=str(data.get("message_id") or "").strip() or uuid.uuid4().hex,
            trace_id=str(data.get("trace_id")).strip() if data.get("trace_id") is not None and str(data.get("trace_id")).strip() else None,
            created_at_epoch_ms=int(data.get("created_at_epoch_ms") or int(time.time() * 1000)),
            payload=dict(payload_raw),
        ).normalized()

    @classmethod
    def from_bytes(cls, payload: bytes | bytearray | str) -> "NsRuntimeBrokerEnvelope":
        """Deserialize broker envelope from UTF-8 JSON bytes."""
        if isinstance(payload, bytes | bytearray):
            raw_text = bytes(payload).decode("utf-8")
        else:
            raw_text = str(payload)

        try:
            data: Any = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise NsRuntimeValidationError("runtime broker envelope payload is invalid JSON") from exc

        return cls.from_dict(data)


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
        normalized_channel = normalize_runtime_broker_channel(channel)
        normalized_payload = self._normalize_payload(payload)

        async with self._lock:
            self._ensure_open()
            queues = list(self._subscribers.get(normalized_channel, set()))

        for queue in queues:
            await queue.put(normalized_payload)

    async def subscribe(self, channel: str) -> AsyncIterator[bytes]:
        """Subscribe to one local memory channel and yield payload bytes."""
        normalized_channel = normalize_runtime_broker_channel(channel)
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
        normalized_channel = normalize_runtime_broker_channel(channel)
        normalized_payload = self._normalize_payload(payload)
        client = await self._get_client()

        try:
            await client.publish(normalized_channel, normalized_payload)
        except Exception as exc:
            raise NsRuntimeBrokerError(f"runtime redis broker publish failed: {exc}") from exc

    async def subscribe(self, channel: str) -> AsyncIterator[bytes]:
        """Subscribe to one Redis/ValKey PubSub channel and yield payload bytes."""
        normalized_channel = normalize_runtime_broker_channel(channel)
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
            with contextlib.suppress(Exception):
                await pubsub.unsubscribe(normalized_channel)
            with contextlib.suppress(Exception):
                await pubsub.close()

    async def close(self) -> None:
        """Close Redis/ValKey broker resources."""
        async with self._client_lock:
            self._closed = True
            client = self._client
            self._client = None

        if client is not None:
            with contextlib.suppress(Exception):
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
    def _normalize_payload(payload: bytes) -> bytes:
        """Normalize broker payload."""
        if isinstance(payload, bytes):
            return payload

        if isinstance(payload, bytearray):
            return bytes(payload)

        raise NsRuntimeBrokerError("runtime broker payload must be bytes")


def normalize_runtime_broker_channel(channel: str) -> str:
    """Normalize runtime broker channel name."""
    normalized = str(channel or "").strip()
    if not normalized:
        raise NsRuntimeBrokerError("runtime broker channel is required")
    return normalized


def normalize_runtime_broker_event_type(event_type: str) -> str:
    """Normalize runtime broker envelope event type."""
    normalized = str(event_type or "").strip()
    if not normalized:
        raise NsRuntimeValidationError("runtime broker envelope event_type is required")
    return normalized

def is_known_runtime_broker_event_type(event_type: str) -> bool:
    """Return whether event type is a known runtime broker control-plane event."""
    try:
        normalized = normalize_runtime_broker_event_type(event_type)
    except NsRuntimeValidationError:
        return False

    return normalized in RUNTIME_BROKER_EVENT_TYPES


def ensure_runtime_broker_event_type_known(event_type: str) -> str:
    """Normalize and ensure event type is a known runtime broker control-plane event.

    This helper is intentionally not called by NsRuntimeBrokerEnvelope.normalized()
    so custom future events can still be transported. Runtime core listener uses
    this helper to classify current control-plane events.
    """
    normalized = normalize_runtime_broker_event_type(event_type)
    if normalized not in RUNTIME_BROKER_EVENT_TYPES:
        raise NsRuntimeValidationError(f"runtime broker event_type is unknown: {normalized}")

    return normalized

def build_runtime_broker_channel(*, namespace: str, name: str) -> str:
    """Build namespaced runtime broker channel."""
    normalized_namespace = str(namespace or "").strip() or RUNTIME_BROKER_DEFAULT_NAMESPACE
    normalized_name = str(name or "").strip()

    if not normalized_name:
        raise NsRuntimeBrokerError("runtime broker channel name is required")

    return f"{normalized_namespace}:{normalized_name}"


def build_runtime_broker_cluster_channel(*, namespace: str = RUNTIME_BROKER_DEFAULT_NAMESPACE) -> str:
    """Build runtime cluster-level broker channel."""
    return build_runtime_broker_channel(namespace=namespace, name=RUNTIME_BROKER_CLUSTER_CHANNEL)


def build_runtime_broker_node_channel(*, node_id: str, namespace: str = RUNTIME_BROKER_DEFAULT_NAMESPACE) -> str:
    """Build runtime node-specific broker channel."""
    normalized_node_id = str(node_id or "").strip()
    if not normalized_node_id:
        raise NsRuntimeBrokerError("runtime broker node_id is required")

    return build_runtime_broker_channel(namespace=namespace, name=f"{RUNTIME_BROKER_NODE_CHANNEL_PREFIX}:{normalized_node_id}")


def build_runtime_broker(config: NsRuntimeConfig | None = None) -> MemoryRuntimeBroker | RedisRuntimeBroker:
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
