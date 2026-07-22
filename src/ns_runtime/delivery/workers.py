# -*- coding: utf-8 -*-
"""P11 run-once workers composed under the existing runtime supervisor."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
from typing import Callable

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import NsRuntimeStateStoreError, NsValidationError
from ns_common.time import Clock
from ns_runtime.protocol import (
    AuthContextGroup, DeliveryGroup, Envelope, MessageGroup, PayloadGroup,
    ProtocolGroup, SourceGroup, TargetGroup, TraceGroup,
    canonical_checksum, canonical_serialize,
)

from .models import DeliveryOwnerRisk, DeliveryRecordStatus, DeliveryWriteFailure
from .scheduling import (
    ClaimResult,
    DeliveryClaim,
    DeliveryPayloadResolver,
    DeliveryPayloadValidator,
    DeliverySchedulingPolicy,
    DeliveryTargetResolver,
    DeliveryTransportWriter,
    LeaseRenewOutcome,
    LeaseRenewResult,
    LocalDeliveryTarget,
    OutboundDeliveryMaterial,
    OutboundDeliveryPayload,
    OwnerRiskGuard,
    PayloadValidationResult,
    SendOutcome,
    SendResult,
    validate_outbound_payload,
    validate_payload_authority,
)
from .scheduling_store import StateStoreDeliveryScheduler


class PreparedActivationWorker:
    def __init__(
        self,
        *,
        scheduler: StateStoreDeliveryScheduler,
        policy: DeliverySchedulingPolicy,
    ) -> None:
        _dependencies(scheduler, policy)
        self._scheduler = scheduler
        self._policy = policy

    async def run_once(
        self,
        *,
        tenant_id: str,
        global_queued_before: int | None = None,
    ):
        return await self._scheduler.activate_prepared(
            tenant_id=tenant_id,
            policy=self._policy,
            global_queued_before=global_queued_before,
        )


class PreparedActivationCoordinator:
    """Serialize local activation and derive the global watermark from authority."""

    def __init__(
        self,
        *,
        scheduler: StateStoreDeliveryScheduler,
        policy: DeliverySchedulingPolicy,
    ) -> None:
        _dependencies(scheduler, policy)
        self._scheduler = scheduler
        self._policy = policy
        self._lock = asyncio.Lock()

    async def run_once(
        self,
        *,
        tenant_id: str,
    ):
        _text(tenant_id, "activation_coordinator.tenant_id")
        async with self._lock:
            return await self._scheduler.activate_prepared(
                tenant_id=tenant_id,
                policy=self._policy,
            )


class ClaimWorker:
    def __init__(
        self,
        *,
        scheduler: StateStoreDeliveryScheduler,
        policy: DeliverySchedulingPolicy,
        runtime_id: str,
        worker_id: str,
        token_factory: Callable[[], str],
    ) -> None:
        _dependencies(scheduler, policy)
        for value, field in ((runtime_id, "runtime_id"), (worker_id, "worker_id")):
            _text(value, field)
        if not callable(token_factory):
            _invalid("token_factory")
        self._scheduler = scheduler
        self._policy = policy
        self._runtime_id = runtime_id
        self._worker_id = worker_id
        self._tokens = token_factory

    async def run_once(self, *, tenant_id: str) -> ClaimResult:
        token = self._tokens()
        if type(token) is not str or not token:
            _invalid("token_factory.result")
        return await self._scheduler.claim_next(
            tenant_id=tenant_id,
            runtime_id=self._runtime_id,
            worker_id=self._worker_id,
            claim_token=token,
            policy=self._policy,
        )


class LeaseRenewWorker:
    def __init__(
        self,
        *,
        scheduler: StateStoreDeliveryScheduler,
        policy: DeliverySchedulingPolicy,
        risk_guard: OwnerRiskGuard,
    ) -> None:
        _dependencies(scheduler, policy)
        if not isinstance(risk_guard, OwnerRiskGuard):
            _invalid("risk_guard")
        self._scheduler = scheduler
        self._policy = policy
        self._risk_guard = risk_guard

    async def run_once(
        self,
        *,
        claim: DeliveryClaim,
    ) -> LeaseRenewResult:
        if not isinstance(claim, DeliveryClaim):
            _invalid("renew.claim")
        try:
            delivery = await self._scheduler.renew_owner(
                claim=claim,
                policy=self._policy,
            )
        except NsRuntimeStateStoreError:
            self._risk_guard.mark_at_risk(claim)
            try:
                delivery = await self._scheduler.mark_owner_at_risk(
                    claim=claim,
                    policy=self._policy,
                )
            except Exception:
                delivery = None
            return LeaseRenewResult(
                outcome=LeaseRenewOutcome.AT_RISK,
                delivery=delivery,
            )
        owner = delivery.owner
        if owner is not None and owner.risk is DeliveryOwnerRisk.AT_RISK:
            self._risk_guard.mark_at_risk(claim)
            return LeaseRenewResult(
                outcome=LeaseRenewOutcome.AT_RISK,
                delivery=delivery,
            )
        self._risk_guard.clear(claim)
        return LeaseRenewResult(outcome=LeaseRenewOutcome.RENEWED, delivery=delivery)

    def schedule(self, *, claim: DeliveryClaim, supervisor: TaskSupervisor) -> None:
        if not isinstance(claim, DeliveryClaim) or not isinstance(supervisor, TaskSupervisor):
            _invalid("renew.schedule")
        supervisor.create_task(
            self._renew_loop(claim),
            name=f"p11-lease-renew:{claim.delivery_id}", cancel_order=23,
        )

    async def _renew_loop(self, claim: DeliveryClaim) -> None:
        while True:
            await self._scheduler.wait_for_renewal(policy=self._policy)
            result = await self.run_once(claim=claim)
            if result.outcome is LeaseRenewOutcome.AT_RISK:
                return
            delivery = result.delivery
            if delivery is None or delivery.status not in {
                DeliveryRecordStatus.QUEUED,
                DeliveryRecordStatus.SENDING,
                DeliveryRecordStatus.ACK_WAITING,
            }:
                return


class SendWorker:
    def __init__(
        self,
        *,
        scheduler: StateStoreDeliveryScheduler,
        policy: DeliverySchedulingPolicy,
        target_resolver: DeliveryTargetResolver,
        payload_validator: DeliveryPayloadValidator,
        payload_resolver: DeliveryPayloadResolver,
        transport_writer: DeliveryTransportWriter,
        risk_guard: OwnerRiskGuard,
        attempt_id_factory: Callable[[], str],
        clock: Clock,
    ) -> None:
        _dependencies(scheduler, policy)
        for value, expected, field in (
            (target_resolver, DeliveryTargetResolver, "target_resolver"),
            (payload_validator, DeliveryPayloadValidator, "payload_validator"),
            (payload_resolver, DeliveryPayloadResolver, "payload_resolver"),
            (transport_writer, DeliveryTransportWriter, "transport_writer"),
            (risk_guard, OwnerRiskGuard, "risk_guard"),
            (clock, Clock, "clock"),
        ):
            if not isinstance(value, expected):
                _invalid(field)
        if not callable(attempt_id_factory):
            _invalid("attempt_id_factory")
        self._scheduler = scheduler
        self._policy = policy
        self._targets = target_resolver
        self._payload_validation = payload_validator
        self._payloads = payload_resolver
        self._transport = transport_writer
        self._risk_guard = risk_guard
        self._attempt_ids = attempt_id_factory
        self._clock = clock

    async def run_once(self, *, claim: DeliveryClaim) -> SendResult:
        if not isinstance(claim, DeliveryClaim):
            _invalid("send.claim")
        delivery = await self._scheduler.load_claimed(claim=claim)
        if delivery.status is not DeliveryRecordStatus.QUEUED:
            _invalid("send.delivery_status")
        if self._risk_guard.is_at_risk(claim) or (
            delivery.owner is not None
            and delivery.owner.risk is DeliveryOwnerRisk.AT_RISK
        ):
            released = await self._release_if_queued(claim, delivery)
            return SendResult(
                outcome=SendOutcome.OWNER_RISK,
                delivery=released,
                failure=DeliveryWriteFailure.OWNER_AT_RISK,
            )
        if delivery.activation is None:
            _invalid("send.activation")
        if delivery.policy_decision.expires_at <= self._clock.utc_now():
            return await self._precheck_failure(
                claim,
                delivery,
                DeliveryWriteFailure.DELIVERY_EXPIRED,
            )
        try:
            target = await self._targets.resolve(delivery)
        except asyncio.CancelledError:
            raise
        except Exception:
            return await self._precheck_failure(
                claim,
                delivery,
                DeliveryWriteFailure.TARGET_DISCONNECTED,
            )
        if type(target) is not LocalDeliveryTarget or not target.active:
            return await self._precheck_failure(
                claim,
                delivery,
                DeliveryWriteFailure.TARGET_DISCONNECTED,
            )
        if not _target_matches(delivery, target):
            return await self._precheck_failure(
                claim,
                delivery,
                DeliveryWriteFailure.TARGET_IDENTITY_MISMATCH,
            )
        try:
            validation = await self._payload_validation.validate(delivery)
        except asyncio.CancelledError:
            raise
        except Exception:
            return await self._precheck_failure(
                claim,
                delivery,
                DeliveryWriteFailure.PAYLOAD_INVALID,
            )
        if type(validation) is not PayloadValidationResult or not validate_payload_authority(
            delivery,
            validation,
        ):
            return await self._precheck_failure(
                claim,
                delivery,
                DeliveryWriteFailure.PAYLOAD_INVALID,
            )
        try:
            material = await self._payloads.resolve(delivery)
        except asyncio.CancelledError:
            raise
        except Exception:
            return await self._precheck_failure(
                claim,
                delivery,
                DeliveryWriteFailure.PAYLOAD_INVALID,
            )
        if type(material) is not OutboundDeliveryMaterial or (
            material.evidence_fingerprint
            != delivery.payload_evidence.evidence_fingerprint
        ):
            return await self._precheck_failure(
                claim,
                delivery,
                DeliveryWriteFailure.PAYLOAD_INVALID,
            )
        attempt_id = self._attempt_ids()
        if type(attempt_id) is not str or not attempt_id:
            _invalid("attempt_id_factory.result")
        transition = await self._scheduler.start_sending(
            claim=claim,
            attempt_id=attempt_id,
            policy=self._policy,
        )
        try:
            payload = _build_outbound_payload(transition.delivery, material)
        except Exception:
            failed = await self._scheduler.complete_write_failure(
                claim=claim, failure=DeliveryWriteFailure.PAYLOAD_INVALID,
            )
            return SendResult(
                outcome=SendOutcome.WRITE_FAILED, delivery=failed,
                failure=DeliveryWriteFailure.PAYLOAD_INVALID,
            )
        if not validate_outbound_payload(transition.delivery, payload):
            _invalid("send.outbound_binding")
        try:
            write_result = await asyncio.wait_for(
                self._transport.write(target=target, payload=payload),
                timeout=self._policy.write_timeout_seconds,
            )
            if write_result is not None:
                raise RuntimeError("transport writer returned a value")
        except asyncio.CancelledError:
            try:
                await asyncio.shield(self._scheduler.complete_write_failure(
                    claim=claim,
                    failure=DeliveryWriteFailure.SHUTDOWN_INTERRUPTED,
                ))
            except Exception:
                pass
            raise
        except asyncio.TimeoutError:
            failed = await self._scheduler.complete_write_failure(
                claim=claim,
                failure=DeliveryWriteFailure.TRANSPORT_WRITE_TIMEOUT,
            )
            return SendResult(
                outcome=SendOutcome.WRITE_FAILED,
                delivery=failed,
                failure=DeliveryWriteFailure.TRANSPORT_WRITE_TIMEOUT,
            )
        except Exception:
            failed = await self._scheduler.complete_write_failure(
                claim=claim,
                failure=DeliveryWriteFailure.TRANSPORT_WRITE_FAILED,
            )
            return SendResult(
                outcome=SendOutcome.WRITE_FAILED,
                delivery=failed,
                failure=DeliveryWriteFailure.TRANSPORT_WRITE_FAILED,
            )
        try:
            ack_waiting = await self._scheduler.complete_write_success(claim=claim)
        except NsRuntimeStateStoreError:
            uncertain = await self._scheduler.mark_write_uncertain(claim=claim)
            return SendResult(
                outcome=SendOutcome.WRITE_FAILED, delivery=uncertain,
                failure=DeliveryWriteFailure.AUTHORITY_CONFLICT_AFTER_WRITE,
            )
        return SendResult(
            outcome=SendOutcome.ACK_WAITING,
            delivery=ack_waiting,
        )

    async def _precheck_failure(
        self,
        claim: DeliveryClaim,
        delivery,
        failure: DeliveryWriteFailure,
    ) -> SendResult:
        released = await self._scheduler.fail_precheck(claim=claim, failure=failure)
        return SendResult(
            outcome=SendOutcome.PRECHECK_FAILED,
            delivery=released,
            failure=failure,
        )

    async def _release_if_queued(self, claim: DeliveryClaim, delivery):
        if delivery.status is DeliveryRecordStatus.QUEUED and delivery.owner is not None:
            return await self._scheduler.fail_precheck(
                claim=claim, failure=DeliveryWriteFailure.OWNER_AT_RISK,
            )
        return delivery


def _build_outbound_payload(
    delivery, material: OutboundDeliveryMaterial,
) -> OutboundDeliveryPayload:
    authority = delivery.envelope_authority
    binding = delivery.binding
    evidence = delivery.payload_evidence
    payload_values = material.payload.to_dict()
    if evidence.kind.value == "inline":
        if material.payload.mode != "inline":
            _invalid("outbound.payload_mode")
        inline = payload_values["inline"]
        if evidence.media_type == "application/octet-stream":
            if (
                not isinstance(inline, dict)
                or set(inline) != {"encoding", "data"}
                or inline.get("encoding") != "base64"
                or type(inline.get("data")) is not str
            ):
                _invalid("outbound.binary_encoding")
            try:
                body = base64.b64decode(inline["data"], validate=True)
            except (ValueError, TypeError):
                _invalid("outbound.binary_encoding")
        else:
            body = json.dumps(
                inline, sort_keys=True, separators=(",", ":"),
                ensure_ascii=False, allow_nan=False,
            ).encode("utf-8")
        if (len(body) != evidence.size_bytes
                or "sha256:" + hashlib.sha256(body).hexdigest() != evidence.digest):
            _invalid("outbound.payload_digest")
    else:
        reference = payload_values.get("payload_ref")
        if material.payload.mode != "reference" or not isinstance(reference, dict):
            _invalid("outbound.payload_mode")
        if (reference.get("object_id") != evidence.object_id
                or reference.get("version") != evidence.object_version
                or reference.get("checksum") != evidence.checksum):
            _invalid("outbound.payload_reference")
    identity_digest = "sha256:" + hashlib.sha256(
        authority.source_identity.encode("utf-8")
    ).hexdigest()
    capabilities_digest = "sha256:" + hashlib.sha256(
        "\0".join(sorted(binding.required_capabilities)).encode("utf-8")
    ).hexdigest()
    envelope = Envelope(
        protocol=ProtocolGroup(major=1, minor=0, patch=0),
        message=MessageGroup(
            message_id=delivery.message_id,
            type=authority.message_type,
            category="task",
            priority={"low": -10, "normal": 0, "high": 10, "critical": 20}[
                delivery.policy_decision.priority.value
            ],
            created_at=delivery.created_at.isoformat(),
            expires_at=delivery.policy_decision.expires_at.isoformat(),
            reliability=delivery.policy_decision.reliability.value,
        ),
        source=SourceGroup(
            runtime_id=binding.runtime_id,
            connection_id=authority.authorization_binding_reference,
            identity_digest=identity_digest,
            tenant_id=delivery.tenant_id,
            component_type="runtime",
            capabilities_digest=capabilities_digest,
        ),
        target=TargetGroup(
            kind="connection", connection_id=binding.connection_id,
            connection_epoch=binding.connection_epoch,
            tenant_id=binding.tenant_id,
            capabilities=tuple(sorted(binding.required_capabilities)) or None,
            component_type=binding.component_type,
            rebind_policy=binding.binding_rebind_policy.value,
        ),
        delivery=DeliveryGroup(
            delivery_id=delivery.delivery_id,
            attempt=delivery.attempt_count,
            summary_id=delivery.summary_id,
            ack_timeout_ms=delivery.policy_decision.ack_timeout_seconds * 1000,
        ),
        auth_context=AuthContextGroup(
            permission_snapshot_ref=authority.permission_snapshot_ref,
            permission_digest=authority.iam_decision_reference,
            iam_mode=authority.iam_decision_version,
            issued_at=delivery.created_at.isoformat(),
            expires_at=delivery.policy_decision.expires_at.isoformat(),
        ),
        payload=material.payload,
        trace=TraceGroup(**authority.trace.to_wire()),
    )
    raw = canonical_serialize(envelope)
    return OutboundDeliveryPayload(
        envelope=envelope, canonical_bytes=raw,
        envelope_digest=canonical_checksum(envelope),
        evidence_fingerprint=material.evidence_fingerprint,
    )


def _target_matches(delivery, target: LocalDeliveryTarget) -> bool:
    binding = delivery.binding
    return (
        target.runtime_id == binding.runtime_id
        and target.connection_id == binding.connection_id
        and target.session_id == binding.session_id
        and target.connection_epoch == binding.connection_epoch
        and target.tenant_id == binding.tenant_id
        and target.identity == binding.identity_reference.value
    )


def _dependencies(
    scheduler: StateStoreDeliveryScheduler,
    policy: DeliverySchedulingPolicy,
) -> None:
    if not isinstance(scheduler, StateStoreDeliveryScheduler):
        _invalid("scheduler")
    if not isinstance(policy, DeliverySchedulingPolicy):
        _invalid("policy")


def _text(value: object, field: str) -> None:
    if type(value) is not str or not value:
        _invalid(field)


def _invalid(field: str):
    raise NsValidationError(
        "P11 worker dependency or state is invalid.",
        details={"component": "delivery_worker", "field": field},
    )


__all__ = (
    "ClaimWorker", "LeaseRenewWorker", "PreparedActivationCoordinator",
    "PreparedActivationWorker", "SendWorker",
)
