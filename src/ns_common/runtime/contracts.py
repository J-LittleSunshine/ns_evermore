# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, AsyncIterator

from ns_common.runtime.messages import NsRuntimeAck, NsRuntimeMessage

if TYPE_CHECKING:
    pass


class NsRuntimeOutbox(Protocol):
    """Durable outbox protocol used by ns_backend workers and runtime connector."""

    def enqueue(self, message: NsRuntimeMessage) -> str:
        """Persist one runtime message and return message id."""

    def claim_batch(self, *, consumer_id: str, limit: int) -> list[NsRuntimeMessage]:
        """Claim pending messages for one connector consumer."""

    def mark_acked(self, *, message_id: str, ack: NsRuntimeAck | None = None) -> None:
        """Mark one message as acknowledged by runtime master."""

    def mark_retry(self, *, message_id: str, reason: str) -> None:
        """Release one message for retry."""

    def mark_dead(self, *, message_id: str, reason: str) -> None:
        """Mark one message as permanently failed."""

    def get_status(self, message_id: str) -> str | None:
        """Return one message status by message id."""

class AsyncNsRuntimeOutbox(Protocol):
    """Async durable outbox protocol used by async runtime components."""

    async def enqueue(self, message: NsRuntimeMessage) -> str:
        """Persist one runtime message and return message id."""

    async def claim_batch(self, *, consumer_id: str, limit: int) -> list[NsRuntimeMessage]:
        """Claim pending messages for one connector consumer."""

    async def mark_acked(self, *, message_id: str, ack: NsRuntimeAck | None = None) -> None:
        """Mark one message as acknowledged by runtime master."""

    async def mark_retry(self, *, message_id: str, reason: str) -> None:
        """Release one message for retry."""

    async def mark_dead(self, *, message_id: str, reason: str) -> None:
        """Mark one message as permanently failed."""

    async def get_status(self, message_id: str) -> str | None:
        """Return one message status by message id."""

class NsRuntimeBroker(Protocol):
    """Runtime broker protocol for cluster event distribution."""

    async def publish(self, channel: str, payload: bytes) -> None:
        """Publish encoded runtime message to one channel."""

    async def subscribe(self, channel: str) -> AsyncIterator[bytes]:
        """Subscribe to one channel and yield encoded messages."""

    async def close(self) -> None:
        """Close broker resources."""


class NsRuntimePublisher(Protocol):
    """Runtime message publisher protocol used by business modules."""

    def publish(self, message: NsRuntimeMessage) -> str:
        """Publish one runtime message and return message id."""
