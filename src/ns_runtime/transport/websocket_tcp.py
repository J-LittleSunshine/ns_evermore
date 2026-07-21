# -*- coding: utf-8 -*-
"""WebSocket over TCP adapter declarations.

The third-party WebSocket implementation is imported lazily by the operational
adapter path added in P04-W03. Importing this module only exposes frozen runtime
contracts and cannot open a listener.
"""

from __future__ import annotations

from .models import TransportCapabilities, TransportCapability


WEBSOCKET_TCP_TRANSPORT_TYPE = "websocket_tcp"
WEBSOCKET_TCP_CAPABILITIES = TransportCapabilities(frozenset({
    TransportCapability.RELIABLE_ORDERED_MESSAGES,
    TransportCapability.TRANSPORT_FLOW_CONTROL,
    TransportCapability.NATIVE_KEEPALIVE,
}))


__all__ = (
    "WEBSOCKET_TCP_CAPABILITIES",
    "WEBSOCKET_TCP_TRANSPORT_TYPE",
)

