# -*- coding: utf-8 -*-
"""Transport-independent logical connection lifecycle contracts."""

from __future__ import annotations

from .state import (
    LogicalConnectionCloseReason,
    LogicalConnectionState,
    LogicalConnectionStateMachine,
    LogicalConnectionStateSnapshot,
)


__all__ = (
    "LogicalConnectionCloseReason",
    "LogicalConnectionState",
    "LogicalConnectionStateMachine",
    "LogicalConnectionStateSnapshot",
)
