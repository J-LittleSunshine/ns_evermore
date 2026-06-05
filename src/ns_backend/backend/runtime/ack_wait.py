# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass

from ns_common.runtime.constants import (
    RUNTIME_MESSAGE_STATUS_ACKED,
    RUNTIME_MESSAGE_STATUS_DEAD,
    RUNTIME_MESSAGE_STATUS_RETRY,
)
from ns_common.runtime.errors import NsRuntimeError


class NsBackendRuntimeAckWaitError(NsRuntimeError):
    """Raised when backend runtime ack wait operation fails."""


class NsBackendRuntimeAckTimeoutError(NsBackendRuntimeAckWaitError):
    """Raised when waiting runtime ack exceeds timeout."""


@dataclass(slots=True, frozen=True, kw_only=True)
class NsBackendRuntimeAckWaitResult:
    """Result of waiting for runtime-level outbox acknowledgement.

    This result only represents runtime infrastructure acknowledgement.
    It does not mean frontend delivery, business processing, or request/reply
    completion.
    """

    message_id: str
    status: str | None
    timeout_seconds: float
    elapsed_seconds: float

    @property
    def acked(self) -> bool:
        """Return whether the message was acknowledged by runtime."""
        return self.status == RUNTIME_MESSAGE_STATUS_ACKED

    @property
    def retry(self) -> bool:
        """Return whether the message was released for retry."""
        return self.status == RUNTIME_MESSAGE_STATUS_RETRY

    @property
    def dead(self) -> bool:
        """Return whether the message was marked permanently failed."""
        return self.status == RUNTIME_MESSAGE_STATUS_DEAD

    @property
    def timed_out(self) -> bool:
        """Return whether waiting ended before a terminal status was observed."""
        return self.status is None

    @property
    def completed(self) -> bool:
        """Return whether a terminal runtime outbox status was observed."""
        return self.acked or self.retry or self.dead

    def raise_for_timeout(self) -> None:
        """Raise timeout error if runtime ack was not observed."""
        if self.timed_out:
            raise NsBackendRuntimeAckTimeoutError(
                f"runtime ack wait timed out: message_id={self.message_id}"
            )
