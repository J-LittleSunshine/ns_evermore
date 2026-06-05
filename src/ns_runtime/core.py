# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import json
import signal
import time
import uuid
from dataclasses import dataclass, field
from threading import Event, RLock
from typing import Any
from urllib.parse import urlparse

from ns_common.config import ns_config
from ns_common.runtime.config import NsRuntimeConfig
from ns_common.runtime.constants import (
    RUNTIME_ACK_STATUS_ACCEPTED,
    RUNTIME_ACK_STATUS_REJECTED,
    RUNTIME_NODE_ROLE_MASTER,
    RUNTIME_NODE_ROLE_STANDALONE,
    RUNTIME_NODE_ROLE_SUB,
)
from ns_common.runtime.errors import NsRuntimeConfigurationError, NsRuntimeValidationError
from ns_common.runtime.messages import NsRuntimeAck, NsRuntimeMessage


@dataclass(slots=True, frozen=True, kw_only=True)
class NsRuntimeBackendConnection:
    """Registered backend connector connection snapshot."""

    connection_id: str
    instance_id: str
    service_name: str = "ns_backend"
    version: str = ""
    environment: str = ""
    remote_address: str = ""
    registered_at_epoch_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    last_seen_epoch_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    health: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True, frozen=True, kw_only=True)
class NsRuntimeNodeStats:
    """Runtime node in-process statistics."""

    opened_connection_count: int = 0
    active_connection_count: int = 0
    backend_register_count: int = 0
    backend_heartbeat_count: int = 0
    backend_publish_count: int = 0
    accepted_count: int = 0
    rejected_count: int = 0
    last_error: str | None = None


@dataclass(slots=True, frozen=True, kw_only=True)
class _RuntimeWireFrame:
    """Minimal backend wire frame parser used by ns_runtime node."""

    frame_type: str
    message_id: str
    trace_id: str | None = None
    created_at_epoch_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    payload: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "_RuntimeWireFrame":
        """Deserialize a backend wire frame."""
        if not isinstance(data, dict):
            raise NsRuntimeValidationError("runtime wire frame must be a JSON object")

        frame_type: str = str(data.get("type") or "").strip()
        if not frame_type:
            raise NsRuntimeValidationError("runtime wire frame type is required")

        payload_raw: Any = data.get("payload") or {}
        if not isinstance(payload_raw, dict):
            raise NsRuntimeValidationError("runtime wire frame payload must be a JSON object")

        return cls(
            frame_type=frame_type,
            message_id=str(data.get("message_id") or "").strip() or uuid.uuid4().hex,
            trace_id=str(data.get("trace_id")).strip() if data.get("trace_id") is not None and str(data.get("trace_id")).strip() else None,
            created_at_epoch_ms=int(data.get("created_at_epoch_ms") or int(time.time() * 1000)),
            payload=dict(payload_raw),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the wire frame."""
        return {
            "type": self.frame_type,
            "message_id": self.message_id,
            "trace_id": self.trace_id,
            "created_at_epoch_ms": self.created_at_epoch_ms,
            "payload": dict(self.payload),
        }


class NsRuntimeNode:
    """Standalone ns_runtime core node.

    P6 only accepts backend connector WebSocket frames:
    - backend.register
    - backend.heartbeat
    - backend.publish

    This component intentionally does not depend on Django. Frontend connection
    management, sub-node forwarding, broker, presence, IAM service token auth,
    and business routing are deferred to later stages.
    """

    def __init__(self, *, config: NsRuntimeConfig | None = None, host: str | None = None, port: int | None = None, path: str | None = None) -> None:
        """Initialize runtime node from ns_common config and optional bind overrides."""
        self._config: NsRuntimeConfig = config or ns_config.runtime_config
        self._host, self._port, self._path = self._resolve_bind_options(host=host, port=port, path=path)

        self._stop_event = Event()
        self._stats_lock = RLock()
        self._stats = NsRuntimeNodeStats()
        self._backend_connections: dict[str, NsRuntimeBackendConnection] = {}

    @property
    def host(self) -> str:
        """Return bind host."""
        return self._host

    @property
    def port(self) -> int:
        """Return bind port."""
        return self._port

    @property
    def path(self) -> str:
        """Return expected WebSocket path."""
        return self._path

    @property
    def stats(self) -> NsRuntimeNodeStats:
        """Return runtime node stats snapshot."""
        with self._stats_lock:
            return self._stats

    def run_forever(self) -> None:
        """Run runtime node until stop() is called."""
        self._ensure_enabled()
        self._ensure_supported_role()
        self._install_signal_handlers()

        try:
            asyncio.run(self._run_server())
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop runtime node."""
        self._stop_event.set()

    async def _run_server(self) -> None:
        """Run WebSocket server lifecycle."""
        try:
            import websockets
        except ImportError as exc:
            raise NsRuntimeConfigurationError("websockets package is required for runtime node") from exc

        async with websockets.serve(self._handle_connection, self._host, self._port):
            while not self._stop_event.is_set():
                await asyncio.sleep(0.2)

    async def _handle_connection(self, websocket: Any, *args: Any) -> None:
        """Handle one backend connector WebSocket connection."""
        request_path: str | None = self._extract_request_path(websocket, args)
        if request_path and self._path and request_path != self._path:
            await websocket.close(code=1008, reason="unsupported runtime websocket path")
            return

        connection_id: str = uuid.uuid4().hex
        self._add_stats(opened_connection_count=1, active_connection_delta=1)

        try:
            async for raw_message in websocket:
                try:
                    data: dict[str, Any] = self._loads_frame(raw_message)
                    frame: _RuntimeWireFrame = _RuntimeWireFrame.from_dict(data)
                    await self._handle_frame(websocket, connection_id, frame)
                except NsRuntimeValidationError as exc:
                    self._add_stats(rejected_count=1, last_error=str(exc))
                except Exception as exc:  # noqa
                    self._add_stats(rejected_count=1, last_error=str(exc))
        finally:
            self._backend_connections.pop(connection_id, None)
            self._add_stats(active_connection_delta=-1)

    async def _handle_frame(self, websocket: Any, connection_id: str, frame: _RuntimeWireFrame) -> None:
        """Dispatch one backend wire frame."""
        if frame.frame_type == "backend.register":
            await self._handle_backend_register(websocket, connection_id, frame)
            return

        if frame.frame_type == "backend.heartbeat":
            await self._handle_backend_heartbeat(websocket, connection_id, frame)
            return

        if frame.frame_type == "backend.publish":
            await self._handle_backend_publish(websocket, frame)
            return

        await self._send_ack(
            websocket,
            frame,
            status=RUNTIME_ACK_STATUS_REJECTED,
            reason=f"unsupported runtime frame type: {frame.frame_type}",
        )
        self._add_stats(rejected_count=1, last_error=f"unsupported runtime frame type: {frame.frame_type}")

    async def _handle_backend_register(self, websocket: Any, connection_id: str, frame: _RuntimeWireFrame) -> None:
        """Register one backend connector connection."""
        payload: dict[str, Any] = dict(frame.payload)
        instance_id: str = str(payload.get("instance_id") or "").strip() or connection_id
        remote_address: str = self._format_remote_address(getattr(websocket, "remote_address", None))

        self._backend_connections[connection_id] = NsRuntimeBackendConnection(
            connection_id=connection_id,
            instance_id=instance_id,
            service_name=str(payload.get("service_name") or "ns_backend").strip() or "ns_backend",
            version=str(payload.get("version") or "").strip(),
            environment=str(payload.get("environment") or "").strip(),
            remote_address=remote_address,
        )

        self._add_stats(backend_register_count=1, accepted_count=1)

        # Register ack is not required by P5 sender, but it keeps the wire
        # protocol symmetric and harmless for future clients.
        await self._send_ack(websocket, frame, status=RUNTIME_ACK_STATUS_ACCEPTED)

    async def _handle_backend_heartbeat(self, websocket: Any, connection_id: str, frame: _RuntimeWireFrame) -> None:
        """Update backend connector heartbeat state."""
        payload: dict[str, Any] = dict(frame.payload)
        existing: NsRuntimeBackendConnection | None = self._backend_connections.get(connection_id)

        if existing is not None:
            self._backend_connections[connection_id] = NsRuntimeBackendConnection(
                connection_id=existing.connection_id,
                instance_id=existing.instance_id,
                service_name=existing.service_name,
                version=existing.version,
                environment=existing.environment,
                remote_address=existing.remote_address,
                registered_at_epoch_ms=existing.registered_at_epoch_ms,
                last_seen_epoch_ms=int(time.time() * 1000),
                health=dict(payload.get("health") or {}),
            )

        self._add_stats(backend_heartbeat_count=1, accepted_count=1)

        # Heartbeat ack is currently ignored by backend sender if there is no
        # matching pending ack future, so this does not affect publish ack flow.
        await self._send_ack(websocket, frame, status=RUNTIME_ACK_STATUS_ACCEPTED)

    async def _handle_backend_publish(self, websocket: Any, frame: _RuntimeWireFrame) -> None:
        """Accept one backend publish frame.

        P6 only acknowledges ingestion. Routing, frontend fanout, broker publish,
        presence matching, and sub-node forwarding are intentionally deferred.
        """
        try:
            message: NsRuntimeMessage = self._message_from_payload(frame.payload)
            _ = message
        except Exception as exc:
            await self._send_ack(websocket, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason=str(exc))
            self._add_stats(backend_publish_count=1, rejected_count=1, last_error=str(exc))
            return

        await self._send_ack(websocket, frame, status=RUNTIME_ACK_STATUS_ACCEPTED)
        self._add_stats(backend_publish_count=1, accepted_count=1)

    async def _send_ack(self, websocket: Any, frame: _RuntimeWireFrame, *, status: str, reason: str | None = None) -> None:
        """Send one ack frame to backend connector."""
        ack: NsRuntimeAck = NsRuntimeAck(
            message_id=frame.message_id,
            status=status,  # type: ignore[arg-type]
            reason=reason,
            handled_by=self._config.node_id,
            trace_id=frame.trace_id,
        ).normalized()

        ack_frame = _RuntimeWireFrame(
            frame_type="ack",
            message_id=ack.message_id,
            trace_id=ack.trace_id,
            payload=ack.to_dict(),
        )

        await websocket.send(json.dumps(ack_frame.to_dict(), ensure_ascii=False, separators=(",", ":")))

    def _message_from_payload(self, payload: dict[str, Any]) -> NsRuntimeMessage:
        """Build and validate NsRuntimeMessage from backend.publish payload."""
        target: dict[str, Any] = dict(payload.get("target") or {})
        producer: dict[str, Any] = dict(payload.get("producer") or {})

        ttl_raw: Any = payload.get("ttl_seconds", 300)
        ttl_seconds: int | None
        if ttl_raw is None:
            ttl_seconds = None
        else:
            ttl_seconds = int(ttl_raw)

        created_at_raw: Any = payload.get("created_at_epoch_ms")
        created_at_epoch_ms: int | None
        if created_at_raw is None:
            created_at_epoch_ms = None
        else:
            created_at_epoch_ms = int(created_at_raw)

        message_payload: Any = payload.get("payload") or {}
        if not isinstance(message_payload, dict):
            raise NsRuntimeValidationError("runtime publish payload.payload must be a JSON object")

        headers_raw: Any = payload.get("headers") or {}
        if not isinstance(headers_raw, dict):
            raise NsRuntimeValidationError("runtime publish payload.headers must be a JSON object")

        return NsRuntimeMessage(
            topic=str(payload.get("topic") or ""),
            event=str(payload.get("event") or ""),
            payload=dict(message_payload),
            target_type=str(target.get("type") or "user"),  # type: ignore[arg-type]
            target_id=target.get("id"),
            producer_type=str(producer.get("type") or "backend"),  # type: ignore[arg-type]
            producer_id=str(producer.get("id")).strip() if producer.get("id") is not None and str(producer.get("id")).strip() else None,
            message_id=str(payload.get("message_id") or ""),
            trace_id=str(payload.get("trace_id")).strip() if payload.get("trace_id") is not None and str(payload.get("trace_id")).strip() else None,
            idempotency_key=str(payload.get("idempotency_key")).strip() if payload.get("idempotency_key") is not None and str(payload.get("idempotency_key")).strip() else None,
            ttl_seconds=ttl_seconds,
            require_ack=bool(payload.get("require_ack", True)),
            created_at_epoch_ms=created_at_epoch_ms,
            headers={str(key).strip(): str(value).strip() for key, value in headers_raw.items() if str(key).strip()},
        ).normalized()

    def _ensure_enabled(self) -> None:
        """Ensure runtime node is enabled."""
        if not self._config.enabled:
            raise NsRuntimeConfigurationError("runtime node is disabled")

    def _ensure_supported_role(self) -> None:
        """Ensure current node role is supported by P6."""
        if self._config.node_role not in {RUNTIME_NODE_ROLE_STANDALONE, RUNTIME_NODE_ROLE_MASTER, RUNTIME_NODE_ROLE_SUB}:
            raise NsRuntimeConfigurationError(f"runtime node_role is invalid: {self._config.node_role}")

        if self._config.node_role == RUNTIME_NODE_ROLE_SUB:
            raise NsRuntimeConfigurationError("runtime node_role sub is reserved and not supported in P6")

    def _resolve_bind_options(self, *, host: str | None, port: int | None, path: str | None) -> tuple[str, int, str]:
        """Resolve bind host, port and path from runtime.master_url with overrides."""
        parsed = urlparse(str(self._config.master_url or "").strip())

        resolved_host: str = str(host or parsed.hostname or "127.0.0.1").strip()
        resolved_port: int = port if port is not None else int(parsed.port or (443 if parsed.scheme == "wss" else 80))
        resolved_path: str = str(path or parsed.path or "/").strip() or "/"

        if not resolved_path.startswith("/"):
            resolved_path = f"/{resolved_path}"

        if not resolved_host:
            raise NsRuntimeConfigurationError("runtime node bind host is required")

        if isinstance(resolved_port, bool) or resolved_port <= 0:
            raise NsRuntimeConfigurationError("runtime node bind port must be a positive int")

        return resolved_host, resolved_port, resolved_path

    def _install_signal_handlers(self) -> None:
        """Install best-effort signal handlers for graceful shutdown."""
        try:
            signal.signal(signal.SIGINT, lambda _sig, _frame: self.stop())
            signal.signal(signal.SIGTERM, lambda _sig, _frame: self.stop())
        except ValueError:
            # Signal handlers can only be installed in main thread.
            pass

    def _add_stats(
            self,
            *,
            opened_connection_count: int = 0,
            active_connection_delta: int = 0,
            backend_register_count: int = 0,
            backend_heartbeat_count: int = 0,
            backend_publish_count: int = 0,
            accepted_count: int = 0,
            rejected_count: int = 0,
            last_error: str | None = None,
    ) -> None:
        """Update node stats."""
        with self._stats_lock:
            active_connection_count: int = max(0, self._stats.active_connection_count + active_connection_delta)
            self._stats = NsRuntimeNodeStats(
                opened_connection_count=self._stats.opened_connection_count + opened_connection_count,
                active_connection_count=active_connection_count,
                backend_register_count=self._stats.backend_register_count + backend_register_count,
                backend_heartbeat_count=self._stats.backend_heartbeat_count + backend_heartbeat_count,
                backend_publish_count=self._stats.backend_publish_count + backend_publish_count,
                accepted_count=self._stats.accepted_count + accepted_count,
                rejected_count=self._stats.rejected_count + rejected_count,
                last_error=last_error if last_error is not None else self._stats.last_error,
            )

    @staticmethod
    def _loads_frame(raw_message: Any) -> dict[str, Any]:
        """Decode one JSON WebSocket frame."""
        if isinstance(raw_message, bytes):
            raw_text: str = raw_message.decode("utf-8")
        else:
            raw_text = str(raw_message)

        try:
            data: Any = json.loads(raw_text)
        except json.JSONDecodeError as exc:
            raise NsRuntimeValidationError("runtime websocket frame is invalid JSON") from exc

        if not isinstance(data, dict):
            raise NsRuntimeValidationError("runtime websocket frame must be a JSON object")

        return data

    @staticmethod
    def _extract_request_path(websocket: Any, args: tuple[Any, ...]) -> str | None:
        """Extract request path across websockets versions."""
        if args:
            return str(args[0] or "") or None

        request: Any = getattr(websocket, "request", None)
        if request is not None and getattr(request, "path", None):
            return str(getattr(request, "path"))

        path: Any = getattr(websocket, "path", None)
        if path:
            return str(path)

        return None

    @staticmethod
    def _format_remote_address(remote_address: Any) -> str:
        """Format remote address for registry snapshots."""
        if remote_address is None:
            return ""

        if isinstance(remote_address, tuple):
            return ":".join(str(part) for part in remote_address)

        return str(remote_address)
