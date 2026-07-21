# -*- coding: utf-8 -*-
"""Transport-independent runtime adapter contracts."""

from .contracts import TransportAdapter, TransportSession
from .conformance import TRANSPORT_CONFORMANCE_CASES, TransportConformanceCase
from .errors import NormalizedTransportFailure, normalize_transport_exception
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
from .registry import (
    TRANSPORT_ADAPTER_NAMES,
    TransportAdapterBuildContext,
    TransportAdapterRegistration,
    TransportAdapterRegistry,
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
    "TransportAdapterBuildContext",
    "TransportAdapterRegistration",
    "TransportAdapterRegistry",
    "TransportCapabilities",
    "TransportCapability",
    "TransportClose",
    "TransportCloseInitiator",
    "TransportCloseReason",
    "TransportConformanceCase",
    "TransportError",
    "TransportErrorKind",
    "TransportDiagnosticSummary",
    "TransportIdentity",
    "TransportIdentityFactory",
    "TransportMessage",
    "NormalizedTransportFailure",
    "TransportPathSnapshot",
    "TransportSession",
    "TransportSessionState",
    "TRANSPORT_ADAPTER_NAMES",
    "TRANSPORT_CONFORMANCE_CASES",
    "WEBSOCKET_TCP_CAPABILITIES",
    "WEBSOCKET_TCP_TRANSPORT_TYPE",
    "WebSocketTcpAdapter",
    "WebSocketTcpAdapterOptions",
    "WebSocketTcpSession",
    "normalize_transport_exception",
)
