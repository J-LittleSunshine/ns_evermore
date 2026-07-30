# -*- coding: utf-8 -*-
"""Adapter from P05 local connection ownership to the P11 send boundary."""

from __future__ import annotations

from ns_common.exceptions import NsValidationError
from ns_runtime.connection.lifecycle import ConnectionLifecycleManager

from .models import DeliveryRecord, DeliveryWriteFailure
from .scheduling import (
    DeliveryTargetResolver,
    DeliveryTransportWriter,
    DeliveryTransportWriteResult,
    DeliveryTransportWriteState,
    LocalDeliveryTarget,
    OutboundDeliveryPayload,
)


class ConnectionLifecycleDeliveryAdapter(
    DeliveryTargetResolver,
    DeliveryTransportWriter,
):
    def __init__(self, *, manager: ConnectionLifecycleManager) -> None:
        if not isinstance(manager, ConnectionLifecycleManager):
            raise NsValidationError(
                "P11 local delivery manager is invalid.",
                details={"component": "delivery_local_transport", "field": "manager"},
            )
        self._manager = manager

    async def resolve(self, delivery: DeliveryRecord) -> LocalDeliveryTarget:
        if not isinstance(delivery, DeliveryRecord):
            raise NsValidationError(
                "P11 local delivery record is invalid.",
                details={"component": "delivery_local_transport", "field": "delivery"},
            )
        return await self._manager.resolve_local_delivery_target(delivery.binding)

    async def write(
        self,
        *,
        target: LocalDeliveryTarget,
        payload: OutboundDeliveryPayload,
    ) -> DeliveryTransportWriteResult:
        from ns_runtime.transport import TransportWriteResult, TransportWriteState

        try:
            result = await self._manager.write_local_delivery(
                target=target,
                payload=payload,
            )
        except BaseException:
            raise
        if type(result) is not TransportWriteResult:
            return DeliveryTransportWriteResult(
                state=DeliveryTransportWriteState.UNCERTAIN,
                failure=DeliveryWriteFailure.TRANSPORT_WRITE_FAILED,
            )
        if result.state is TransportWriteState.SUCCEEDED:
            return DeliveryTransportWriteResult(
                state=DeliveryTransportWriteState.SUCCEEDED,
            )
        failure = (
            DeliveryWriteFailure.TRANSPORT_WRITE_TIMEOUT
            if result.failure_reason == "send_timeout"
            else DeliveryWriteFailure.TRANSPORT_WRITE_FAILED
        )
        return DeliveryTransportWriteResult(
            state=(
                DeliveryTransportWriteState.NOT_STARTED
                if result.state is TransportWriteState.NOT_STARTED
                else DeliveryTransportWriteState.UNCERTAIN
            ),
            failure=failure,
        )


__all__ = ("ConnectionLifecycleDeliveryAdapter",)
