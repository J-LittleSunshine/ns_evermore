# -*- coding: utf-8 -*-
"""WebSocket over TCP adapter declarations.

The third-party WebSocket implementation is imported lazily by the operational
adapter path added in P04-W03. Importing this module only exposes frozen runtime
contracts and cannot open a listener.
"""

from __future__ import annotations

import asyncio
import ssl
from dataclasses import dataclass, field
from typing import Any

from ns_common.exceptions import (
    NsRuntimeTransportHandshakeFailedError,
    NsRuntimeTransportReceiveFailedError,
    NsRuntimeTransportSendFailedError,
    NsRuntimeTransportStreamResetError,
    NsRuntimeStartupSecurityError,
    NsStateError,
    NsValidationError,
)
from ns_common.time import Clock

from .contracts import TransportAdapter, TransportSession
from .models import (
    TransportClose,
    TransportCloseInitiator,
    TransportCloseReason,
    TransportMessage,
    TransportSessionState,
)
from .models import TransportCapabilities, TransportCapability


WEBSOCKET_TCP_TRANSPORT_TYPE = "websocket_tcp"
WEBSOCKET_TCP_CAPABILITIES = TransportCapabilities(frozenset({
    TransportCapability.RELIABLE_ORDERED_MESSAGES,
    TransportCapability.TRANSPORT_FLOW_CONTROL,
    TransportCapability.NATIVE_KEEPALIVE,
}))


@dataclass(frozen=True, slots=True, kw_only=True)
class WebSocketTcpAdapterOptions:
    host: str
    port: int
    clock: Clock
    ssl_context: ssl.SSLContext | None = field(default=None, repr=False)
    environment: str = "local"
    allow_plaintext_non_prod: bool = False
    allowed_origins: tuple[str, ...] = ()
    max_message_bytes: int = 1_048_576
    accept_queue_capacity: int = 128
    send_timeout_seconds: float = 10.0
    ping_timeout_seconds: float = 10.0
    close_timeout_seconds: float = 10.0
    adapter_shutdown_timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        if not isinstance(self.host, str) or not self.host.strip():
            self._invalid("host")
        if isinstance(self.port, bool) or not isinstance(self.port, int) or not 0 <= self.port <= 65535:
            self._invalid("port")
        if not isinstance(self.clock, Clock):
            self._invalid("clock")
        if self.ssl_context is not None and not isinstance(self.ssl_context, ssl.SSLContext):
            self._invalid("ssl_context")
        if self.environment not in {"dev", "local", "prod", "test"}:
            self._invalid("environment")
        if not isinstance(self.allow_plaintext_non_prod, bool):
            self._invalid("allow_plaintext_non_prod")
        if self.environment == "prod" and self.ssl_context is None:
            raise NsRuntimeStartupSecurityError(
                "Runtime production transport requires TLS.",
                details={
                    "component": "transport",
                    "field": "ssl_context",
                    "environment": "prod",
                    "reason": "plaintext_transport_in_production",
                },
            )
        if self.ssl_context is None and not self.allow_plaintext_non_prod:
            raise NsRuntimeStartupSecurityError(
                "Runtime plaintext transport is disabled.",
                details={
                    "component": "transport",
                    "field": "allow_plaintext_non_prod",
                    "reason": "plaintext_transport_disabled",
                },
            )
        try:
            origins = tuple(self.allowed_origins)
        except (TypeError, ValueError):
            self._invalid("allowed_origins")
        if any(not isinstance(item, str) or not item for item in origins):
            self._invalid("allowed_origins")
        object.__setattr__(self, "allowed_origins", origins)
        for field_name in ("max_message_bytes", "accept_queue_capacity"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                self._invalid(field_name)
        for field_name in (
            "send_timeout_seconds",
            "ping_timeout_seconds",
            "close_timeout_seconds",
            "adapter_shutdown_timeout_seconds",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
                self._invalid(field_name)
            object.__setattr__(self, field_name, float(value))

    @staticmethod
    def _invalid(field_name: str) -> None:
        raise NsValidationError(
            "WebSocket TCP adapter option is invalid.",
            details={"component": "transport", "field": field_name},
        )


class WebSocketTcpSession(TransportSession):
    """A library-object firewall around one accepted WebSocket connection."""

    def __init__(self, *, connection: Any, options: WebSocketTcpAdapterOptions) -> None:
        self._connection = connection
        self._options = options
        self._state = TransportSessionState.HANDSHAKING
        self._close_info: TransportClose | None = None
        self._close_lock = asyncio.Lock()
        self._send_lock = asyncio.Lock()
        self._closed = asyncio.Event()

    @property
    def transport_type(self) -> str:
        return WEBSOCKET_TCP_TRANSPORT_TYPE

    @property
    def capabilities(self) -> TransportCapabilities:
        return WEBSOCKET_TCP_CAPABILITIES

    @property
    def state(self) -> TransportSessionState:
        return self._state

    @property
    def close_info(self) -> TransportClose | None:
        return self._close_info

    async def receive(self) -> TransportMessage:
        if self._state is TransportSessionState.CLOSED:
            raise NsStateError(
                "Transport session is closed.",
                details={"component": "transport", "operation": "receive", "state": "closed"},
            )
        try:
            value = await self._connection.recv()
        except asyncio.CancelledError:
            raise
        except Exception:
            await self._mark_remote_closed(clean=False)
            raise NsRuntimeTransportReceiveFailedError(
                "Runtime transport receive failed.",
                details={
                    "component": "transport",
                    "operation": "receive",
                    "transport_type": WEBSOCKET_TCP_TRANSPORT_TYPE,
                },
            ) from None
        if not isinstance(value, str):
            await self._close_with(
                reason=TransportCloseReason.PROTOCOL_ERROR,
                initiator=TransportCloseInitiator.ADAPTER,
                clean=False,
                protocol_code=1003,
            )
            raise NsRuntimeTransportReceiveFailedError(
                "Runtime transport requires text messages.",
                details={
                    "component": "transport",
                    "operation": "receive",
                    "reason": "binary_message_rejected",
                    "transport_type": WEBSOCKET_TCP_TRANSPORT_TYPE,
                },
            )
        byte_size = len(value.encode("utf-8"))
        if byte_size > self._options.max_message_bytes:
            await self._close_with(
                reason=TransportCloseReason.MESSAGE_TOO_LARGE,
                initiator=TransportCloseInitiator.ADAPTER,
                clean=False,
                protocol_code=1009,
            )
            raise NsRuntimeTransportReceiveFailedError(
                "Runtime transport message exceeds the configured boundary.",
                details={
                    "component": "transport",
                    "operation": "receive",
                    "reason": "message_too_large",
                    "transport_type": WEBSOCKET_TCP_TRANSPORT_TYPE,
                },
            )
        return TransportMessage(
            text=value,
            byte_size=byte_size,
            received_at=self._options.clock.utc_now(),
        )

    async def send(self, text: str) -> None:
        if not isinstance(text, str):
            raise NsValidationError(
                "Transport send requires text.",
                details={"component": "transport", "field": "message.text"},
            )
        if len(text.encode("utf-8")) > self._options.max_message_bytes:
            raise NsRuntimeTransportSendFailedError(
                "Runtime transport message exceeds the configured boundary.",
                details={
                    "component": "transport",
                    "operation": "send",
                    "reason": "message_too_large",
                    "transport_type": WEBSOCKET_TCP_TRANSPORT_TYPE,
                },
            )
        if self._state is not TransportSessionState.HANDSHAKING:
            raise NsStateError(
                "Transport session is not writable.",
                details={
                    "component": "transport",
                    "operation": "send",
                    "state": self._state.value,
                },
            )
        try:
            async with self._send_lock:
                await asyncio.wait_for(
                    self._connection.send(text),
                    timeout=self._options.send_timeout_seconds,
                )
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            raise NsRuntimeTransportSendFailedError(
                "Runtime transport send timed out.",
                details={
                    "component": "transport",
                    "operation": "send",
                    "reason": "send_timeout",
                    "transport_type": WEBSOCKET_TCP_TRANSPORT_TYPE,
                },
            ) from None
        except Exception:
            raise NsRuntimeTransportSendFailedError(
                "Runtime transport send failed.",
                details={
                    "component": "transport",
                    "operation": "send",
                    "reason": "write_failed",
                    "transport_type": WEBSOCKET_TCP_TRANSPORT_TYPE,
                },
            ) from None

    async def ping(self) -> None:
        if self._state is not TransportSessionState.HANDSHAKING:
            raise NsStateError(
                "Transport session cannot perform keepalive.",
                details={
                    "component": "transport",
                    "operation": "keepalive",
                    "state": self._state.value,
                },
            )
        try:
            pong_waiter = await self._connection.ping()
            await asyncio.wait_for(
                pong_waiter,
                timeout=self._options.ping_timeout_seconds,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            raise NsRuntimeTransportStreamResetError(
                "Runtime transport keepalive failed.",
                details={
                    "component": "transport",
                    "operation": "keepalive",
                    "transport_type": WEBSOCKET_TCP_TRANSPORT_TYPE,
                },
            ) from None

    async def close(self) -> TransportClose:
        return await self._close_with(
            reason=TransportCloseReason.NORMAL,
            initiator=TransportCloseInitiator.LOCAL,
            clean=True,
            protocol_code=1000,
        )

    async def wait_closed(self) -> None:
        await self._closed.wait()

    async def _mark_remote_closed(self, *, clean: bool) -> TransportClose:
        return await self._close_with(
            reason=TransportCloseReason.REMOTE_CLOSED,
            initiator=TransportCloseInitiator.REMOTE,
            clean=clean,
            protocol_code=getattr(self._connection, "close_code", None),
            send_close=False,
        )

    async def _close_with(
        self,
        *,
        reason: TransportCloseReason,
        initiator: TransportCloseInitiator,
        clean: bool,
        protocol_code: int | None,
        send_close: bool = True,
    ) -> TransportClose:
        async with self._close_lock:
            if self._close_info is not None:
                return self._close_info
            self._state = TransportSessionState.CLOSING
            close_info = TransportClose(
                reason=reason,
                initiator=initiator,
                clean=clean,
                protocol_code=protocol_code,
            )
            if send_close:
                try:
                    await asyncio.wait_for(
                        self._connection.close(
                            code=protocol_code or 1000,
                            reason="",
                        ),
                        timeout=self._options.close_timeout_seconds,
                    )
                except asyncio.CancelledError:
                    self._state = TransportSessionState.CLOSED
                    self._close_info = close_info
                    self._closed.set()
                    raise
                except Exception:
                    close_info = TransportClose(
                        reason=reason,
                        initiator=initiator,
                        clean=False,
                        protocol_code=protocol_code,
                    )
            self._state = TransportSessionState.CLOSED
            self._close_info = close_info
            self._closed.set()
            return close_info


class WebSocketTcpAdapter(TransportAdapter):
    """TLS/TCP WebSocket listener with typed admission and drain operations."""

    def __init__(self, *, options: WebSocketTcpAdapterOptions) -> None:
        if not isinstance(options, WebSocketTcpAdapterOptions):
            raise NsValidationError(
                "WebSocket TCP adapter options are invalid.",
                details={"component": "transport", "field": "options"},
            )
        self._options = options
        self._server: Any | None = None
        self._accept_queue: asyncio.Queue[WebSocketTcpSession] = asyncio.Queue(
            maxsize=options.accept_queue_capacity,
        )
        self._sessions: set[WebSocketTcpSession] = set()
        self._accepting = False
        self._start_lock = asyncio.Lock()
        self._close_lock = asyncio.Lock()
        self._closed = False

    @property
    def transport_type(self) -> str:
        return WEBSOCKET_TCP_TRANSPORT_TYPE

    @property
    def capabilities(self) -> TransportCapabilities:
        return WEBSOCKET_TCP_CAPABILITIES

    @property
    def accepting(self) -> bool:
        return self._accepting

    @property
    def bound_port(self) -> int | None:
        if self._server is None or not self._server.sockets:
            return None
        return int(self._server.sockets[0].getsockname()[1])

    async def start(self) -> None:
        async with self._start_lock:
            if self._closed:
                raise NsStateError(
                    "Transport adapter is closed.",
                    details={"component": "transport", "operation": "listen", "state": "closed"},
                )
            if self._server is not None:
                return
            try:
                from websockets.asyncio.server import serve

                self._server = await serve(
                    self._handle_connection,
                    self._options.host,
                    self._options.port,
                    ssl=self._options.ssl_context,
                    origins=(self._options.allowed_origins or None),
                    compression=None,
                    max_size=self._options.max_message_bytes,
                    max_queue=16,
                    open_timeout=self._options.send_timeout_seconds,
                    ping_timeout=self._options.ping_timeout_seconds,
                    close_timeout=self._options.close_timeout_seconds,
                    server_header=None,
                )
            except asyncio.CancelledError:
                raise
            except Exception:
                raise NsRuntimeTransportHandshakeFailedError(
                    "Runtime transport listener failed.",
                    details={
                        "component": "transport",
                        "operation": "listen",
                        "transport_type": WEBSOCKET_TCP_TRANSPORT_TYPE,
                    },
                ) from None
            self._accepting = True

    async def accept(self) -> TransportSession:
        if not self._accepting and self._accept_queue.empty():
            raise NsStateError(
                "Transport adapter is not accepting sessions.",
                details={"component": "transport", "operation": "accept", "state": "closed"},
            )
        return await self._accept_queue.get()

    async def stop_admission(self) -> None:
        self._accepting = False
        if self._server is not None:
            self._server.close(close_connections=False)

    async def drain(self) -> None:
        sessions = tuple(self._sessions)
        if not sessions:
            return
        try:
            await asyncio.wait_for(
                asyncio.gather(*(session.close() for session in sessions)),
                timeout=self._options.adapter_shutdown_timeout_seconds,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            # Individual close paths normalize and seal their own state. Drain
            # remains fail-soft so one broken socket cannot retain the adapter.
            return

    async def close(self) -> None:
        async with self._close_lock:
            if self._closed:
                return
            await self.stop_admission()
            await self.drain()
            if self._server is not None:
                self._server.close()
                try:
                    await asyncio.wait_for(
                        self._server.wait_closed(),
                        timeout=self._options.adapter_shutdown_timeout_seconds,
                    )
                except asyncio.CancelledError:
                    raise
                except Exception:
                    pass
            self._closed = True

    async def _handle_connection(self, connection: Any) -> None:
        if not self._accepting:
            try:
                await connection.close(code=1001, reason="")
            except Exception:
                pass
            return
        session = WebSocketTcpSession(connection=connection, options=self._options)
        self._sessions.add(session)
        try:
            self._accept_queue.put_nowait(session)
        except asyncio.QueueFull:
            await session._close_with(
                reason=TransportCloseReason.READ_QUEUE_FULL,
                initiator=TransportCloseInitiator.ADAPTER,
                clean=False,
                protocol_code=1013,
            )
            self._sessions.discard(session)
            return
        try:
            await connection.wait_closed()
            if session.state is not TransportSessionState.CLOSED:
                await session._mark_remote_closed(
                    clean=getattr(connection, "close_code", None) in {1000, 1001},
                )
        finally:
            self._sessions.discard(session)


__all__ = (
    "WEBSOCKET_TCP_CAPABILITIES",
    "WEBSOCKET_TCP_TRANSPORT_TYPE",
    "WebSocketTcpAdapter",
    "WebSocketTcpAdapterOptions",
    "WebSocketTcpSession",
)
