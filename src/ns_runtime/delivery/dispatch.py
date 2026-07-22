# -*- coding: utf-8 -*-
"""P11 local experimental dispatch composition over the existing supervisor."""

from __future__ import annotations

from collections.abc import Callable

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import NsStateError, NsValidationError
from ns_common.time import Clock

from .scheduling import (
    ClaimOutcome,
    DeliveryPayloadResolver,
    DeliveryPayloadValidator,
    DeliverySchedulingPolicy,
    SendOutcome,
    DeliveryTargetResolver,
    DeliveryTransportWriter,
    OwnerRiskGuard,
)
from .scheduling_store import StateStoreDeliveryScheduler
from .workers import ClaimWorker, LeaseRenewWorker, PreparedActivationCoordinator, SendWorker


class LocalDeliveryDispatchCoordinator:
    """Schedule bounded local dispatch turns; it owns no event loop or shutdown."""

    def __init__(
        self,
        *,
        task_supervisor: TaskSupervisor,
        scheduler: StateStoreDeliveryScheduler,
        policy: DeliverySchedulingPolicy,
        runtime_id: str,
        target_resolver: DeliveryTargetResolver,
        payload_validator: DeliveryPayloadValidator,
        payload_resolver: DeliveryPayloadResolver,
        transport_writer: DeliveryTransportWriter,
        risk_guard: OwnerRiskGuard,
        identifier_factory: Callable[[str], str],
        clock: Clock,
    ) -> None:
        for value, expected, field in (
            (task_supervisor, TaskSupervisor, "task_supervisor"),
            (scheduler, StateStoreDeliveryScheduler, "scheduler"),
            (policy, DeliverySchedulingPolicy, "policy"),
            (target_resolver, DeliveryTargetResolver, "target_resolver"),
            (payload_validator, DeliveryPayloadValidator, "payload_validator"),
            (payload_resolver, DeliveryPayloadResolver, "payload_resolver"),
            (transport_writer, DeliveryTransportWriter, "transport_writer"),
            (risk_guard, OwnerRiskGuard, "risk_guard"),
            (clock, Clock, "clock"),
        ):
            if not isinstance(value, expected):
                _invalid(field)
        _text(runtime_id, "runtime_id")
        if not callable(identifier_factory):
            _invalid("identifier_factory")
        self._supervisor = task_supervisor
        self._scheduler = scheduler
        self._policy = policy
        self._runtime_id = runtime_id
        self._targets = target_resolver
        self._payload_validation = payload_validator
        self._payloads = payload_resolver
        self._transport = transport_writer
        self._risk_guard = risk_guard
        self._ids = identifier_factory
        self._clock = clock
        self._activation = PreparedActivationCoordinator(
            scheduler=scheduler,
            policy=policy,
        )

    def schedule(self, *, tenant_id: str) -> bool:
        """Register one bounded turn with the runtime's existing supervisor."""

        _text(tenant_id, "schedule.tenant_id")
        task_id = self._identifier("dispatch_task")
        try:
            self._supervisor.create_task(
                self._run_once(tenant_id=tenant_id),
                name=f"p11-local-dispatch:{task_id}",
                cancel_order=24,
            )
        except NsStateError:
            # Admission is already authoritative. During shutdown it must remain
            # prepared rather than turning a committed acceptance into an error.
            return False
        return True

    async def _run_once(self, *, tenant_id: str) -> None:
        await self._activation.run_once(
            tenant_id=tenant_id,
        )
        for _ in range(self._policy.activation_batch_size):
            worker_id = self._identifier("claim_worker")
            claim = await ClaimWorker(
                scheduler=self._scheduler,
                policy=self._policy,
                runtime_id=self._runtime_id,
                worker_id=worker_id,
                token_factory=lambda: self._identifier("claim_token"),
            ).run_once(tenant_id=tenant_id)
            if claim.outcome is not ClaimOutcome.CLAIMED:
                return
            LeaseRenewWorker(
                scheduler=self._scheduler, policy=self._policy,
                risk_guard=self._risk_guard,
            ).schedule(claim=claim.claim, supervisor=self._supervisor)
            result = await SendWorker(
                scheduler=self._scheduler,
                policy=self._policy,
                target_resolver=self._targets,
                payload_validator=self._payload_validation,
                payload_resolver=self._payloads,
                transport_writer=self._transport,
                risk_guard=self._risk_guard,
                attempt_id_factory=lambda: self._identifier("attempt"),
                clock=self._clock,
            ).run_once(claim=claim.claim)
            if result.outcome in {SendOutcome.PRECHECK_FAILED, SendOutcome.OWNER_RISK}:
                # The same queued item would be selected again. Stop this turn
                # instead of amplifying a disconnect, invalid payload, or risk.
                return

    def _identifier(self, kind: str) -> str:
        value = self._ids(kind)
        if type(value) is not str or not value or "\0" in value:
            _invalid("identifier_factory.result")
        return value


def _text(value: object, field: str) -> None:
    if type(value) is not str or not value or "\0" in value:
        _invalid(field)


def _invalid(field: str):
    raise NsValidationError(
        "P11 local dispatch composition is invalid.",
        details={"component": "local_delivery_dispatch", "field": field},
    )


__all__ = ("LocalDeliveryDispatchCoordinator",)
