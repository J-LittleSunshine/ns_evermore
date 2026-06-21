# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from itertools import count

from ns_common.runtime.config import NsRuntimeConfig
from ns_common.runtime.constants import (
    RUNTIME_ACK_STATUS_ACCEPTED,
    RUNTIME_ACK_STATUS_REJECTED,
    RUNTIME_MASTER_FORWARD_LOCAL_FIRST,
    RUNTIME_MASTER_FORWARD_SUB_REQUIRED,
    RUNTIME_NODE_ROLE_MASTER,
    RUNTIME_NODE_ROLE_STANDALONE,
    RUNTIME_NODE_ROLE_SUB,
)
from ns_common.runtime.messages import NsRuntimeAck, NsRuntimeMessage
from ns_runtime.connection import NsRuntimeConnection
from ns_runtime.delivery import NsRuntimeLocalDelivery
from ns_runtime.protocol import build_runtime_forward_frame
from ns_runtime.registry import NsRuntimeConnectionRegistry


class NsRuntimeDispatcher:
    """Runtime message dispatcher.

    P8 implements backend.publish dispatching plus local frontend delivery:
    - standalone: local delivery
    - master: sub-first forwarding with local fallback
    - sub: local delivery for runtime.forward
    """

    def __init__(
            self,
            *,
            config: NsRuntimeConfig,
            registry: NsRuntimeConnectionRegistry,
            delivery: NsRuntimeLocalDelivery | None = None,
    ) -> None:
        """Initialize dispatcher."""
        self._config = config
        self._registry = registry
        self._delivery = delivery or NsRuntimeLocalDelivery(registry=registry)
        self._round_robin_counter = count()

    async def dispatch_backend_publish(self, message: NsRuntimeMessage) -> NsRuntimeAck:
        """Dispatch backend.publish according to node role and forward policy."""
        normalized_message = message.normalized()

        if self._config.node_role == RUNTIME_NODE_ROLE_STANDALONE:
            return await self.local_handle(normalized_message)

        if self._config.node_role == RUNTIME_NODE_ROLE_SUB:
            return NsRuntimeAck(
                message_id=str(normalized_message.message_id),
                status=RUNTIME_ACK_STATUS_REJECTED,  # type: ignore[arg-type]
                reason="sub runtime node does not accept backend.publish directly",
                handled_by=self._config.node_id,
                trace_id=normalized_message.trace_id,
            ).normalized()

        if self._config.node_role != RUNTIME_NODE_ROLE_MASTER:
            return NsRuntimeAck(
                message_id=str(normalized_message.message_id),
                status=RUNTIME_ACK_STATUS_REJECTED,  # type: ignore[arg-type]
                reason=f"unsupported runtime node_role: {self._config.node_role}",
                handled_by=self._config.node_id,
                trace_id=normalized_message.trace_id,
            ).normalized()

        if self._config.master_forward_policy == RUNTIME_MASTER_FORWARD_LOCAL_FIRST:
            return await self.local_handle(normalized_message)

        sub_nodes: list[NsRuntimeConnection] = self._ordered_sub_nodes()
        if sub_nodes:
            forwarded_ack = await self._forward_to_sub_nodes(normalized_message, sub_nodes)
            if forwarded_ack is not None:
                return forwarded_ack

            if self._config.master_forward_policy == RUNTIME_MASTER_FORWARD_SUB_REQUIRED:
                return NsRuntimeAck(
                    message_id=str(normalized_message.message_id),
                    status=RUNTIME_ACK_STATUS_REJECTED,  # type: ignore[arg-type]
                    reason="runtime master failed to forward message to sub node",
                    handled_by=self._config.node_id,
                    trace_id=normalized_message.trace_id,
                ).normalized()

        if self._config.master_forward_policy == RUNTIME_MASTER_FORWARD_SUB_REQUIRED:
            return NsRuntimeAck(
                message_id=str(normalized_message.message_id),
                status=RUNTIME_ACK_STATUS_REJECTED,  # type: ignore[arg-type]
                reason="runtime master requires sub node but no healthy sub node is available",
                handled_by=self._config.node_id,
                trace_id=normalized_message.trace_id,
            ).normalized()

        if not self._config.master_handle_when_no_sub_node:
            return NsRuntimeAck(
                message_id=str(normalized_message.message_id),
                status=RUNTIME_ACK_STATUS_REJECTED,  # type: ignore[arg-type]
                reason="runtime master local handling is disabled and no healthy sub node is available",
                handled_by=self._config.node_id,
                trace_id=normalized_message.trace_id,
            ).normalized()

        return await self.local_handle(normalized_message)

    async def local_handle(self, message: NsRuntimeMessage) -> NsRuntimeAck:
        """Accept and locally deliver message.

        P8 local delivery is best-effort frontend fanout. No matched frontend
        connection is still accepted because offline/presence semantics are not
        part of this stage.
        """
        normalized_message = message.normalized()
        await self._delivery.deliver(normalized_message)

        return NsRuntimeAck(
            message_id=str(normalized_message.message_id),
            status=RUNTIME_ACK_STATUS_ACCEPTED,  # type: ignore[arg-type]
            handled_by=self._config.node_id,
            trace_id=normalized_message.trace_id,
        ).normalized()

    def _ordered_sub_nodes(self) -> list[NsRuntimeConnection]:
        """Return healthy sub nodes in round-robin order."""
        sub_nodes: list[NsRuntimeConnection] = self._registry.list_healthy_sub_nodes()
        if len(sub_nodes) <= 1:
            return sub_nodes

        start_index = next(self._round_robin_counter) % len(sub_nodes)
        return sub_nodes[start_index:] + sub_nodes[:start_index]

    async def _forward_to_sub_nodes(self, message: NsRuntimeMessage, sub_nodes: list[NsRuntimeConnection]) -> NsRuntimeAck | None:
        """Forward message to sub nodes until one accepts it."""
        normalized_message = message.normalized()
        message_id: str = str(normalized_message.message_id)
        frame = build_runtime_forward_frame(
            source_node_id=self._config.node_id,
            message=normalized_message,
        )

        for sub_node in sub_nodes:
            try:
                pending_ack = sub_node.create_pending_ack(message_id)
                await sub_node.send_frame(frame)
                ack: NsRuntimeAck = await asyncio.wait_for(pending_ack, timeout=float(self._config.ack_timeout_seconds))
            except Exception:
                sub_node.remove_pending_ack(message_id)
                continue

            if ack.status == RUNTIME_ACK_STATUS_ACCEPTED:
                return ack

        return None
