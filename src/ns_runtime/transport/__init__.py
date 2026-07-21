# -*- coding: utf-8 -*-
"""Transport-independent runtime adapter contracts."""

from .contracts import TransportAdapter, TransportSession
from .identity import (
    TransportDiagnosticSummary,
    TransportIdentity,
    TransportIdentityFactory,
    TransportPathSnapshot,
)
from .models import (
    TransportCapabilities,
    TransportCapability,
    TransportClose,
    TransportCloseInitiator,
    TransportCloseReason,
    TransportError,
    TransportErrorKind,
    TransportMessage,
    TransportSessionState,
)
from .websocket_tcp import (
    WEBSOCKET_TCP_CAPABILITIES,
    WEBSOCKET_TCP_TRANSPORT_TYPE,
    WebSocketTcpAdapter,
    WebSocketTcpAdapterOptions,
    WebSocketTcpSession,
)


__all__ = (
    "TransportAdapter",
    "TransportCapabilities",
    "TransportCapability",
    "TransportClose",
    "TransportCloseInitiator",
    "TransportCloseReason",
    "TransportError",
    "TransportErrorKind",
    "TransportDiagnosticSummary",
    "TransportIdentity",
    "TransportIdentityFactory",
    "TransportMessage",
    "TransportPathSnapshot",
    "TransportSession",
    "TransportSessionState",
    "WEBSOCKET_TCP_CAPABILITIES",
    "WEBSOCKET_TCP_TRANSPORT_TYPE",
    "WebSocketTcpAdapter",
    "WebSocketTcpAdapterOptions",
    "WebSocketTcpSession",
)
