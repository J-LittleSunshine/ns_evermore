# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from dataclasses import dataclass
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
    NsRuntimeAuthError,
    NsRuntimeCodecError,
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
class NsRuntimeAcceptedConnection:
    connection_id: str
    peer: NsRuntimePeer
    principal: dict[str, Any]
    introspection: NsRuntimeIamIntrospectionResult
    access_decision: NsRuntimeIamAccessDecision


class NsRuntimeWebSocketServer:
    CONNECTION_HELLO_TIMEOUT_SECONDS = 10.0

    def __init__(
            self,
            *,
            runtime_config: NsRuntimeConfig,
            iam_adapter: NsRuntimeIamAdapter | None = None,
    ) -> None:
        self.runtime_config: NsRuntimeConfig = runtime_config
        self.ws_config = runtime_config.server.websocket
        self.iam_adapter: NsRuntimeIamAdapter = iam_adapter or get_runtime_iam_adapter(runtime_config)
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
            },
        )

    async def stop(self, *, reason: str = "normal") -> None:
        if not self._started:
            return

        server = self._server
        self._server = None
        self._started = False

        if server is not None:
            server.close()
            await server.wait_closed()

        self.logger.info(
            "Runtime WebSocket server stopped.",
            extra={
                "runtime_id": self.runtime_config.runtime_id,
                "cluster_id": self.runtime_config.cluster_id,
                "mode": self.runtime_config.mode,
                "reason": reason,
            },
        )

    async def _process_connection(self, websocket: ServerConnection) -> None:
        connection_id = self._resolve_connection_id(websocket)
        remote_address = str(getattr(websocket, "remote_address", "") or "")

        accepted: NsRuntimeAcceptedConnection | None = None

        try:
            if not self._is_expected_path(websocket):
                await self._reject_and_close(
                    websocket,
                    connection_id=connection_id,
                    reason="INVALID_WEBSOCKET_PATH",
                    details={
                        "expected_path": self.ws_config.path,
                        "actual_path": self._resolve_request_path(websocket),
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
            )

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
                },
            )

            async for raw_message in websocket:
                await self._process_runtime_message(
                    websocket,
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
                    websocket,
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
                self.logger.info(
                    "Runtime WebSocket connection released.",
                    extra={
                        "runtime_id": self.runtime_config.runtime_id,
                        "connection_id": accepted.connection_id,
                        "client_type": accepted.peer.client_type,
                        "client_id": accepted.peer.client_id,
                        "node_id": accepted.peer.node_id,
                        "node_group": accepted.peer.node_group,
                    },
                )

    async def _accept_connection(
            self,
            websocket: ServerConnection,
            hello: NsRuntimeEnvelope,
            *,
            connection_id: str,
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
                "remote_address": str(getattr(websocket, "remote_address", "") or ""),
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

        accepted = NsRuntimeAcceptedConnection(
            connection_id=connection_id,
            peer=peer,
            principal=principal,
            introspection=introspection,
            access_decision=access_decision,
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
            },
        )

        await websocket.send(NsRuntimeJsonCodec.encode(response))
        return accepted

    async def _process_runtime_message(
            self,
            websocket: ServerConnection,
            raw_message: str | bytes,
            *,
            connection: NsRuntimeAcceptedConnection,
    ) -> None:
        envelope = NsRuntimeJsonCodec.decode(raw_message)

        if envelope.is_expired():
            await self._send_error_response(
                websocket,
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
                },
            )
            await websocket.send(NsRuntimeJsonCodec.encode(pong))
            return

        if envelope.message_type == NsRuntimeMessageType.ACK:
            self.logger.debug(
                "Runtime WebSocket ACK received.",
                extra={
                    "runtime_id": self.runtime_config.runtime_id,
                    "connection_id": connection.connection_id,
                    "message_id": envelope.message_id,
                    "payload": envelope.payload,
                },
            )
            return

        await self._send_error_response(
            websocket,
            connection=connection,
            code="RUNTIME_PROCESSOR_NOT_IMPLEMENTED",
            message="Runtime processors are not implemented in this phase.",
            details={
                "message_id": envelope.message_id,
                "message_type": envelope.message_type,
                "phase": "1.5",
            },
            reply_to=envelope,
        )

    async def _send_error_response(
            self,
            websocket: ServerConnection,
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
        await websocket.send(NsRuntimeJsonCodec.encode(envelope))

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
