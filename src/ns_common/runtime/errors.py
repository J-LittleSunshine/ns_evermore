# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

class NsRuntimeError(Exception):
    """Base error for ns runtime infrastructure."""


class NsRuntimeConfigurationError(NsRuntimeError):
    """Raised when runtime configuration is invalid."""


class NsRuntimeValidationError(NsRuntimeError):
    """Raised when runtime payload validation fails."""


class NsRuntimePublishError(NsRuntimeError):
    """Raised when runtime message publishing fails."""

class NsRuntimeIpcError(NsRuntimeError):
    """Raised when runtime IPC operation fails."""

class NsRuntimeOutboxError(NsRuntimeError):
    """Raised when runtime outbox operation fails."""


class NsRuntimeBrokerError(NsRuntimeError):
    """Raised when runtime broker operation fails."""


class NsRuntimeAckTimeoutError(NsRuntimeError):
    """Raised when runtime message ack times out."""
