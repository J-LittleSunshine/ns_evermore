# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Literal

from ns_common.runtime.messages import NsRuntimeAck
from ns_runtime.protocol import NsRuntimeWireFrame, parse_ack_frame

RuntimeConnectionType = Literal["unknown", "backend", "runtime_sub", "frontend"]
RuntimeConnectionStatus = Literal["healthy", "unhealthy", "closed"]


@dataclass(slots=True, kw_only=True)
class NsRuntimeConnection:
    """Runtime WebSocket connection state.

    The websocket object is intentionally kept as Any because different
    websockets versions expose different concrete protocol classes.
    """

    websocket: Any
    connection_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    connection_type: RuntimeConnectionType = "unknown"
    status: RuntimeConnectionStatus = "healthy"

    node_id: str | None = None
    node_role: str | None = None
    instance_id: str | None = None
    service_name: str = ""
    version: str = ""
    environment: str = ""
    remote_address: str = ""

    client_id: str | None = None
    session_id: str | None = None
    user_id: str | None = None
    rooms: set[str] = field(default_factory=set)
    device: str = ""

    registered_at_epoch_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    last_seen_epoch_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    health: dict[str, Any] = field(default_factory=dict)

    send_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    pending_acks: dict[str, asyncio.Future[NsRuntimeAck]] = field(default_factory=dict)

    async def send_frame(self, frame: NsRuntimeWireFrame) -> None:
        """Send one wire frame through this connection."""
        async with self.send_lock:
            await self.websocket.send(frame.to_json())

    def mark_seen(self, *, health: dict[str, Any] | None = None) -> None:
        """Refresh connection last-seen state."""
        self.last_seen_epoch_ms = int(time.time() * 1000)
        self.status = "healthy"
        if health is not None:
            self.health = dict(health)

    def create_pending_ack(self, message_id: str) -> asyncio.Future[NsRuntimeAck]:
        """Create one pending ack future for an outbound message."""
        normalized_message_id: str = str(message_id or "").strip()
        if not normalized_message_id:
            raise ValueError("message_id is required for pending ack")

        loop = asyncio.get_running_loop()
        future: asyncio.Future[NsRuntimeAck] = loop.create_future()
        self.pending_acks[normalized_message_id] = future
        return future

    def remove_pending_ack(self, message_id: str) -> None:
        """Remove one pending ack future."""
        normalized_message_id: str = str(message_id or "").strip()
        if normalized_message_id:
            self.pending_acks.pop(normalized_message_id, None)

    def resolve_ack(self, frame: NsRuntimeWireFrame) -> bool:
        """Resolve one pending ack if the frame matches an outbound message."""
        ack: NsRuntimeAck = parse_ack_frame(frame)
        future: asyncio.Future[NsRuntimeAck] | None = self.pending_acks.pop(ack.message_id, None)
        if future is None:
            return False

        if not future.done():
            future.set_result(ack)
        return True

    def reject_pending_acks(self, exc: BaseException) -> None:
        """Reject all pending acks when connection is closed."""
        pending_acks = list(self.pending_acks.values())
        self.pending_acks.clear()

        for future in pending_acks:
            if not future.done():
                future.set_exception(exc)
