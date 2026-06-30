# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from dataclasses import (
    dataclass,
    field,
)
from typing import (
    Any,
    Mapping,
)

from websockets.asyncio.server import (
    Server,
    ServerConnection,
    serve,
)
from websockets.exceptions import (
    ConnectionClosed,
    ConnectionClosedError,
    ConnectionClosedOK,
)

from ns_common.exceptions import (
    NsEvermoreError,
    NsRuntimeAuthError,
    NsRuntimeCodecError,
    NsRuntimeMessageError,
    NsRuntimeProtocolError,
)
from ns_common.logger import get_ns_logger
from ns_common.runtime_config import NsRuntimeConfig
from ns_runtime.iam_adapter import (
    NsRuntimeIamAccessDecision,
    NsRuntimeIamAdapter,
    NsRuntimeIamIntrospectionResult,
    get_runtime_iam_adapter,
)
from ns_runtime.processor import (
    NsRuntimeLocalProcessorRegistry,
    NsRuntimeProcessorContext,
    build_default_processor_registry,
)
from ns_runtime.protocol import (
    NsRuntimeClientType,
    NsRuntimeEnvelope,
    NsRuntimeJsonCodec,
    NsRuntimeMessageType,
    NsRuntimePeer,
    current_epoch_ms,
    new_runtime_message_id,
)


@dataclass(slots=True, kw_only=True)
class NsRuntimePendingAck:
    message_id: str
    message_type: str
    created_at_epoch_ms: int
    expires_at_epoch_ms: int
    trace_id: str | None = None
    correlation_id: str | None = None
    reply_to_message_id: str | None = None

    def is_expired(self, *, now_epoch_ms: int | None = None) -> bool:
        now_value = now_epoch_ms if now_epoch_ms is not None else current_epoch_ms()
        return now_value > self.expires_at_epoch_ms

    def to_summary(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "message_type": self.message_type,
            "created_at_epoch_ms": self.created_at_epoch_ms,
            "expires_at_epoch_ms": self.expires_at_epoch_ms,
            "trace_id": self.trace_id,
            "correlation_id": self.correlation_id,
            "reply_to_message_id": self.reply_to_message_id,
        }


@dataclass(slots=True, kw_only=True)
class NsRuntimeAckResult:
    ack_message_id: str | None
    matched: bool
    pending_ack: NsRuntimePendingAck | None = None

    def to_mapping(self) -> dict[str, Any]:
        return {
            "ack_message_id": self.ack_message_id,
            "matched": self.matched,
            "pending_ack": self.pending_ack.to_summary() if self.pending_ack else None,
        }


@dataclass(slots=True, kw_only=True)
class NsRuntimeAcceptedConnection:
    connection_id: str
    peer: NsRuntimePeer
    principal: dict[str, Any]
    introspection: NsRuntimeIamIntrospectionResult
    access_decision: NsRuntimeIamAccessDecision
    websocket: ServerConnection = field(repr=False)
    connected_at_epoch_ms: int
    last_seen_epoch_ms: int
    max_inflight: int
    backpressure_policy: str
    ack_timeout_ms: int

    remote_address: str | None = None
    request_path: str | None = None
    inflight_count: int = 0

    _inflight_lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)
    _send_lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)
    _processor_tasks: set[asyncio.Task[None]] = field(default_factory=set, repr=False)
    _pending_ack_lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False)
    _pending_acks: dict[str, NsRuntimePendingAck] = field(default_factory=dict, repr=False)

    def touch(self) -> None:
        self.last_seen_epoch_ms = current_epoch_ms()

    @property
    def client_type(self) -> str:
        return self.peer.client_type

    @property
    def client_id(self) -> str | None:
        return self.peer.client_id

    @property
    def node_id(self) -> str | None:
        return self.peer.node_id

    @property
    def node_group(self) -> str | None:
        return self.peer.node_group

    @property
    def principal_id(self) -> str | None:
        return self.peer.principal_id

    @property
    def principal_type(self) -> str | None:
        return self.peer.principal_type

    async def try_acquire_processor_slot(self) -> bool:
        async with self._inflight_lock:
            if self.inflight_count >= self.max_inflight:
                return False

            self.inflight_count += 1
            self.touch()
            return True

    async def release_processor_slot(self) -> None:
        async with self._inflight_lock:
            if self.inflight_count > 0:
                self.inflight_count -= 1

            self.touch()

    async def get_inflight_count(self) -> int:
        async with self._inflight_lock:
            return self.inflight_count

    def add_processor_task(self, task: asyncio.Task[None]) -> None:
        self._processor_tasks.add(task)

    def discard_processor_task(self, task: asyncio.Task[None] | None) -> None:
        if task is None:
            return

        self._processor_tasks.discard(task)

    async def cancel_processor_tasks(self) -> None:
        tasks = list(self._processor_tasks)
        self._processor_tasks.clear()

        for task in tasks:
            if not task.done():
                task.cancel()

        if tasks:
            await asyncio.gather(
                *tasks,
                return_exceptions=True,
            )

    async def register_pending_ack(self, envelope: NsRuntimeEnvelope) -> NsRuntimePendingAck | None:
        if not envelope.requires_ack:
            return None

        now_epoch_ms = current_epoch_ms()
        pending_ack = NsRuntimePendingAck(
            message_id=envelope.message_id,
            message_type=envelope.message_type,
            created_at_epoch_ms=now_epoch_ms,
            expires_at_epoch_ms=now_epoch_ms + self.ack_timeout_ms,
            trace_id=envelope.trace_id,
            correlation_id=envelope.correlation_id,
            reply_to_message_id=envelope.reply_to_message_id,
        )

        async with self._pending_ack_lock:
            self._pending_acks[pending_ack.message_id] = pending_ack

        return pending_ack

    async def forget_pending_ack(self, message_id: str | None) -> NsRuntimePendingAck | None:
        if not message_id:
            return None

        async with self._pending_ack_lock:
            return self._pending_acks.pop(message_id, None)

    async def acknowledge(self, ack_envelope: NsRuntimeEnvelope) -> NsRuntimeAckResult:
        payload = dict(ack_envelope.payload or {})
        ack_message_id = _normalize_optional_text(
            payload.get("ack_message_id")
            or payload.get("message_id")
            or ack_envelope.reply_to_message_id
        )

        if not ack_message_id:
            return NsRuntimeAckResult(
                ack_message_id=None,
                matched=False,
            )

        pending_ack = await self.forget_pending_ack(ack_message_id)

        return NsRuntimeAckResult(
            ack_message_id=ack_message_id,
            matched=pending_ack is not None,
            pending_ack=pending_ack,
        )

    async def prune_expired_pending_acks(self) -> list[NsRuntimePendingAck]:
        now_epoch_ms = current_epoch_ms()

        async with self._pending_ack_lock:
            expired = [
                item
                for item in self._pending_acks.values()
                if item.is_expired(now_epoch_ms=now_epoch_ms)
            ]

            for item in expired:
                self._pending_acks.pop(item.message_id, None)

            return expired

    async def clear_pending_acks(self) -> list[NsRuntimePendingAck]:
        async with self._pending_ack_lock:
            pending = list(self._pending_acks.values())
            self._pending_acks.clear()
            return pending

    async def get_pending_ack_count(self) -> int:
        async with self._pending_ack_lock:
            return len(self._pending_acks)

    async def pending_ack_snapshot(self) -> list[dict[str, Any]]:
        async with self._pending_ack_lock:
            return [
                item.to_summary()
                for item in sorted(
                    self._pending_acks.values(),
                    key=lambda pending: pending.created_at_epoch_ms,
                )
            ]

    async def send_envelope(
            self,
            envelope: NsRuntimeEnvelope,
            *,
            track_ack: bool = True,
    ) -> None:
        pending_ack: NsRuntimePendingAck | None = None

        if track_ack and envelope.requires_ack:
            pending_ack = await self.register_pending_ack(envelope)

        try:
            async with self._send_lock:
                await self.websocket.send(NsRuntimeJsonCodec.encode(envelope))
        except Exception:
            if pending_ack is not None:
                await self.forget_pending_ack(pending_ack.message_id)
            raise

    def to_summary(self) -> dict[str, Any]:
        return {
            "connection_id": self.connection_id,
            "client_type": self.client_type,
            "client_id": self.client_id,
            "node_id": self.node_id,
            "node_group": self.node_group,
            "principal_id": self.principal_id,
            "principal_type": self.principal_type,
            "connected_at_epoch_ms": self.connected_at_epoch_ms,
            "last_seen_epoch_ms": self.last_seen_epoch_ms,
            "remote_address": self.remote_address,
            "request_path": self.request_path,
            "max_inflight": self.max_inflight,
            "inflight_count": self.inflight_count,
            "backpressure_policy": self.backpressure_policy,
            "ack_timeout_ms": self.ack_timeout_ms,
            "pending_ack_count": len(self._pending_acks),
        }


class NsRuntimeConnectionRegistry:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._connections: dict[str, NsRuntimeAcceptedConnection] = {}
        self._client_id_index: dict[str, set[str]] = {}
        self._node_id_index: dict[str, set[str]] = {}
        self._principal_id_index: dict[str, set[str]] = {}

    async def register(self, connection: NsRuntimeAcceptedConnection) -> None:
        async with self._lock:
            old_connection = self._connections.get(connection.connection_id)
            if old_connection is not None:
                self._remove_indexes(old_connection)

            self._connections[connection.connection_id] = connection
            self._add_indexes(connection)

    async def unregister(self, connection_id: str) -> NsRuntimeAcceptedConnection | None:
        async with self._lock:
            connection = self._connections.pop(connection_id, None)
            if connection is not None:
                self._remove_indexes(connection)

            return connection

    async def touch(self, connection_id: str) -> bool:
        async with self._lock:
            connection = self._connections.get(connection_id)
            if connection is None:
                return False

            connection.touch()
            return True

    async def get_by_connection_id(self, connection_id: str) -> NsRuntimeAcceptedConnection | None:
        async with self._lock:
            return self._connections.get(connection_id)

    async def list_by_client_id(self, client_id: str) -> list[NsRuntimeAcceptedConnection]:
        return await self._list_by_index(self._client_id_index, client_id)

    async def list_by_node_id(self, node_id: str) -> list[NsRuntimeAcceptedConnection]:
        return await self._list_by_index(self._node_id_index, node_id)

    async def list_by_principal_id(self, principal_id: str) -> list[NsRuntimeAcceptedConnection]:
        return await self._list_by_index(self._principal_id_index, principal_id)

    async def list_all(self) -> list[NsRuntimeAcceptedConnection]:
        async with self._lock:
            return list(self._connections.values())

    async def count(self) -> int:
        async with self._lock:
            return len(self._connections)

    async def snapshot(self) -> dict[str, Any]:
        async with self._lock:
            connections = list(self._connections.values())

            return {
                "total": len(connections),
                "by_client_id": {
                    key: sorted(value)
                    for key, value in self._client_id_index.items()
                },
                "by_node_id": {
                    key: sorted(value)
                    for key, value in self._node_id_index.items()
                },
                "by_principal_id": {
                    key: sorted(value)
                    for key, value in self._principal_id_index.items()
                },
                "connections": [
                    connection.to_summary()
                    for connection in connections
                ],
            }

    async def close_all(self, *, code: int = 1001, reason: str = "runtime server stopping") -> None:
        connections = await self.list_all()

        for connection in connections:
            await connection.cancel_processor_tasks()
            await connection.clear_pending_acks()

            try:
                await connection.websocket.close(
                    code=code,
                    reason=reason[:120],
                )
            except Exception:  # noqa
                pass

    async def _list_by_index(self, index: dict[str, set[str]], value: str) -> list[NsRuntimeAcceptedConnection]:
        normalized = _normalize_optional_text(value)
        if not normalized:
            return []

        async with self._lock:
            connection_ids = set(index.get(normalized, set()))
            result: list[NsRuntimeAcceptedConnection] = []

            for connection_id in connection_ids:
                connection = self._connections.get(connection_id)
                if connection is not None:
                    result.append(connection)

            return result

    def _add_indexes(self, connection: NsRuntimeAcceptedConnection) -> None:
        self._add_index(self._client_id_index, connection.client_id, connection.connection_id)
        self._add_index(self._node_id_index, connection.node_id, connection.connection_id)
        self._add_index(self._principal_id_index, connection.principal_id, connection.connection_id)

    def _remove_indexes(self, connection: NsRuntimeAcceptedConnection) -> None:
        self._remove_index(self._client_id_index, connection.client_id, connection.connection_id)
        self._remove_index(self._node_id_index, connection.node_id, connection.connection_id)
        self._remove_index(self._principal_id_index, connection.principal_id, connection.connection_id)

    @staticmethod
    def _add_index(index: dict[str, set[str]], value: str | None, connection_id: str) -> None:
        if not value:
            return

        index.setdefault(value, set()).add(connection_id)

    @staticmethod
    def _remove_index(index: dict[str, set[str]], value: str | None, connection_id: str) -> None:
        if not value:
            return

        bucket = index.get(value)
        if bucket is None:
            return

        bucket.discard(connection_id)

        if not bucket:
            index.pop(value, None)


class NsRuntimeWebSocketServer:
    CONNECTION_HELLO_TIMEOUT_SECONDS = 10.0
    DEFAULT_ACK_TIMEOUT_MS = 30_000

    def __init__(
            self,
            *,
            runtime_config: NsRuntimeConfig,
            iam_adapter: NsRuntimeIamAdapter | None = None,
            connection_registry: NsRuntimeConnectionRegistry | None = None,
            processor_registry: NsRuntimeLocalProcessorRegistry | None = None,
    ) -> None:
        self.runtime_config: NsRuntimeConfig = runtime_config
        self.ws_config = runtime_config.server.websocket
        self.iam_adapter: NsRuntimeIamAdapter = iam_adapter or get_runtime_iam_adapter(runtime_config)
        self.connection_registry: NsRuntimeConnectionRegistry = connection_registry or NsRuntimeConnectionRegistry()
        self.processor_registry: NsRuntimeLocalProcessorRegistry = processor_registry or build_default_processor_registry(runtime_config)
        self.logger = get_ns_logger("ns_runtime.ws_server")
        self._server: Server | None = None
        self._started: bool = False

    async def start(self) -> None:
        if self._started:
            return

        self.runtime_config.validate()

        self._server = await serve(
            self._process_connection,
            self.ws_config.host,
            self.ws_config.port,
            ping_interval=self.ws_config.ping_interval_seconds,
            ping_timeout=self.ws_config.ping_timeout_seconds,
            max_size=self.ws_config.max_message_size_bytes,
        )

        self._started = True

        self.logger.info(
            "Runtime WebSocket server started.",
            extra={
                "runtime_id": self.runtime_config.runtime_id,
                "cluster_id": self.runtime_config.cluster_id,
                "mode": self.runtime_config.mode,
                "host": self.ws_config.host,
                "port": self.ws_config.port,
                "path": self.ws_config.path,
                "ping_interval_seconds": self.ws_config.ping_interval_seconds,
                "ping_timeout_seconds": self.ws_config.ping_timeout_seconds,
                "max_message_size_bytes": self.ws_config.max_message_size_bytes,
                "processors": self.processor_registry.list_processors(),
                "default_connection_max_inflight": self.runtime_config.default_connection_max_inflight,
                "default_backpressure_policy": self.runtime_config.default_backpressure_policy,
                "default_processor_timeout_ms": self.runtime_config.default_processor_timeout_ms,
                "default_ack_timeout_ms": self.DEFAULT_ACK_TIMEOUT_MS,
            },
        )

    async def stop(self, *, reason: str = "normal") -> None:
        if not self._started:
            return

        server = self._server
        self._server = None
        self._started = False

        await self.connection_registry.close_all(
            code=1001,
            reason=reason,
        )

        if server is not None:
            server.close()
            await server.wait_closed()

        snapshot = await self.connection_registry.snapshot()

        self.logger.info(
            "Runtime WebSocket server stopped.",
            extra={
                "runtime_id": self.runtime_config.runtime_id,
                "cluster_id": self.runtime_config.cluster_id,
                "mode": self.runtime_config.mode,
                "reason": reason,
                "connection_total": snapshot["total"],
            },
        )

    async def _process_connection(self, websocket: ServerConnection) -> None:
        connection_id = self._resolve_connection_id(websocket)
        remote_address = str(getattr(websocket, "remote_address", "") or "")
        request_path = self._resolve_request_path(websocket)

        accepted: NsRuntimeAcceptedConnection | None = None

        try:
            if not self._is_expected_path(websocket):
                await self._reject_and_close(
                    websocket,
                    connection_id=connection_id,
                    reason="INVALID_WEBSOCKET_PATH",
                    details={
                        "expected_path": self.ws_config.path,
                        "actual_path": request_path,
                    },
                )
                return

            hello_raw = await asyncio.wait_for(
                websocket.recv(),
                timeout=self.CONNECTION_HELLO_TIMEOUT_SECONDS,
            )
            hello = NsRuntimeJsonCodec.decode(hello_raw)

            accepted = await self._accept_connection(
                websocket,
                hello,
                connection_id=connection_id,
                remote_address=remote_address,
                request_path=request_path,
            )
            await self.connection_registry.register(accepted)

            self.logger.info(
                "Runtime WebSocket connection accepted.",
                extra={
                    "runtime_id": self.runtime_config.runtime_id,
                    "connection_id": accepted.connection_id,
                    "client_type": accepted.peer.client_type,
                    "client_id": accepted.peer.client_id,
                    "node_id": accepted.peer.node_id,
                    "node_group": accepted.peer.node_group,
                    "principal_type": accepted.peer.principal_type,
                    "principal_id": accepted.peer.principal_id,
                    "remote_address": remote_address,
                    "active_connection_count": await self.connection_registry.count(),
                    "max_inflight": accepted.max_inflight,
                    "backpressure_policy": accepted.backpressure_policy,
                    "ack_timeout_ms": accepted.ack_timeout_ms,
                },
            )

            async for raw_message in websocket:
                await self.connection_registry.touch(accepted.connection_id)
                await self._process_runtime_message(
                    raw_message,
                    connection=accepted,
                )

        except asyncio.TimeoutError:
            await self._reject_and_close(
                websocket,
                connection_id=connection_id,
                reason="CONNECTION_HELLO_TIMEOUT",
                details={
                    "timeout_seconds": self.CONNECTION_HELLO_TIMEOUT_SECONDS,
                },
            )
        except (
                NsRuntimeAuthError,
                NsRuntimeCodecError,
                NsRuntimeProtocolError,
        ) as exc:
            if accepted is None:
                await self._reject_and_close(
                    websocket,
                    connection_id=connection_id,
                    reason=exc.code,
                    details=exc.to_dict(),
                )
            else:
                await self._send_error_response(
                    connection=accepted,
                    code=exc.code,
                    message=exc.message,
                    numeric_code=exc.numeric_code,
                    details=exc.details,
                )
        except ConnectionClosedOK:
            pass
        except ConnectionClosedError as exc:
            self.logger.warning(
                "Runtime WebSocket connection closed with error.",
                extra={
                    "runtime_id": self.runtime_config.runtime_id,
                    "connection_id": connection_id,
                    "code": getattr(exc, "code", None),
                    "reason": getattr(exc, "reason", None),
                },
            )
        except ConnectionClosed:
            pass
        except Exception as exc:  # noqa
            self.logger.exception(
                "Runtime WebSocket connection failed unexpectedly.",
                extra={
                    "runtime_id": self.runtime_config.runtime_id,
                    "connection_id": connection_id,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
            try:
                await self._reject_and_close(
                    websocket,
                    connection_id=connection_id,
                    reason="RUNTIME_CONNECTION_ERROR",
                    details={
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    },
                )
            except Exception:  # noqa
                pass
        finally:
            if accepted is not None:
                await accepted.cancel_processor_tasks()
                pending_acks = await accepted.clear_pending_acks()
                await self.connection_registry.unregister(accepted.connection_id)

                self.logger.info(
                    "Runtime WebSocket connection released.",
                    extra={
                        "runtime_id": self.runtime_config.runtime_id,
                        "connection_id": accepted.connection_id,
                        "client_type": accepted.peer.client_type,
                        "client_id": accepted.peer.client_id,
                        "node_id": accepted.peer.node_id,
                        "node_group": accepted.peer.node_group,
                        "active_connection_count": await self.connection_registry.count(),
                        "cleared_pending_ack_count": len(pending_acks),
                    },
                )

    async def _accept_connection(
            self,
            websocket: ServerConnection,
            hello: NsRuntimeEnvelope,
            *,
            connection_id: str,
            remote_address: str | None,
            request_path: str | None,
    ) -> NsRuntimeAcceptedConnection:
        if hello.message_type != NsRuntimeMessageType.CONNECTION_HELLO:
            raise NsRuntimeProtocolError(
                "First runtime WebSocket message must be connection.hello.",
                details={
                    "connection_id": connection_id,
                    "actual_message_type": hello.message_type,
                    "expected_message_type": NsRuntimeMessageType.CONNECTION_HELLO,
                },
            )

        payload = dict(hello.payload or {})

        access_token = _normalize_required_text(
            payload.get("access_token") or payload.get("token"),
            "payload.access_token",
        )
        token_type = _normalize_optional_text(payload.get("token_type")) or "access"
        client_type = _normalize_required_text(payload.get("client_type"), "payload.client_type")
        client_id = _normalize_optional_text(payload.get("client_id"))
        session_id = _normalize_optional_text(payload.get("session_id"))
        node_id = _normalize_optional_text(payload.get("node_id"))
        node_group = _normalize_optional_text(payload.get("node_group"))

        introspection = await self.iam_adapter.introspect_token(
            access_token,
            token_type=token_type,
            client_id=client_id,
            session_id=session_id,
            trace_id=hello.trace_id,
        )

        if not introspection.active or not introspection.principal:
            await self._reject_and_close(
                websocket,
                connection_id=connection_id,
                reason=introspection.reason,
                trace_id=hello.trace_id,
                details={
                    "active": introspection.active,
                    "reason": introspection.reason,
                },
            )
            raise NsRuntimeAuthError(
                "Runtime WebSocket connection token is not active.",
                details={
                    "connection_id": connection_id,
                    "reason": introspection.reason,
                },
            )

        principal = dict(introspection.principal)

        access_decision = await self.iam_adapter.check_connection_access(
            principal=principal,
            client_type=client_type,
            client_id=client_id,
            node_id=node_id,
            node_group=node_group,
            trace_id=hello.trace_id,
            extra_context={
                "connection_id": connection_id,
                "remote_address": str(remote_address or ""),
            },
        )

        if not access_decision.allowed:
            await self._reject_and_close(
                websocket,
                connection_id=connection_id,
                reason=access_decision.reason or "CONNECTION_ACCESS_DENIED",
                trace_id=hello.trace_id,
                details={
                    "effect": access_decision.effect,
                    "reason": access_decision.reason,
                    "resource_type": access_decision.resource_type,
                    "resource_id": access_decision.resource_id,
                    "action_code": access_decision.action_code,
                    "decision_chain": access_decision.decision_chain,
                },
            )
            raise NsRuntimeAuthError(
                "Runtime WebSocket connection access denied.",
                details={
                    "connection_id": connection_id,
                    "effect": access_decision.effect,
                    "reason": access_decision.reason,
                    "resource_type": access_decision.resource_type,
                    "resource_id": access_decision.resource_id,
                    "action_code": access_decision.action_code,
                },
            )

        peer = NsRuntimePeer(
            client_type=client_type,
            client_id=client_id,
            runtime_id=self.runtime_config.runtime_id,
            node_id=node_id,
            node_group=node_group,
            principal_id=_normalize_optional_text(principal.get("principal_id")),
            principal_type=_normalize_optional_text(principal.get("principal_type")),
        )
        peer.validate("peer")

        now_epoch_ms = current_epoch_ms()
        accepted = NsRuntimeAcceptedConnection(
            connection_id=connection_id,
            peer=peer,
            principal=principal,
            introspection=introspection,
            access_decision=access_decision,
            websocket=websocket,
            connected_at_epoch_ms=now_epoch_ms,
            last_seen_epoch_ms=now_epoch_ms,
            max_inflight=self.runtime_config.default_connection_max_inflight,
            backpressure_policy=self.runtime_config.default_backpressure_policy,
            ack_timeout_ms=self.DEFAULT_ACK_TIMEOUT_MS,
            remote_address=remote_address,
            request_path=request_path,
        )

        response = NsRuntimeEnvelope.new(
            message_type=NsRuntimeMessageType.CONNECTION_ACCEPTED,
            source=self._build_runtime_peer(),
            target=peer,
            trace_id=hello.trace_id,
            correlation_id=hello.correlation_id or hello.message_id,
            reply_to_message_id=hello.message_id,
            payload={
                "connection_id": connection_id,
                "runtime_id": self.runtime_config.runtime_id,
                "cluster_id": self.runtime_config.cluster_id,
                "mode": self.runtime_config.mode,
                "server_time_epoch_ms": current_epoch_ms(),
                "principal": principal,
                "access_decision": access_decision.raw,
                "max_inflight": accepted.max_inflight,
                "backpressure_policy": accepted.backpressure_policy,
                "ack_timeout_ms": accepted.ack_timeout_ms,
            },
        )

        await accepted.send_envelope(response)
        return accepted

    async def _process_runtime_message(
            self,
            raw_message: str | bytes,
            *,
            connection: NsRuntimeAcceptedConnection,
    ) -> None:
        envelope = NsRuntimeJsonCodec.decode(raw_message)

        if envelope.is_expired():
            await self._send_error_response(
                connection=connection,
                code="RUNTIME_MESSAGE_EXPIRED",
                message="Runtime message is expired.",
                details={
                    "message_id": envelope.message_id,
                    "message_type": envelope.message_type,
                    "ttl_ms": envelope.ttl_ms,
                    "timestamp_epoch_ms": envelope.timestamp_epoch_ms,
                },
                reply_to=envelope,
            )
            return

        if envelope.message_type == NsRuntimeMessageType.ACK:
            await self._process_ack(
                envelope,
                connection=connection,
            )
            return

        if envelope.requires_ack:
            await self._send_inbound_ack(
                envelope,
                connection=connection,
            )

        expired_pending_acks = await connection.prune_expired_pending_acks()
        if expired_pending_acks:
            self.logger.warning(
                "Runtime pending ACK entries expired.",
                extra={
                    "runtime_id": self.runtime_config.runtime_id,
                    "connection_id": connection.connection_id,
                    "expired_pending_ack_count": len(expired_pending_acks),
                    "expired_pending_acks": [
                        item.to_summary()
                        for item in expired_pending_acks
                    ],
                },
            )

        if envelope.message_type == NsRuntimeMessageType.HEARTBEAT_PING:
            pong = NsRuntimeEnvelope.new(
                message_type=NsRuntimeMessageType.HEARTBEAT_PONG,
                source=self._build_runtime_peer(),
                target=connection.peer,
                trace_id=envelope.trace_id,
                correlation_id=envelope.correlation_id or envelope.message_id,
                reply_to_message_id=envelope.message_id,
                payload={
                    "connection_id": connection.connection_id,
                    "server_time_epoch_ms": current_epoch_ms(),
                    "echo": envelope.payload,
                    "inflight_count": await connection.get_inflight_count(),
                    "max_inflight": connection.max_inflight,
                    "pending_ack_count": await connection.get_pending_ack_count(),
                },
            )
            await connection.send_envelope(pong)
            return

        if envelope.message_type == NsRuntimeMessageType.PROCESSOR_REQUEST:
            await self._schedule_processor_request(
                envelope,
                connection=connection,
            )
            return

        await self._send_error_response(
            connection=connection,
            code=NsRuntimeMessageError.code,
            message="Runtime message type is not supported in local WebSocket server.",
            numeric_code=NsRuntimeMessageError.numeric_code,
            details={
                "message_id": envelope.message_id,
                "message_type": envelope.message_type,
                "phase": "1.9",
            },
            reply_to=envelope,
        )

    async def _process_ack(
            self,
            envelope: NsRuntimeEnvelope,
            *,
            connection: NsRuntimeAcceptedConnection,
    ) -> None:
        ack_result = await connection.acknowledge(envelope)

        if ack_result.matched:
            self.logger.debug(
                "Runtime pending ACK matched.",
                extra={
                    "runtime_id": self.runtime_config.runtime_id,
                    "connection_id": connection.connection_id,
                    **ack_result.to_mapping(),
                },
            )
            return

        self.logger.warning(
            "Runtime ACK received without matching pending message.",
            extra={
                "runtime_id": self.runtime_config.runtime_id,
                "connection_id": connection.connection_id,
                "ack_message_id": ack_result.ack_message_id,
                "ack_payload": envelope.payload,
                "reply_to_message_id": envelope.reply_to_message_id,
            },
        )

    async def _send_inbound_ack(
            self,
            envelope: NsRuntimeEnvelope,
            *,
            connection: NsRuntimeAcceptedConnection,
    ) -> None:
        ack = envelope.build_ack(
            source=self._build_runtime_peer(),
            metadata={
                "connection_id": connection.connection_id,
                "acknowledged_at_epoch_ms": current_epoch_ms(),
            },
        )
        await connection.send_envelope(
            ack,
            track_ack=False,
        )

    async def _schedule_processor_request(
            self,
            envelope: NsRuntimeEnvelope,
            *,
            connection: NsRuntimeAcceptedConnection,
    ) -> None:
        acquired = await connection.try_acquire_processor_slot()
        if not acquired:
            await self._send_error_response(
                connection=connection,
                code="RUNTIME_BACKPRESSURE_REJECTED",
                message="Runtime connection inflight limit exceeded.",
                numeric_code=NsRuntimeMessageError.numeric_code,
                details={
                    "message_id": envelope.message_id,
                    "message_type": envelope.message_type,
                    "connection_id": connection.connection_id,
                    "inflight_count": await connection.get_inflight_count(),
                    "max_inflight": connection.max_inflight,
                    "configured_backpressure_policy": connection.backpressure_policy,
                    "applied_backpressure_policy": "reject",
                    "reason": "QUEUE_POLICY_NOT_IMPLEMENTED_IN_PHASE_1_9",
                },
                reply_to=envelope,
            )
            return

        task = asyncio.create_task(
            self._run_processor_request_task(
                envelope,
                connection=connection,
            )
        )
        connection.add_processor_task(task)

        self.logger.debug(
            "Runtime processor request scheduled.",
            extra={
                "runtime_id": self.runtime_config.runtime_id,
                "connection_id": connection.connection_id,
                "message_id": envelope.message_id,
                "message_type": envelope.message_type,
                "inflight_count": await connection.get_inflight_count(),
                "max_inflight": connection.max_inflight,
            },
        )

    async def _run_processor_request_task(
            self,
            envelope: NsRuntimeEnvelope,
            *,
            connection: NsRuntimeAcceptedConnection,
    ) -> None:
        task = asyncio.current_task()

        try:
            await self._process_processor_request(
                envelope,
                connection=connection,
            )
        except ConnectionClosed:
            pass
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa
            self.logger.exception(
                "Runtime processor request task failed unexpectedly.",
                extra={
                    "runtime_id": self.runtime_config.runtime_id,
                    "connection_id": connection.connection_id,
                    "message_id": envelope.message_id,
                    "message_type": envelope.message_type,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            )
            try:
                await self._send_error_response(
                    connection=connection,
                    code="RUNTIME_PROCESSOR_TASK_ERROR",
                    message="Runtime processor task failed unexpectedly.",
                    details={
                        "message_id": envelope.message_id,
                        "message_type": envelope.message_type,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    },
                    reply_to=envelope,
                )
            except Exception:  # noqa
                pass
        finally:
            await connection.release_processor_slot()
            connection.discard_processor_task(task)

    async def _process_processor_request(
            self,
            envelope: NsRuntimeEnvelope,
            *,
            connection: NsRuntimeAcceptedConnection,
    ) -> None:
        context = NsRuntimeProcessorContext(
            runtime_config=self.runtime_config,
            connection_id=connection.connection_id,
            peer=connection.peer,
            principal=dict(connection.principal),
            request=envelope,
            connection_summary=connection.to_summary(),
        )

        timeout_ms = self.runtime_config.default_processor_timeout_ms
        timeout_seconds = timeout_ms / 1000.0

        try:
            result = await asyncio.wait_for(
                self.processor_registry.dispatch(context),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            processor_name = self._resolve_processor_name_for_error(envelope)

            self.logger.warning(
                "Runtime processor request timed out.",
                extra={
                    "runtime_id": self.runtime_config.runtime_id,
                    "connection_id": connection.connection_id,
                    "message_id": envelope.message_id,
                    "message_type": envelope.message_type,
                    "processor_name": processor_name,
                    "timeout_ms": timeout_ms,
                    "trace_id": envelope.trace_id,
                },
            )

            await self._send_error_response(
                connection=connection,
                code="RUNTIME_PROCESSOR_TIMEOUT",
                message="Runtime processor execution timed out.",
                details={
                    "message_id": envelope.message_id,
                    "message_type": envelope.message_type,
                    "processor_name": processor_name,
                    "timeout_ms": timeout_ms,
                    "trace_id": envelope.trace_id,
                },
                reply_to=envelope,
            )
            return
        except NsEvermoreError as exc:
            await self._send_error_response(
                connection=connection,
                code=exc.code,
                message=exc.message,
                numeric_code=exc.numeric_code,
                details=exc.details,
                reply_to=envelope,
            )
            return
        except Exception as exc:  # noqa
            await self._send_error_response(
                connection=connection,
                code="RUNTIME_PROCESSOR_ERROR",
                message="Runtime processor failed unexpectedly.",
                details={
                    "message_id": envelope.message_id,
                    "message_type": envelope.message_type,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                reply_to=envelope,
            )
            return

        response_requires_ack = _resolve_response_requires_ack(envelope)

        response = NsRuntimeEnvelope.new(
            message_type=NsRuntimeMessageType.PROCESSOR_RESPONSE,
            source=self._build_runtime_peer(),
            target=connection.peer,
            trace_id=envelope.trace_id,
            correlation_id=envelope.correlation_id or envelope.message_id,
            reply_to_message_id=envelope.message_id,
            payload=result.payload,
            metadata=result.metadata,
            requires_ack=response_requires_ack,
        )
        await connection.send_envelope(response)

    def _resolve_processor_name_for_error(self, envelope: NsRuntimeEnvelope) -> str | None:
        try:
            return self.processor_registry.resolve_processor_name(envelope)
        except Exception:  # noqa
            return None

    async def send_to_connection(
            self,
            connection_id: str,
            envelope: NsRuntimeEnvelope,
    ) -> bool:
        connection = await self.connection_registry.get_by_connection_id(connection_id)
        if connection is None:
            return False

        await connection.send_envelope(envelope)
        await self.connection_registry.touch(connection_id)
        return True

    async def _send_error_response(
            self,
            *,
            connection: NsRuntimeAcceptedConnection,
            code: str,
            message: str,
            numeric_code: int | None = None,
            details: Mapping[str, Any] | None = None,
            reply_to: NsRuntimeEnvelope | None = None,
    ) -> None:
        envelope = NsRuntimeEnvelope.new(
            message_type=NsRuntimeMessageType.PROCESSOR_ERROR,
            source=self._build_runtime_peer(),
            target=connection.peer,
            trace_id=reply_to.trace_id if reply_to else None,
            correlation_id=(reply_to.correlation_id or reply_to.message_id) if reply_to else None,
            reply_to_message_id=reply_to.message_id if reply_to else None,
            payload={
                "code": code,
                "numeric_code": numeric_code,
                "message": message,
                "details": dict(details or {}),
            },
        )
        await connection.send_envelope(envelope)

    async def _reject_and_close(
            self,
            websocket: ServerConnection,
            *,
            connection_id: str,
            reason: str,
            trace_id: str | None = None,
            details: Mapping[str, Any] | None = None,
    ) -> None:
        envelope = NsRuntimeEnvelope.new(
            message_type=NsRuntimeMessageType.CONNECTION_REJECTED,
            source=self._build_runtime_peer(),
            trace_id=trace_id,
            payload={
                "connection_id": connection_id,
                "reason": reason,
                "details": dict(details or {}),
                "server_time_epoch_ms": current_epoch_ms(),
            },
        )

        try:
            await websocket.send(NsRuntimeJsonCodec.encode(envelope))
        except Exception:  # noqa
            pass

        try:
            await websocket.close(
                code=1008,
                reason=reason[:120],
            )
        except Exception:  # noqa
            pass

    def _is_expected_path(self, websocket: ServerConnection) -> bool:
        actual_path = self._resolve_request_path(websocket)
        if actual_path is None:
            return True

        return actual_path == self.ws_config.path

    @staticmethod
    def _resolve_request_path(websocket: ServerConnection) -> str | None:
        request = getattr(websocket, "request", None)
        path = getattr(request, "path", None)

        if path is None:
            return None

        path_text = str(path).strip()
        if not path_text:
            return None

        return path_text.split("?", 1)[0]

    @staticmethod
    def _resolve_connection_id(websocket: ServerConnection) -> str:
        connection_id = getattr(websocket, "id", None)
        if connection_id is not None:
            text = str(connection_id).strip()
            if text:
                return text

        return new_runtime_message_id()

    def _build_runtime_peer(self) -> NsRuntimePeer:
        return NsRuntimePeer(
            client_type=NsRuntimeClientType.NS_NODE,
            runtime_id=self.runtime_config.runtime_id,
            node_group=self.runtime_config.cluster_id,
        )


def _normalize_required_text(value: Any, field_name: str) -> str:
    normalized = str(value or "").strip()

    if not normalized:
        raise NsRuntimeProtocolError(
            f"{field_name} is required.",
            details={
                "field": field_name,
            },
        )

    return normalized


def _normalize_optional_text(value: Any) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()
    return normalized or None


def _resolve_response_requires_ack(envelope: NsRuntimeEnvelope) -> bool:
    payload = dict(envelope.payload or {})
    metadata = dict(envelope.metadata or {})

    value = (
        payload.get("response_requires_ack")
        if "response_requires_ack" in payload
        else metadata.get("response_requires_ack")
    )

    return value is True
