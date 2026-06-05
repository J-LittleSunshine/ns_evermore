# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import signal
from dataclasses import dataclass
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
from ns_runtime.connection import NsRuntimeConnection
from ns_runtime.dispatcher import NsRuntimeDispatcher
from ns_runtime.protocol import (
    RUNTIME_FRAME_ACK,
    RUNTIME_FRAME_BACKEND_HEARTBEAT,
    RUNTIME_FRAME_BACKEND_PUBLISH,
    RUNTIME_FRAME_BACKEND_REGISTER,
    RUNTIME_FRAME_RUNTIME_FORWARD,
    RUNTIME_FRAME_RUNTIME_HEARTBEAT,
    RUNTIME_FRAME_RUNTIME_REGISTER,
    NsRuntimeWireFrame,
    build_ack_frame,
    build_runtime_heartbeat_frame,
    build_runtime_register_frame,
    runtime_message_from_forward_payload,
    runtime_message_from_payload,
)
from ns_runtime.registry import NsRuntimeConnectionRegistry


@dataclass(slots=True, frozen=True, kw_only=True)
class NsRuntimeNodeStats:
    """Runtime node in-process statistics."""

    opened_connection_count: int = 0
    active_connection_count: int = 0

    backend_register_count: int = 0
    backend_heartbeat_count: int = 0
    backend_publish_count: int = 0

    sub_register_count: int = 0
    sub_heartbeat_count: int = 0
    runtime_forward_count: int = 0

    accepted_count: int = 0
    rejected_count: int = 0
    forwarded_count: int = 0
    local_handled_count: int = 0

    last_error: str | None = None


class NsRuntimeNode:
    """Standalone ns_runtime core node.

    P7 supports:
    - standalone runtime node: handle backend.publish locally
    - master runtime node: forward backend.publish to healthy sub nodes first
    - sub runtime node: connect to master and handle runtime.forward locally

    Frontend connection management, presence, broker, IAM service token auth,
    and business routing are intentionally deferred.
    """

    def __init__(self, *, config: NsRuntimeConfig | None = None, host: str | None = None, port: int | None = None, path: str | None = None) -> None:
        """Initialize runtime node from ns_common config and optional bind overrides."""
        self._config: NsRuntimeConfig = config or ns_config.runtime_config
        self._host, self._port, self._path = self._resolve_bind_options(host=host, port=port, path=path)

        self._stop_event = Event()
        self._stats_lock = RLock()
        self._stats = NsRuntimeNodeStats()
        self._registry = NsRuntimeConnectionRegistry()
        self._dispatcher = NsRuntimeDispatcher(config=self._config, registry=self._registry)

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
            if self._config.node_role == RUNTIME_NODE_ROLE_SUB:
                asyncio.run(self._run_sub_client())
                return

            asyncio.run(self._run_server())
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop runtime node."""
        self._stop_event.set()

    async def _run_server(self) -> None:
        """Run WebSocket server lifecycle for standalone/master node."""
        try:
            import websockets
        except ImportError as exc:
            raise NsRuntimeConfigurationError("websockets package is required for runtime node") from exc

        async with websockets.serve(self._handle_connection, self._host, self._port, ping_interval=20, ping_timeout=20, max_size=2 ** 20, max_queue=32):
            while not self._stop_event.is_set():
                await asyncio.sleep(0.2)

    async def _run_sub_client(self) -> None:
        """Run sub node as WebSocket client connected to master."""
        try:
            import websockets
        except ImportError as exc:
            raise NsRuntimeConfigurationError("websockets package is required for runtime sub node") from exc

        reconnect_delay: float = max(float(self._config.retry_base_delay_seconds), 1.0)
        max_delay: float = max(float(self._config.retry_max_delay_seconds), reconnect_delay)

        while not self._stop_event.is_set():
            try:
                async with websockets.connect(self._config.master_url, ping_interval=20, ping_timeout=20, max_size=2 ** 20, max_queue=32) as websocket:
                    connection = NsRuntimeConnection(
                        websocket=websocket,
                        connection_type="runtime_sub",
                        node_id=self._config.node_id,
                        node_role=RUNTIME_NODE_ROLE_SUB,
                        remote_address=str(self._config.master_url),
                    )
                    self._registry.add_unknown(connection)

                    await connection.send_frame(
                        build_runtime_register_frame(
                            node_id=self._config.node_id,
                            node_role=RUNTIME_NODE_ROLE_SUB,
                            parent_node_id=None,
                        )
                    )

                    heartbeat_task = asyncio.create_task(self._sub_heartbeat_loop(connection))
                    receive_task = asyncio.create_task(self._sub_receive_loop(connection))

                    done, pending = await asyncio.wait(
                        {heartbeat_task, receive_task},
                        return_when=asyncio.FIRST_EXCEPTION,
                    )

                    for task in pending:
                        task.cancel()

                    for task in done:
                        task.result()
            except Exception as exc:
                self._registry.remove(self._config.node_id, exc)
                self._add_stats(rejected_count=1, last_error=str(exc))

                if self._stop_event.is_set():
                    break

                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, max_delay)
                continue

            reconnect_delay = max(float(self._config.retry_base_delay_seconds), 1.0)

    async def _sub_receive_loop(self, connection: NsRuntimeConnection) -> None:
        """Receive frames from master on sub node connection."""
        async for raw_message in connection.websocket:
            try:
                frame = NsRuntimeWireFrame.from_json(raw_message)
                await self._handle_sub_frame(connection, frame)
            except Exception as exc:
                self._add_stats(rejected_count=1, last_error=str(exc))

    async def _sub_heartbeat_loop(self, connection: NsRuntimeConnection) -> None:
        """Send runtime.heartbeat frames from sub node to master."""
        interval_seconds: float = max(float(self._config.heartbeat_interval_seconds), 1.0)

        while not self._stop_event.is_set():
            await asyncio.sleep(interval_seconds)
            await connection.send_frame(
                build_runtime_heartbeat_frame(
                    node_id=self._config.node_id,
                    node_role=RUNTIME_NODE_ROLE_SUB,
                    health={
                        "active_connections": self._registry.count_active(),
                        "handled_messages": self._stats.local_handled_count,
                    },
                )
            )

    async def _handle_connection(self, websocket: Any, *args: Any) -> None:
        """Handle one inbound WebSocket connection on standalone/master node."""
        request_path: str | None = self._extract_request_path(websocket, args)
        if request_path and self._path and request_path != self._path:
            await websocket.close(code=1008, reason="unsupported runtime websocket path")
            return

        connection = NsRuntimeConnection(
            websocket=websocket,
            remote_address=self._format_remote_address(getattr(websocket, "remote_address", None)),
        )
        self._registry.add_unknown(connection)
        self._add_stats(opened_connection_count=1, active_connection_delta=1)

        try:
            async for raw_message in websocket:
                try:
                    frame = NsRuntimeWireFrame.from_json(raw_message)
                    await self._handle_server_frame(connection, frame)
                except NsRuntimeValidationError as exc:
                    self._add_stats(rejected_count=1, last_error=str(exc))
                except Exception as exc:  # noqa
                    self._add_stats(rejected_count=1, last_error=str(exc))
        finally:
            self._registry.remove(connection.connection_id, RuntimeError("runtime websocket connection closed"))
            self._add_stats(active_connection_delta=-1)

    async def _handle_server_frame(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame) -> None:
        """Dispatch one inbound server-side wire frame."""
        if frame.frame_type == RUNTIME_FRAME_ACK:
            handled: bool = connection.resolve_ack(frame)
            if not handled:
                self._add_stats(last_error=f"runtime ack has no pending waiter: {frame.message_id}")
            return

        if frame.frame_type == RUNTIME_FRAME_BACKEND_REGISTER:
            await self._handle_backend_register(connection, frame)
            return

        if frame.frame_type == RUNTIME_FRAME_BACKEND_HEARTBEAT:
            await self._handle_backend_heartbeat(connection, frame)
            return

        if frame.frame_type == RUNTIME_FRAME_BACKEND_PUBLISH:
            await self._handle_backend_publish(connection, frame)
            return

        if frame.frame_type == RUNTIME_FRAME_RUNTIME_REGISTER:
            await self._handle_runtime_register(connection, frame)
            return

        if frame.frame_type == RUNTIME_FRAME_RUNTIME_HEARTBEAT:
            await self._handle_runtime_heartbeat(connection, frame)
            return

        await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason=f"unsupported runtime frame type: {frame.frame_type}")
        self._add_stats(rejected_count=1, last_error=f"unsupported runtime frame type: {frame.frame_type}")

    async def _handle_sub_frame(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame) -> None:
        """Dispatch one frame received by sub node from master."""
        if frame.frame_type == RUNTIME_FRAME_ACK:
            connection.resolve_ack(frame)
            return

        if frame.frame_type == RUNTIME_FRAME_RUNTIME_FORWARD:
            await self._handle_runtime_forward(connection, frame)
            return

        if frame.frame_type in {RUNTIME_FRAME_BACKEND_REGISTER, RUNTIME_FRAME_BACKEND_HEARTBEAT, RUNTIME_FRAME_BACKEND_PUBLISH}:
            await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason="sub runtime node does not accept backend frames")
            return

        await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason=f"unsupported sub runtime frame type: {frame.frame_type}")
        self._add_stats(rejected_count=1, last_error=f"unsupported sub runtime frame type: {frame.frame_type}")

    async def _handle_backend_register(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame) -> None:
        """Register one backend connector connection."""
        self._registry.register_backend(
            connection.connection_id,
            payload=dict(frame.payload),
            remote_address=connection.remote_address,
        )
        self._add_stats(backend_register_count=1, accepted_count=1)
        await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_ACCEPTED)

    async def _handle_backend_heartbeat(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame) -> None:
        """Update backend connector heartbeat state."""
        payload: dict[str, Any] = dict(frame.payload)
        self._registry.refresh_backend(connection.connection_id, health=dict(payload.get("health") or {}))
        self._add_stats(backend_heartbeat_count=1, accepted_count=1)
        await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_ACCEPTED)

    async def _handle_backend_publish(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame) -> None:
        """Dispatch backend.publish through standalone/master policy."""
        self._add_stats(backend_publish_count=1)

        try:
            message: NsRuntimeMessage = runtime_message_from_payload(frame.payload)
            ack: NsRuntimeAck = await self._dispatcher.dispatch_backend_publish(message)
        except Exception as exc:
            await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason=str(exc))
            self._add_stats(rejected_count=1, last_error=str(exc))
            return

        await connection.send_frame(build_ack_frame(ack))

        if ack.status == RUNTIME_ACK_STATUS_ACCEPTED:
            if ack.handled_by == self._config.node_id:
                self._add_stats(accepted_count=1, local_handled_count=1)
            else:
                self._add_stats(accepted_count=1, forwarded_count=1)
            return

        self._add_stats(rejected_count=1, last_error=ack.reason)

    async def _handle_runtime_register(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame) -> None:
        """Register one runtime sub node on master."""
        if self._config.node_role != RUNTIME_NODE_ROLE_MASTER:
            await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason="only master runtime node accepts runtime.register")
            self._add_stats(rejected_count=1)
            return

        try:
            self._registry.register_sub_node(
                connection.connection_id,
                payload=dict(frame.payload),
                remote_address=connection.remote_address,
            )
        except Exception as exc:
            await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason=str(exc))
            self._add_stats(rejected_count=1, last_error=str(exc))
            return

        self._add_stats(sub_register_count=1, accepted_count=1)
        await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_ACCEPTED)

    async def _handle_runtime_heartbeat(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame) -> None:
        """Update runtime sub node heartbeat state."""
        if self._config.node_role != RUNTIME_NODE_ROLE_MASTER:
            await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason="only master runtime node accepts runtime.heartbeat")
            self._add_stats(rejected_count=1)
            return

        payload: dict[str, Any] = dict(frame.payload)
        self._registry.refresh_sub_node(connection.connection_id, health=dict(payload.get("health") or {}))
        self._add_stats(sub_heartbeat_count=1, accepted_count=1)
        await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_ACCEPTED)

    async def _handle_runtime_forward(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame) -> None:
        """Handle runtime.forward on sub node."""
        if self._config.node_role != RUNTIME_NODE_ROLE_SUB:
            await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason="runtime.forward is only accepted by sub runtime node")
            self._add_stats(rejected_count=1)
            return

        try:
            message: NsRuntimeMessage = runtime_message_from_forward_payload(frame.payload)
            ack: NsRuntimeAck = self._dispatcher.local_handle(message)
        except Exception as exc:
            await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason=str(exc))
            self._add_stats(runtime_forward_count=1, rejected_count=1, last_error=str(exc))
            return

        await connection.send_frame(build_ack_frame(ack))
        self._add_stats(runtime_forward_count=1, accepted_count=1, local_handled_count=1)

    async def _send_ack(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame, *, status: str, reason: str | None = None) -> None:
        """Send one ack frame through a runtime connection."""
        ack: NsRuntimeAck = NsRuntimeAck(
            message_id=frame.message_id,
            status=status,  # type: ignore[arg-type]
            reason=reason,
            handled_by=self._config.node_id,
            trace_id=frame.trace_id,
        ).normalized()

        await connection.send_frame(build_ack_frame(ack))

    def _ensure_enabled(self) -> None:
        """Ensure runtime node is enabled."""
        if not self._config.enabled:
            raise NsRuntimeConfigurationError("runtime node is disabled")

    def _ensure_supported_role(self) -> None:
        """Ensure current node role is supported."""
        if self._config.node_role not in {RUNTIME_NODE_ROLE_STANDALONE, RUNTIME_NODE_ROLE_MASTER, RUNTIME_NODE_ROLE_SUB}:
            raise NsRuntimeConfigurationError(f"runtime node_role is invalid: {self._config.node_role}")

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
            sub_register_count: int = 0,
            sub_heartbeat_count: int = 0,
            runtime_forward_count: int = 0,
            accepted_count: int = 0,
            rejected_count: int = 0,
            forwarded_count: int = 0,
            local_handled_count: int = 0,
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
                sub_register_count=self._stats.sub_register_count + sub_register_count,
                sub_heartbeat_count=self._stats.sub_heartbeat_count + sub_heartbeat_count,
                runtime_forward_count=self._stats.runtime_forward_count + runtime_forward_count,
                accepted_count=self._stats.accepted_count + accepted_count,
                rejected_count=self._stats.rejected_count + rejected_count,
                forwarded_count=self._stats.forwarded_count + forwarded_count,
                local_handled_count=self._stats.local_handled_count + local_handled_count,
                last_error=last_error if last_error is not None else self._stats.last_error,
            )

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
