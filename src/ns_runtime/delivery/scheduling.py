# -*- coding: utf-8 -*-
"""P11 local scheduling contracts; ACK and retry semantics are absent."""

from __future__ import annotations

import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from ns_common.exceptions import NsValidationError

from .models import DeliveryAttempt, DeliveryRecord, DeliveryWriteFailure, PayloadKind


class ActivationSkipReason(str, Enum):
    BATCH_LIMIT = "batch_limit"
    GLOBAL_WATERMARK = "global_watermark"
    TENANT_WATERMARK = "tenant_watermark"
    TARGET_WATERMARK = "target_watermark"
    EXPIRED = "expired"
    NO_PREPARED = "no_prepared"


class ClaimOutcome(str, Enum):
    CLAIMED = "claimed"
    EMPTY = "empty"
    CONTENDED = "contended"


class SendOutcome(str, Enum):
    ACK_WAITING = "ack_waiting"
    PRECHECK_FAILED = "precheck_failed"
    WRITE_FAILED = "write_failed"
    OWNER_RISK = "owner_risk"


class LeaseRenewOutcome(str, Enum):
    RENEWED = "renewed"
    FAILURE_RECORDED = "failure_recorded"
    AT_RISK = "at_risk"


@dataclass(frozen=True, slots=True, kw_only=True)
class DeliverySchedulingPolicy:
    config_version: str
    policy_version: str
    activation_batch_size: int = 200
    global_queued_high_watermark: int = 10_000
    tenant_queued_high_watermark: int = 10_000
    target_queued_high_watermark: int = 256
    lease_ttl_seconds: float = 15.0
    renew_interval_seconds: float = 5.0
    max_renew_failures: int = 2
    owner_risk_window_seconds: float = 4.0
    write_timeout_seconds: float = 10.0

    def __post_init__(self) -> None:
        for name in ("config_version", "policy_version"):
            if type(getattr(self, name)) is not str or not getattr(self, name):
                _invalid(f"policy.{name}")
        for name in (
            "activation_batch_size", "global_queued_high_watermark",
            "tenant_queued_high_watermark",
            "target_queued_high_watermark", "max_renew_failures",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                _invalid(f"policy.{name}")
        for name in (
            "lease_ttl_seconds", "renew_interval_seconds",
            "owner_risk_window_seconds", "write_timeout_seconds",
        ):
            value = getattr(self, name)
            if (
                type(value) not in {int, float}
                or not math.isfinite(float(value))
                or float(value) <= 0
            ):
                _invalid(f"policy.{name}")
        if self.renew_interval_seconds >= self.lease_ttl_seconds:
            _invalid("policy.renew_interval_seconds")
        if self.write_timeout_seconds >= self.lease_ttl_seconds:
            _invalid("policy.write_timeout_seconds")


@dataclass(frozen=True, slots=True, kw_only=True)
class ActivationResult:
    tenant_id: str = field(repr=False)
    candidate_count: int
    activated: tuple[DeliveryRecord, ...]
    queued_before: int
    queued_after: int
    global_queued_before: int
    global_queued_after: int
    skip_reasons: tuple[ActivationSkipReason, ...]
    policy_version: str

    def __post_init__(self) -> None:
        _text(self.tenant_id, "activation_result.tenant_id")
        _nonnegative(self.candidate_count, "activation_result.candidate_count")
        _nonnegative(self.queued_before, "activation_result.queued_before")
        _nonnegative(self.queued_after, "activation_result.queued_after")
        _nonnegative(
            self.global_queued_before,
            "activation_result.global_queued_before",
        )
        _nonnegative(
            self.global_queued_after,
            "activation_result.global_queued_after",
        )
        if not isinstance(self.activated, tuple) or any(
            not isinstance(value, DeliveryRecord) for value in self.activated
        ):
            _invalid("activation_result.activated")
        if not isinstance(self.skip_reasons, tuple) or any(
            not isinstance(value, ActivationSkipReason) for value in self.skip_reasons
        ):
            _invalid("activation_result.skip_reasons")
        _text(self.policy_version, "activation_result.policy_version")
        if self.queued_after != self.queued_before + len(self.activated):
            _invalid("activation_result.queued_count")
        if self.global_queued_after != self.global_queued_before + len(self.activated):
            _invalid("activation_result.global_queued_count")


@dataclass(frozen=True, slots=True, kw_only=True)
class DeliveryResourceCounts:
    tenant_id: str = field(repr=False)
    prepared: int
    queued: int
    sending: int
    ack_waiting: int
    write_failed: int

    def __post_init__(self) -> None:
        _text(self.tenant_id, "resource_counts.tenant_id")
        for name in (
            "prepared", "queued", "sending", "ack_waiting", "write_failed",
        ):
            _nonnegative(getattr(self, name), f"resource_counts.{name}")

    @property
    def active(self) -> int:
        return self.sending

    @property
    def inflight(self) -> int:
        return self.ack_waiting


@dataclass(frozen=True, slots=True, kw_only=True)
class DeliveryClaim:
    tenant_id: str = field(repr=False)
    delivery_id: str = field(repr=False)
    runtime_id: str
    worker_id: str
    claim_token: str = field(repr=False)

    def __post_init__(self) -> None:
        for name in ("tenant_id", "delivery_id", "runtime_id", "worker_id", "claim_token"):
            _text(getattr(self, name), f"claim.{name}")


@dataclass(frozen=True, slots=True, kw_only=True)
class ClaimResult:
    outcome: ClaimOutcome
    claim: DeliveryClaim | None
    delivery: DeliveryRecord | None

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, ClaimOutcome):
            _invalid("claim_result.outcome")
        if self.outcome is ClaimOutcome.CLAIMED:
            if not isinstance(self.claim, DeliveryClaim) or not isinstance(self.delivery, DeliveryRecord):
                _invalid("claim_result.claimed")
            if (
                self.claim.delivery_id != self.delivery.delivery_id
                or self.claim.tenant_id != self.delivery.tenant_id
            ):
                _invalid("claim_result.binding")
        elif self.claim is not None or self.delivery is not None:
            _invalid("claim_result.empty")


@dataclass(frozen=True, slots=True, kw_only=True)
class PayloadValidationResult:
    valid: bool
    evidence_fingerprint: str
    object_id: str | None
    object_version: str | None
    checksum: str
    tenant_id: str = field(repr=False)

    def __post_init__(self) -> None:
        if type(self.valid) is not bool:
            _invalid("payload_validation.valid")
        for name in ("evidence_fingerprint", "checksum", "tenant_id"):
            _text(getattr(self, name), f"payload_validation.{name}")
        if self.object_id is not None:
            _text(self.object_id, "payload_validation.object_id")
        if self.object_version is not None:
            _text(self.object_version, "payload_validation.object_version")


@dataclass(frozen=True, slots=True, kw_only=True)
class OutboundDeliveryPayload:
    wire_text: str = field(repr=False)
    message_id: str
    target_fingerprint: str
    evidence_fingerprint: str
    content_digest: str

    def __post_init__(self) -> None:
        if type(self.wire_text) is not str or not self.wire_text:
            _invalid("outbound_payload.wire_text")
        for name in (
            "message_id", "target_fingerprint", "evidence_fingerprint",
            "content_digest",
        ):
            _text(getattr(self, name), f"outbound_payload.{name}")


@dataclass(frozen=True, slots=True, kw_only=True)
class LocalDeliveryTarget:
    runtime_id: str
    connection_id: str
    session_id: str
    connection_epoch: int
    tenant_id: str = field(repr=False)
    identity: str = field(repr=False)
    active: bool

    def __post_init__(self) -> None:
        for name in ("runtime_id", "connection_id", "session_id", "tenant_id", "identity"):
            _text(getattr(self, name), f"target.{name}")
        _nonnegative(self.connection_epoch, "target.connection_epoch")
        if type(self.active) is not bool:
            _invalid("target.active")


@dataclass(frozen=True, slots=True, kw_only=True)
class SendResult:
    outcome: SendOutcome
    delivery: DeliveryRecord
    failure: DeliveryWriteFailure | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, SendOutcome):
            _invalid("send_result.outcome")
        if not isinstance(self.delivery, DeliveryRecord):
            _invalid("send_result.delivery")
        if self.outcome is SendOutcome.ACK_WAITING:
            if self.failure is not None:
                _invalid("send_result.success_failure")
        elif not isinstance(self.failure, DeliveryWriteFailure):
            _invalid("send_result.failure")


@dataclass(frozen=True, slots=True, kw_only=True)
class SendingTransition:
    delivery: DeliveryRecord
    attempt: DeliveryAttempt

    def __post_init__(self) -> None:
        if not isinstance(self.delivery, DeliveryRecord) or not isinstance(self.attempt, DeliveryAttempt):
            _invalid("sending_transition.values")
        if (
            self.delivery.delivery_id != self.attempt.delivery_id
            or self.delivery.current_attempt_id != self.attempt.attempt_id
            or self.delivery.attempt_count != self.attempt.attempt_number
        ):
            _invalid("sending_transition.binding")


@dataclass(frozen=True, slots=True, kw_only=True)
class LeaseRenewResult:
    outcome: LeaseRenewOutcome
    delivery: DeliveryRecord | None

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, LeaseRenewOutcome):
            _invalid("lease_renew_result.outcome")
        if self.delivery is not None and not isinstance(self.delivery, DeliveryRecord):
            _invalid("lease_renew_result.delivery")
        if self.outcome is not LeaseRenewOutcome.AT_RISK and self.delivery is None:
            _invalid("lease_renew_result.delivery")


class DeliveryPayloadValidator(ABC):
    @abstractmethod
    async def validate(self, delivery: DeliveryRecord) -> PayloadValidationResult:
        raise NotImplementedError


class DeliveryPayloadResolver(ABC):
    @abstractmethod
    async def resolve(self, delivery: DeliveryRecord) -> OutboundDeliveryPayload:
        raise NotImplementedError


class DeliveryTargetResolver(ABC):
    @abstractmethod
    async def resolve(self, delivery: DeliveryRecord) -> LocalDeliveryTarget:
        raise NotImplementedError


class DeliveryTransportWriter(ABC):
    @abstractmethod
    async def write(
        self,
        *,
        target: LocalDeliveryTarget,
        payload: OutboundDeliveryPayload,
    ) -> None:
        raise NotImplementedError


class OwnerRiskGuard:
    """Process-local stop gate; authority state remains in DeliveryRecord."""

    def __init__(self) -> None:
        self._risky_claims: set[str] = set()

    def mark_at_risk(self, claim: DeliveryClaim) -> None:
        if not isinstance(claim, DeliveryClaim):
            _invalid("risk_guard.claim")
        self._risky_claims.add(claim.claim_token)

    def clear(self, claim: DeliveryClaim) -> None:
        if not isinstance(claim, DeliveryClaim):
            _invalid("risk_guard.claim")
        self._risky_claims.discard(claim.claim_token)

    def is_at_risk(self, claim: DeliveryClaim) -> bool:
        if not isinstance(claim, DeliveryClaim):
            _invalid("risk_guard.claim")
        return claim.claim_token in self._risky_claims


def validate_payload_authority(
    delivery: DeliveryRecord,
    result: PayloadValidationResult,
) -> bool:
    if not isinstance(delivery, DeliveryRecord) or not isinstance(result, PayloadValidationResult):
        _invalid("payload_authority")
    evidence = delivery.payload_evidence
    if (
        not result.valid
        or result.evidence_fingerprint != evidence.evidence_fingerprint
        or result.checksum != evidence.checksum
        or result.tenant_id != delivery.tenant_id
    ):
        return False
    if evidence.kind is PayloadKind.REFERENCE:
        return (
            result.object_id == evidence.object_id
            and result.object_version == evidence.object_version
        )
    return result.object_id is None and result.object_version is None


def validate_outbound_payload(
    delivery: DeliveryRecord,
    payload: OutboundDeliveryPayload,
) -> bool:
    if not isinstance(delivery, DeliveryRecord) or not isinstance(payload, OutboundDeliveryPayload):
        _invalid("outbound_authority")
    return (
        payload.message_id == delivery.message_id
        and payload.target_fingerprint == delivery.target_fingerprint
        and payload.evidence_fingerprint == delivery.payload_evidence.evidence_fingerprint
        and payload.content_digest == delivery.payload_evidence.digest
    )


def utc(value: object, field: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        _invalid(field)
    return value.astimezone(timezone.utc)


def _text(value: object, field: str) -> None:
    if type(value) is not str or not value or len(value) > 1024 or "\0" in value:
        _invalid(field)


def _nonnegative(value: object, field: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        _invalid(field)


def _invalid(field: str):
    raise NsValidationError(
        "P11 scheduling contract value is invalid.",
        details={"component": "delivery_scheduling", "field": field},
    )


__all__ = (
    "ActivationResult", "ActivationSkipReason", "ClaimOutcome", "ClaimResult",
    "DeliveryClaim", "DeliveryPayloadResolver", "DeliveryPayloadValidator",
    "DeliveryResourceCounts", "DeliverySchedulingPolicy", "DeliveryTargetResolver",
    "DeliveryTransportWriter",
    "LeaseRenewOutcome", "LeaseRenewResult", "LocalDeliveryTarget",
    "OutboundDeliveryPayload", "OwnerRiskGuard",
    "PayloadValidationResult", "SendOutcome", "SendResult", "SendingTransition",
    "validate_outbound_payload", "validate_payload_authority",
)
