# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import contextlib
import signal
from dataclasses import dataclass, asdict
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
from ns_common.runtime.permissions import (
    RUNTIME_IAM_ACTION_CONNECT,
    RUNTIME_IAM_RESOURCE_FRONTEND,
    RUNTIME_PERMISSION_FRONTEND_CONNECT,
    RUNTIME_PRINCIPAL_ANONYMOUS_FRONTEND,
    RUNTIME_PRINCIPAL_BACKEND_SERVICE,
    RUNTIME_PRINCIPAL_FRONTEND_USER,
    RUNTIME_PRINCIPAL_RUNTIME_NODE,
    build_runtime_frontend_resource_id,
)
from ns_common.runtime.security import NsRuntimeAuthorizationRequest, NsRuntimePrincipal
from ns_runtime.auth_provider import NsRuntimeAuthProviderError, build_runtime_auth_provider
from ns_runtime.connection import NsRuntimeConnection
from ns_runtime.dispatcher import NsRuntimeDispatcher
from ns_runtime.presence import NsRuntimePresenceRecord, NsRuntimePresenceStore, build_runtime_presence_store
from ns_runtime.protocol import (
    RUNTIME_FRAME_ACK,
    RUNTIME_FRAME_BACKEND_HEARTBEAT,
    RUNTIME_FRAME_BACKEND_PUBLISH,
    RUNTIME_FRAME_BACKEND_REGISTER,
    RUNTIME_FRAME_BACKEND_REPLY,
    RUNTIME_FRAME_FRONTEND_ACK,
    RUNTIME_FRAME_FRONTEND_HEARTBEAT,
    RUNTIME_FRAME_FRONTEND_REGISTER,
    RUNTIME_FRAME_RUNTIME_FORWARD,
    RUNTIME_FRAME_RUNTIME_HEARTBEAT,
    RUNTIME_FRAME_RUNTIME_REGISTER,
    NsRuntimeWireFrame,
    backend_reply_message_from_payload,
    build_ack_frame,
    build_backend_deliver_frame,
    build_runtime_heartbeat_frame,
    build_runtime_register_frame,
    parse_ack_frame,
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

    frontend_register_count: int = 0
    frontend_heartbeat_count: int = 0
    frontend_ack_count: int = 0

    accepted_count: int = 0
    rejected_count: int = 0
    forwarded_count: int = 0
    local_handled_count: int = 0

    last_error: str | None = None


class NsRuntimeNode:
    """Standalone ns_runtime core node.

    P8 supports:
    - standalone runtime node: handle backend.publish and deliver to local frontend
    - master runtime node: forward backend.publish to healthy sub nodes first
    - sub runtime node: connect to master and handle runtime.forward locally
    - frontend WebSocket register / heartbeat / best-effort local delivery

    Presence, broker, IAM service token auth, and business routing are deferred.
    """

    def __init__(self, *, config: NsRuntimeConfig | None = None, host: str | None = None, port: int | None = None, path: str | None = None, serve_inbound: bool | None = None) -> None:
        """Initialize runtime node from ns_common config and optional bind overrides."""
        self._config: NsRuntimeConfig = config or ns_config.runtime_config
        self._host, self._port, self._path = self._resolve_bind_options(host=host, port=port, path=path)
        self._serve_inbound: bool = True if serve_inbound is None else bool(serve_inbound)

        self._stop_event = Event()
        self._stats_lock = RLock()
        self._stats = NsRuntimeNodeStats()
        self._registry = NsRuntimeConnectionRegistry()
        self._presence: NsRuntimePresenceStore = build_runtime_presence_store(self._config)
        self._dispatcher = NsRuntimeDispatcher(config=self._config, registry=self._registry)
        self._auth_provider = build_runtime_auth_provider(self._config)

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
    def serve_inbound(self) -> bool:
        """Return whether this node starts inbound WebSocket server."""
        return self._serve_inbound

    @property
    def stats(self) -> NsRuntimeNodeStats:
        """Return runtime node stats snapshot."""
        with self._stats_lock:
            return self._stats

    def stats_dict(self) -> dict[str, Any]:
        """Return runtime node stats as a JSON-compatible dict."""
        with self._stats_lock:
            return asdict(self._stats)

    def health_report(self) -> dict[str, Any]:
        """Return local runtime node health report.

        This report is used by runtime sub-node heartbeat and future diagnostics.
        It is local-process health only; it does not imply distributed cluster
        health or global presence consistency.
        """
        return {
            "node_id": self._config.node_id,
            "node_role": self._config.node_role,
            "bind": {
                "host": self._host,
                "port": self._port,
                "path": self._path,
                "serve_inbound": self._serve_inbound,
            },
            "connections": {
                "active": self._registry.count_active(),
                "backend": self._registry.count_backend(),
                "frontend": self._registry.count_frontend(),
                "runtime_sub_nodes": self._registry.count_sub_nodes(),
            },
            "presence": self.presence_counts(),
            "stats": self.stats_dict(),
        }

    def presence_counts(self) -> dict[str, int]:
        """Return local runtime presence counters.

        This is an in-process read-only helper for runtime internals and future
        diagnostics. It does not expose HTTP API and does not imply distributed
        presence consistency.
        """
        return self._presence.snapshot_counts()

    def get_presence_connection(self, connection_id: str) -> NsRuntimePresenceRecord | None:
        """Return one local online presence record by connection id."""
        return self._presence.get_connection(connection_id)

    def list_presence_frontends(self) -> list[NsRuntimePresenceRecord]:
        """Return local online frontend presence records."""
        return self._presence.list_online_frontends()

    def list_presence_backends(self) -> list[NsRuntimePresenceRecord]:
        """Return local online backend presence records."""
        return self._presence.list_online_backends()

    def list_presence_runtime_sub_nodes(self) -> list[NsRuntimePresenceRecord]:
        """Return local online runtime sub-node presence records."""
        return self._presence.list_online_runtime_sub_nodes()

    def list_presence_by_user(self, user_id: str) -> list[NsRuntimePresenceRecord]:
        """Return local online frontend presence records for one user."""
        return self._presence.list_online_by_user(user_id)

    def list_presence_by_session(self, session_id: str) -> list[NsRuntimePresenceRecord]:
        """Return local online frontend presence records for one session."""
        return self._presence.list_online_by_session(session_id)

    def list_presence_by_client(self, client_id: str) -> list[NsRuntimePresenceRecord]:
        """Return local online frontend presence records for one client."""
        return self._presence.list_online_by_client(client_id)

    def list_presence_by_room(self, room_id: str) -> list[NsRuntimePresenceRecord]:
        """Return local online frontend presence records for one room."""
        return self._presence.list_online_by_room(room_id)

    def run_forever(self) -> None:
        """Run runtime node until stop() is called."""
        self._ensure_enabled()
        self._ensure_supported_role()
        self._install_signal_handlers()

        try:
            if self._config.node_role == RUNTIME_NODE_ROLE_SUB:
                asyncio.run(self._run_sub_node())
                return

            asyncio.run(self._run_server())
        finally:
            self.stop()

    def stop(self) -> None:
        """Stop runtime node."""
        self._stop_event.set()

    async def _run_sub_node(self) -> None:
        """Run sub node client and optional inbound frontend server."""
        if not self._serve_inbound:
            await self._run_sub_client()
            return

        server_task = asyncio.create_task(self._run_server())
        client_task = asyncio.create_task(self._run_sub_client())

        done, pending = await asyncio.wait(
            {server_task, client_task},
            return_when=asyncio.FIRST_EXCEPTION,
        )

        for task in pending:
            task.cancel()

        for task in pending:
            with contextlib.suppress(asyncio.CancelledError):
                await task

        for task in done:
            task.result()

    async def _run_server(self) -> None:
        """Run WebSocket server lifecycle for standalone/master node or sub inbound frontend server."""
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
            connection: NsRuntimeConnection | None = None

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

                    register_frame = build_runtime_register_frame(
                        node_id=self._config.node_id,
                        node_role=RUNTIME_NODE_ROLE_SUB,
                        parent_node_id=None,
                        auth_token=self._config.service_token,
                    )
                    await connection.send_frame(register_frame)

                    # P11.8-B: runtime.forward is protected by registered runtime_sub
                    # state. The sub client must wait until master accepts
                    # runtime.register before it starts heartbeat / receive loops.
                    await self._await_sub_registration_ack(connection, register_frame)

                    heartbeat_task = asyncio.create_task(self._sub_heartbeat_loop(connection))
                    receive_task = asyncio.create_task(self._sub_receive_loop(connection))

                    done, pending = await asyncio.wait(
                        {heartbeat_task, receive_task},
                        return_when=asyncio.FIRST_COMPLETED,
                    )

                    for task in pending:
                        task.cancel()

                    for task in pending:
                        with contextlib.suppress(asyncio.CancelledError):
                            await task

                    for task in done:
                        task.result()
            except Exception as exc:
                if connection is not None:
                    self._remove_presence(connection.connection_id)
                    self._registry.remove(connection.connection_id, exc)

                self._add_stats(rejected_count=1, last_error=str(exc))

                if self._stop_event.is_set():
                    break

                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, max_delay)
                continue

            if connection is not None:
                self._remove_presence(connection.connection_id)
                self._registry.remove(connection.connection_id)

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
                    health=self.health_report(),
                )
            )

    async def _handle_connection(self, websocket: Any, *args: Any) -> None:
        """Handle one inbound WebSocket connection."""
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
            # P12-A: remove connection from local presence before registry cleanup.
            # The memory presence store is local-only and does not affect durable
            # message reliability.
            self._remove_presence(connection.connection_id)
            self._registry.remove(connection.connection_id, RuntimeError("runtime websocket connection closed"))
            self._add_stats(active_connection_delta=-1)

    async def _handle_server_frame(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame) -> None:
        """Dispatch one inbound server-side wire frame."""
        if frame.frame_type == RUNTIME_FRAME_ACK:
            handled: bool = connection.resolve_ack(frame)
            if not handled:
                self._add_stats(last_error=f"runtime ack has no pending waiter: {frame.message_id}")
            return

        if frame.frame_type == RUNTIME_FRAME_FRONTEND_REGISTER:
            await self._handle_frontend_register(connection, frame)
            return

        if frame.frame_type == RUNTIME_FRAME_FRONTEND_HEARTBEAT:
            await self._handle_frontend_heartbeat(connection, frame)
            return

        if frame.frame_type == RUNTIME_FRAME_FRONTEND_ACK:
            await self._handle_frontend_ack(connection, frame)
            return

        if self._config.node_role == RUNTIME_NODE_ROLE_SUB and frame.frame_type in {
            RUNTIME_FRAME_BACKEND_REGISTER,
            RUNTIME_FRAME_BACKEND_HEARTBEAT,
            RUNTIME_FRAME_BACKEND_PUBLISH,
            RUNTIME_FRAME_BACKEND_REPLY,
            RUNTIME_FRAME_RUNTIME_REGISTER,
            RUNTIME_FRAME_RUNTIME_HEARTBEAT,
        }:
            reason = "sub runtime node does not accept backend or runtime service frames"
            await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason=reason)
            self._add_stats(rejected_count=1, last_error=reason)
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

        if frame.frame_type == RUNTIME_FRAME_BACKEND_REPLY:
            await self._handle_backend_reply(connection, frame)
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

        if frame.frame_type in {
            RUNTIME_FRAME_BACKEND_REGISTER,
            RUNTIME_FRAME_BACKEND_HEARTBEAT,
            RUNTIME_FRAME_BACKEND_PUBLISH,
            RUNTIME_FRAME_BACKEND_REPLY,
        }:
            reason = "sub runtime node does not accept backend frames"
            await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason=reason)
            self._add_stats(rejected_count=1, last_error=reason)
            return

        await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason=f"unsupported sub runtime frame type: {frame.frame_type}")
        self._add_stats(rejected_count=1, last_error=f"unsupported sub runtime frame type: {frame.frame_type}")

    async def _handle_backend_register(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame) -> None:
        """Register one backend connector connection."""
        payload: dict[str, Any] = dict(frame.payload)

        try:
            principal = await self._auth_provider.authenticate_service(
                payload,
                principal_type=RUNTIME_PRINCIPAL_BACKEND_SERVICE,
                trace_id=frame.trace_id,
            )
            connection.principal = principal
        except Exception as exc:
            reason = str(exc)
            await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason=reason)
            self._add_stats(rejected_count=1, last_error=reason)
            await connection.websocket.close(code=1008, reason="runtime backend auth failed")
            return

        registered_connection = self._registry.register_backend(
            connection.connection_id,
            payload=payload,
            remote_address=connection.remote_address,
        )
        self._upsert_presence(registered_connection)

        self._add_stats(backend_register_count=1, accepted_count=1)
        await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_ACCEPTED)

    async def _handle_backend_heartbeat(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame) -> None:
        """Update backend connector heartbeat state."""
        payload: dict[str, Any] = dict(frame.payload)
        health = dict(payload.get("health") or {})

        if not await self._ensure_registered_backend_connection(connection, frame, health=health):
            return

        self._add_stats(backend_heartbeat_count=1, accepted_count=1)
        await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_ACCEPTED)

    async def _handle_backend_publish(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame) -> None:
        """Dispatch backend.publish through standalone/master policy."""
        if not await self._ensure_registered_backend_connection(connection, frame):
            return

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

    async def _handle_backend_reply(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame) -> None:
        """Forward backend.reply frame to backend connector as backend.deliver.

        P9 only provides the inbound reply channel skeleton. It does not
        implement a high-level backend request_reply API yet.
        """
        if not await self._ensure_registered_backend_connection(connection, frame):
            return

        try:
            message, target_backend_id, correlation_id, reply_to_message_id = backend_reply_message_from_payload(frame.payload)
            backend_connection = self._registry.select_backend_for_reply(target_backend_id)

            if backend_connection is None:
                await self._send_ack(
                    connection,
                    frame,
                    status=RUNTIME_ACK_STATUS_REJECTED,
                    reason="target backend connection is not available",
                )
                self._add_stats(rejected_count=1, last_error="target backend connection is not available")
                return
            deliver_frame = build_backend_deliver_frame(
                source_node_id=self._config.node_id,
                message=message,
                correlation_id=correlation_id,
                reply_to_message_id=reply_to_message_id,
            )

            pending_ack = backend_connection.create_pending_ack(deliver_frame.message_id)
            await backend_connection.send_frame(deliver_frame)

            backend_ack = await asyncio.wait_for(
                pending_ack,
                timeout=float(self._config.ack_timeout_seconds),
            )
        except Exception as exc:
            await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason=str(exc))
            self._add_stats(rejected_count=1, last_error=str(exc))
            return
        finally:
            try:
                backend_connection.remove_pending_ack(deliver_frame.message_id)  # type: ignore[name-defined]
            except Exception:  # noqa
                pass

        await self._send_ack(
            connection,
            frame,
            status=backend_ack.status,
            reason=backend_ack.reason,
        )

        if backend_ack.status == RUNTIME_ACK_STATUS_ACCEPTED:
            self._add_stats(accepted_count=1)
            return

        self._add_stats(rejected_count=1, last_error=backend_ack.reason)

    async def _handle_runtime_register(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame) -> None:
        """Register one runtime sub node on master."""
        if self._config.node_role != RUNTIME_NODE_ROLE_MASTER:
            await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason="only master runtime node accepts runtime.register")
            self._add_stats(rejected_count=1)
            return

        payload: dict[str, Any] = dict(frame.payload)

        try:
            principal = await self._auth_provider.authenticate_service(
                payload,
                principal_type=RUNTIME_PRINCIPAL_RUNTIME_NODE,
                trace_id=frame.trace_id,
            )
            connection.principal = principal
        except Exception as exc:
            reason = str(exc)
            await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason=reason)
            self._add_stats(rejected_count=1, last_error=reason)
            await connection.websocket.close(code=1008, reason="runtime sub node auth failed")
            return

        try:
            registered_connection = self._registry.register_sub_node(
                connection.connection_id,
                payload=payload,
                remote_address=connection.remote_address,
            )
            self._upsert_presence(registered_connection)
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
        health = dict(payload.get("health") or {})

        if not await self._ensure_registered_runtime_sub_connection(connection, frame, health=health):
            return

        self._add_stats(sub_heartbeat_count=1, accepted_count=1)
        await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_ACCEPTED)

    async def _handle_runtime_forward(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame) -> None:
        """Handle runtime.forward on sub node."""
        if self._config.node_role != RUNTIME_NODE_ROLE_SUB:
            await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason="runtime.forward is only accepted by sub runtime node")
            self._add_stats(rejected_count=1)
            return

        if not await self._ensure_registered_runtime_sub_connection(connection, frame):
            return

        try:
            message: NsRuntimeMessage = runtime_message_from_forward_payload(frame.payload)
            ack: NsRuntimeAck = await self._dispatcher.local_handle(message)
        except Exception as exc:
            await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason=str(exc))
            self._add_stats(runtime_forward_count=1, rejected_count=1, last_error=str(exc))
            return

        await connection.send_frame(build_ack_frame(ack))
        self._add_stats(runtime_forward_count=1, accepted_count=1, local_handled_count=1)

    async def _handle_frontend_register(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame) -> None:
        """Register one frontend WebSocket connection."""
        payload: dict[str, Any] = dict(frame.payload)

        try:
            principal = await self._auth_provider.authenticate_frontend(payload, trace_id=frame.trace_id)
            await self._authorize_frontend_connect(
                principal=principal,
                connection=connection,
                frame=frame,
                payload=payload,
            )
            connection.principal = principal
            payload = self._frontend_payload_with_principal(payload=payload, principal=principal)
        except Exception as exc:
            reason = str(exc)
            await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason=reason)
            self._add_stats(rejected_count=1, last_error=reason)
            await connection.websocket.close(code=1008, reason="runtime frontend auth failed")
            return

        try:
            registered_connection = self._registry.register_frontend(
                connection.connection_id,
                payload=payload,
                remote_address=connection.remote_address,
            )
            self._upsert_presence(registered_connection)
        except Exception as exc:
            await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason=str(exc))
            self._add_stats(rejected_count=1, last_error=str(exc))
            return

        self._add_stats(frontend_register_count=1, accepted_count=1)
        await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_ACCEPTED)

    async def _handle_frontend_heartbeat(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame) -> None:
        """Update frontend heartbeat state."""
        payload: dict[str, Any] = dict(frame.payload)
        health = dict(payload.get("health") or {})

        if not await self._ensure_registered_frontend_connection(connection, frame, health=health):
            return

        self._add_stats(frontend_heartbeat_count=1, accepted_count=1)
        await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_ACCEPTED)

    async def _handle_frontend_ack(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame) -> None:
        """Accept frontend ack frame without waiting on it in P8."""
        if not await self._ensure_registered_frontend_connection(connection, frame):
            return

        self._add_stats(frontend_ack_count=1, accepted_count=1)

    async def _authorize_frontend_connect(self, *, principal: NsRuntimePrincipal, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame, payload: dict[str, Any]) -> None:
        """Authorize frontend connect action.

        Anonymous frontend is controlled by authenticate_frontend(). If anonymous
        frontend is accepted there, this method does not call IAM authorize
        because P11.6 currently supports frontend_user authorization only.
        """
        if principal.principal_type == RUNTIME_PRINCIPAL_ANONYMOUS_FRONTEND:
            return

        if principal.principal_type != RUNTIME_PRINCIPAL_FRONTEND_USER:
            raise NsRuntimeAuthProviderError(f"unsupported frontend principal type: {principal.principal_type}")

        resource_id = build_runtime_frontend_resource_id(
            user_id=principal.user_id or principal.principal_id,
            client_id=principal.client_id or payload.get("client_id"),
        )

        decision = await self._auth_provider.authorize(
            NsRuntimeAuthorizationRequest(
                principal=principal,
                resource_type=RUNTIME_IAM_RESOURCE_FRONTEND,
                resource_id=resource_id,
                action_code=RUNTIME_IAM_ACTION_CONNECT,
                permission_code=RUNTIME_PERMISSION_FRONTEND_CONNECT,
                context={
                    "connection_id": connection.connection_id,
                    "remote_address": connection.remote_address,
                    "client_id": principal.client_id or payload.get("client_id"),
                    "session_id": principal.session_id or payload.get("session_id"),
                    "user_id": principal.user_id,
                    "frame_type": frame.frame_type,
                },
                trace_id=frame.trace_id,
            )
        )

        if not decision.allowed:
            raise NsRuntimeAuthProviderError(decision.reason or "runtime frontend connect is denied")

    @staticmethod
    def _frontend_payload_with_principal(*, payload: dict[str, Any], principal: NsRuntimePrincipal) -> dict[str, Any]:
        """Merge authenticated principal identity into frontend register payload.

        This prevents a frontend client from registering an arbitrary user_id
        that differs from the IAM-introspected principal. Anonymous frontend
        connections must not be indexed as authenticated user connections.
        """
        merged_payload = dict(payload)

        if principal.client_id is not None:
            merged_payload["client_id"] = principal.client_id

        if principal.session_id is not None:
            merged_payload["session_id"] = principal.session_id

        if principal.user_id is not None:
            merged_payload["user_id"] = principal.user_id
        else:
            # Anonymous or non-user principals must not inherit user_id from
            # untrusted frontend payload; otherwise target_type=user delivery
            # could reach an unauthenticated connection.
            merged_payload.pop("user_id", None)

        merged_payload["runtime_principal"] = principal.to_dict()
        return merged_payload

    async def _await_sub_registration_ack(self, connection: NsRuntimeConnection, register_frame: NsRuntimeWireFrame) -> None:
        """Wait for master ack after sub node runtime.register.

        P11.8-B protects runtime.forward with registered runtime_sub state. A sub
        node must therefore not start processing master frames until master has
        accepted runtime.register.
        """
        raw_message = await asyncio.wait_for(
            connection.websocket.recv(),
            timeout=float(self._config.ack_timeout_seconds),
        )
        ack_frame = NsRuntimeWireFrame.from_json(raw_message)

        if ack_frame.frame_type != RUNTIME_FRAME_ACK:
            raise NsRuntimeAuthProviderError(f"runtime sub registration expected ack, got: {ack_frame.frame_type}")

        ack = parse_ack_frame(ack_frame)
        if ack.message_id != register_frame.message_id:
            raise NsRuntimeAuthProviderError("runtime sub registration ack message_id mismatch")

        if ack.status != RUNTIME_ACK_STATUS_ACCEPTED:
            raise NsRuntimeAuthProviderError(ack.reason or "runtime sub registration rejected")

        self._mark_sub_master_connection_registered(connection)

    def _mark_sub_master_connection_registered(self, connection: NsRuntimeConnection) -> None:
        """Mark the sub node's upstream master connection as locally registered.

        The master performs real service authentication. This local principal only
        represents the accepted upstream registration result so runtime.forward
        can enforce registered connection state on the sub node side.
        """
        node_id = str(self._config.node_id or "").strip()
        connection.principal = NsRuntimePrincipal(
            principal_type=RUNTIME_PRINCIPAL_RUNTIME_NODE,
            principal_id=node_id,
            authenticated=bool(self._config.auth_enabled),
            display_name=node_id,
            node_id=node_id,
            claims={
                "runtime_sub_upstream_registered": True,
            },
        )
        registered_connection = self._registry.register_sub_node(
            connection.connection_id,
            payload={
                "node_id": node_id,
                "node_role": RUNTIME_NODE_ROLE_SUB,
            },
            remote_address=connection.remote_address,
        )
        self._upsert_presence(registered_connection)

    async def _ensure_registered_backend_connection(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame, *, health: dict[str, Any] | None = None) -> bool:
        """Return whether current connection is a registered backend connection."""
        reason = "backend connection is not registered"

        if connection.connection_type != "backend" or connection.principal is None or connection.principal.principal_type != RUNTIME_PRINCIPAL_BACKEND_SERVICE:
            await self._reject_unregistered_connection(connection, frame, reason=reason)
            return False

        backend = self._registry.refresh_backend(connection.connection_id, health=health)
        if backend is None:
            await self._reject_unregistered_connection(connection, frame, reason=reason)
            return False

        self._refresh_presence(backend)
        return True

    async def _ensure_registered_runtime_sub_connection(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame, *, health: dict[str, Any] | None = None) -> bool:
        """Return whether current connection is a registered runtime sub connection."""
        reason = "runtime sub connection is not registered"

        if connection.connection_type != "runtime_sub" or connection.principal is None or connection.principal.principal_type != RUNTIME_PRINCIPAL_RUNTIME_NODE:
            await self._reject_unregistered_connection(connection, frame, reason=reason)
            return False

        sub_node = self._registry.refresh_sub_node(connection.connection_id, health=health)
        if sub_node is None:
            await self._reject_unregistered_connection(connection, frame, reason=reason)
            return False

        self._refresh_presence(sub_node)
        return True

    async def _ensure_registered_frontend_connection(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame, *, health: dict[str, Any] | None = None) -> bool:
        """Return whether current connection is a registered frontend connection."""
        reason = "frontend connection is not registered"

        if (
                connection.connection_type != "frontend"
                or connection.principal is None
                or connection.principal.principal_type not in {
            RUNTIME_PRINCIPAL_FRONTEND_USER,
            RUNTIME_PRINCIPAL_ANONYMOUS_FRONTEND,
        }
        ):
            await self._reject_unregistered_connection(connection, frame, reason=reason)
            return False

        frontend = self._registry.refresh_frontend(connection.connection_id, health=health)
        if frontend is None:
            await self._reject_unregistered_connection(connection, frame, reason=reason)
            return False

        self._refresh_presence(frontend)
        return True

    async def _reject_unregistered_connection(self, connection: NsRuntimeConnection, frame: NsRuntimeWireFrame, *, reason: str) -> None:
        """Reject a protected frame sent by an unregistered or mismatched connection."""
        await self._send_ack(connection, frame, status=RUNTIME_ACK_STATUS_REJECTED, reason=reason)
        self._add_stats(rejected_count=1, last_error=reason)

        # Policy violation: protected frame before successful register, or frame
        # sent by a connection registered as another role. Close to reduce abuse.
        with contextlib.suppress(Exception):
            await connection.websocket.close(code=1008, reason=reason)

    def _upsert_presence(self, connection: NsRuntimeConnection) -> None:
        """Upsert local runtime presence for one registered connection."""
        self._presence.upsert_connection(connection, node_id=self._config.node_id)

    def _refresh_presence(self, connection: NsRuntimeConnection) -> None:
        """Refresh local runtime presence for one registered connection."""
        record = self._presence.refresh_connection(
            connection.connection_id,
            last_seen_epoch_ms=connection.last_seen_epoch_ms,
            health=dict(connection.health or {}),
        )
        if record is None:
            # Presence is derived state. If it is missing because of a process-local
            # reset or future backend-specific eviction, rebuild it from registry
            # connection state without interrupting the runtime frame.
            self._upsert_presence(connection)

    def _remove_presence(self, connection_id: str) -> None:
        """Remove one connection from local runtime presence."""
        self._presence.remove_connection(connection_id)

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
            frontend_register_count: int = 0,
            frontend_heartbeat_count: int = 0,
            frontend_ack_count: int = 0,
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
                frontend_register_count=self._stats.frontend_register_count + frontend_register_count,
                frontend_heartbeat_count=self._stats.frontend_heartbeat_count + frontend_heartbeat_count,
                frontend_ack_count=self._stats.frontend_ack_count + frontend_ack_count,
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
