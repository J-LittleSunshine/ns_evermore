# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass

from ns_common.runtime.messages import NsRuntimeMessage
from ns_runtime.protocol import build_frontend_message_frame
from ns_runtime.registry import NsRuntimeConnectionRegistry


@dataclass(slots=True, frozen=True, kw_only=True)
class NsRuntimeDeliveryResult:
    """Local frontend delivery result.

    P8 delivery is best-effort in-process fanout. This result is diagnostic
    only. Backend runtime ACK still means runtime accepted the message, not
    that every frontend client processed it.
    """

    matched_count: int = 0
    delivered_count: int = 0
    failed_count: int = 0


class NsRuntimeLocalDelivery:
    """In-process frontend delivery.

    P8 intentionally does not wait for frontend ACK. It only sends
    frontend.message frames to currently registered local frontend connections.
    """

    def __init__(self, *, registry: NsRuntimeConnectionRegistry) -> None:
        """Initialize local delivery with runtime registry."""
        self._registry = registry

    async def deliver(self, message: NsRuntimeMessage) -> NsRuntimeDeliveryResult:
        """Deliver one runtime message to local frontend connections."""
        normalized_message = message.normalized()
        targets = self._registry.list_frontend_targets(normalized_message)
        frame = build_frontend_message_frame(normalized_message)

        delivered_count = 0
        failed_count = 0

        for connection in targets:
            try:
                await connection.send_frame(frame)
                delivered_count += 1
            except Exception:  # noqa
                # P8 does not fail backend ACK on frontend send failure.
                # The connection receive loop will eventually clean up closed sockets.
                connection.status = "unhealthy"
                failed_count += 1

        return NsRuntimeDeliveryResult(
            matched_count=len(targets),
            delivered_count=delivered_count,
            failed_count=failed_count,
        )
