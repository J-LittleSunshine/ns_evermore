# -*- coding: utf-8 -*-
"""Transport-independent logical connection lifecycle contracts."""

from __future__ import annotations

from .handshake import ConnectionHelloReceiver
from .state import (
    LogicalConnectionCloseReason,
    LogicalConnectionState,
    LogicalConnectionStateMachine,
    LogicalConnectionStateSnapshot,
)


__all__ = (
    "ConnectionHelloReceiver",
    "LogicalConnectionCloseReason",
    "LogicalConnectionState",
    "LogicalConnectionStateMachine",
    "LogicalConnectionStateSnapshot",
)
