# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ns_backend.backend.runtime.inbox import NsBackendRuntimeInboundMessage
from ns_common.runtime.errors import NsRuntimeError


class NsBackendRuntimeRequestReplyError(NsRuntimeError):
    """Raised when backend runtime request/reply operation fails."""


class NsBackendRuntimeRequestTimeoutError(NsBackendRuntimeRequestReplyError):
    """Raised when backend runtime request/reply waits beyond timeout."""


@dataclass(slots=True, frozen=True, kw_only=True)
class NsBackendRuntimeRequestReplyResult:
    """Result of a short-timeout backend runtime request/reply call.

    This object deliberately keeps timeout as a normal result state, so Django
    views can return HTTP 202/504 according to business semantics instead of
    always handling exceptions.
    """

    request_message_id: str
    correlation_id: str
    reply_to_backend_id: str
    timeout_seconds: float
    elapsed_seconds: float
    reply: NsBackendRuntimeInboundMessage | None = None

    @property
    def timed_out(self) -> bool:
        """Return whether no reply was received within timeout."""
        return self.reply is None

    @property
    def ok(self) -> bool:
        """Return whether a reply was received."""
        return self.reply is not None

    @property
    def payload(self) -> dict[str, Any] | None:
        """Return reply payload when available."""
        if self.reply is None:
            return None
        return dict(self.reply.payload)

    def raise_for_timeout(self) -> None:
        """Raise timeout error when no reply was received."""
        if self.reply is None:
            raise NsBackendRuntimeRequestTimeoutError(f"runtime request/reply timed out: correlation_id={self.correlation_id}, reply_to_backend_id={self.reply_to_backend_id}")
