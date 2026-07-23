# -*- coding: utf-8 -*-
"""P11 local scheduling contracts; ACK and retry semantics are absent."""

from __future__ import annotations

import hashlib
import hmac
import json
import math
import secrets
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from ns_common.exceptions import NsValidationError
from ns_runtime.protocol import (
    Envelope, MessageGroup, PayloadGroup, ProtocolGroup, canonical_checksum,
    canonical_serialize,
)

from .models import (
    AUTHORITY_LAYOUT_GENERATION,
    AUTHORITY_LAYOUT_VERSION,
    MAX_ACTIVATION_BATCH_SIZE,
    DeliveryAttempt,
    DeliveryRecord,
    DeliveryWriteFailure,
    PayloadKind,
)


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
    WRITE_UNCERTAIN = "write_uncertain"
    OWNER_RISK = "owner_risk"
    WRITE_OUTCOME_UNKNOWN = "write_outcome_unknown"


class DeliveryTransportWriteState(str, Enum):
    NOT_STARTED = "not_started"
    UNCERTAIN = "uncertain"
    SUCCEEDED = "succeeded"


@dataclass(frozen=True, slots=True, kw_only=True)
class DeliveryTransportWriteResult:
    state: DeliveryTransportWriteState
    failure: DeliveryWriteFailure | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.state, DeliveryTransportWriteState):
            _invalid("transport_write_result.state")
        if self.state is DeliveryTransportWriteState.SUCCEEDED:
            if self.failure is not None:
                _invalid("transport_write_result.success")
        elif not isinstance(self.failure, DeliveryWriteFailure):
            _invalid("transport_write_result.failure")


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
    authority_bucket_count: int = 8
    activation_scan_budget: int = 1000
    authority_layout_version: str = AUTHORITY_LAYOUT_VERSION
    authority_layout_generation: int = AUTHORITY_LAYOUT_GENERATION

    def __post_init__(self) -> None:
        for name in ("config_version", "policy_version", "authority_layout_version"):
            if type(getattr(self, name)) is not str or not getattr(self, name):
                _invalid(f"policy.{name}")
        for name in (
            "activation_batch_size", "global_queued_high_watermark",
            "tenant_queued_high_watermark",
            "target_queued_high_watermark", "max_renew_failures",
            "authority_bucket_count", "activation_scan_budget",
            "authority_layout_generation",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                _invalid(f"policy.{name}")
        if self.activation_batch_size > MAX_ACTIVATION_BATCH_SIZE:
            _invalid("policy.activation_batch_size")
        if self.authority_layout_version != AUTHORITY_LAYOUT_VERSION:
            _invalid("policy.authority_layout_version")
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

    @classmethod
    def from_runtime_config(
        cls, value, *, config_version: str, policy_version: str,
    ) -> "DeliverySchedulingPolicy":
        from ns_common.config import NsRuntimeDeliveryConfig
        if type(value) is not NsRuntimeDeliveryConfig:
            _invalid("policy.runtime_config")
        return cls(
            config_version=config_version,
            policy_version=policy_version,
            activation_batch_size=value.activation_batch_size,
            global_queued_high_watermark=value.global_queued_high_watermark,
            tenant_queued_high_watermark=value.tenant_queued_high_watermark,
            target_queued_high_watermark=value.target_queued_high_watermark,
            lease_ttl_seconds=value.lease_ttl_seconds,
            renew_interval_seconds=value.lease_renew_interval_seconds,
            max_renew_failures=value.lease_max_renew_failures,
            owner_risk_window_seconds=value.owner_risk_window_seconds,
            write_timeout_seconds=value.write_timeout_seconds,
            authority_bucket_count=value.authority_bucket_count,
            activation_scan_budget=value.activation_scan_budget,
            authority_layout_version=value.authority_layout_version,
            authority_layout_generation=value.authority_layout_generation,
        )


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
    waiting: int = 0
    expired: int = 0
    payload_rejected: int = 0
    write_uncertain: int = 0

    def __post_init__(self) -> None:
        _text(self.tenant_id, "resource_counts.tenant_id")
        for name in (
            "prepared", "queued", "sending", "ack_waiting", "write_failed",
            "waiting", "expired", "payload_rejected", "write_uncertain",
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
    fencing: int
    owner_epoch: int
    authority_bucket_count: int
    authority_bucket_id: int
    authority_layout_version: str = AUTHORITY_LAYOUT_VERSION
    authority_layout_generation: int = AUTHORITY_LAYOUT_GENERATION

    def __post_init__(self) -> None:
        for name in ("tenant_id", "delivery_id", "runtime_id", "worker_id", "claim_token"):
            _text(getattr(self, name), f"claim.{name}")
        if isinstance(self.fencing, bool) or not isinstance(self.fencing, int) or self.fencing <= 0:
            _invalid("claim.fencing")
        for name in ("owner_epoch", "authority_bucket_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                _invalid(f"claim.{name}")
        _nonnegative(self.authority_bucket_id, "claim.authority_bucket_id")
        if self.authority_bucket_id >= self.authority_bucket_count:
            _invalid("claim.authority_bucket_id")
        if self.authority_layout_version != AUTHORITY_LAYOUT_VERSION:
            _invalid("claim.authority_layout_version")
        if (
            isinstance(self.authority_layout_generation, bool)
            or not isinstance(self.authority_layout_generation, int)
            or self.authority_layout_generation <= 0
        ):
            _invalid("claim.authority_layout_generation")


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


class _PayloadAccessEvidenceIssuer:
    """One validator-owned capability bound to its exact production IAM client."""

    __slots__ = ("_iam", "_clock", "_key", "_pending_token")

    def __init__(self, *, iam_client: object, clock: object) -> None:
        from ns_common.time import Clock
        from ns_runtime.iam.client import IamClient

        if (
            type(iam_client) is not IamClient
            or not iam_client._is_production_adapter()
            or not isinstance(clock, Clock)
        ):
            _invalid("payload_access_issuer.composition")
        self._iam = iam_client
        self._clock = clock
        self._key = secrets.token_bytes(32)
        self._pending_token: object | None = None

    def issue(
        self,
        *,
        request: object,
        decision: object,
        delivery: DeliveryRecord,
        target: object,
    ) -> "PayloadAccessDecisionEvidence | None":
        from ns_common.iam import (
            PayloadRefRevalidationDecision,
            PayloadRefRevalidationRequest,
        )

        if (
            not self._iam._is_production_adapter()
            or type(request) is not PayloadRefRevalidationRequest
            or type(decision) is not PayloadRefRevalidationDecision
            or not self._iam._consume_payload_revalidation(
                request=request,
                decision=decision,
            )
            or not isinstance(delivery, DeliveryRecord)
            or type(target) is not LocalDeliveryTarget
        ):
            _invalid("payload_access_issuer.result")
        evidence = delivery.payload_evidence
        now = self._clock.utc_now()
        expires_at = min(decision.expires_at, delivery.policy_decision.expires_at)
        if not (
            evidence.kind is PayloadKind.REFERENCE
            and evidence.object_id is not None
            and evidence.object_version is not None
            and request.object_id == evidence.object_id
            and request.version == evidence.object_version
            and request.checksum == evidence.checksum
            and request.size_bytes == evidence.size_bytes
            and request.tenant_id == delivery.tenant_id
            and request.target_principal == target.identity
            and request.target_tenant_id == target.tenant_id
            and request.target_fingerprint == delivery.target_fingerprint
            and request.permission_snapshot_ref
            == target.permission_snapshot_reference
            and request.permission_version == target.permission_version
            and request.admission_authority_reference
            == delivery.policy_decision.request_fingerprint
            and decision.valid
            and decision.allowed
            and not decision.refresh_required
            and decision.object_id == request.object_id
            and decision.version == request.version
            and decision.checksum == request.checksum
            and decision.size_bytes == request.size_bytes
            and decision.tenant_id == request.tenant_id
            and decision.target_principal == request.target_principal
            and decision.target_fingerprint == request.target_fingerprint
            and decision.permission_snapshot_ref
            == request.permission_snapshot_ref
            and decision.permission_version == request.permission_version
            and decision.decided_at <= now < expires_at
        ):
            return None
        request_fingerprint = payload_access_decision_request_fingerprint(
            delivery,
            target=target,
        )
        values = {
            "allowed": True,
            "request_fingerprint": request_fingerprint,
            "object_id": evidence.object_id,
            "object_version": evidence.object_version,
            "checksum": evidence.checksum,
            "size_bytes": evidence.size_bytes,
            "tenant_id": delivery.tenant_id,
            "target_fingerprint": delivery.target_fingerprint,
            "admission_authority_reference": (
                delivery.policy_decision.request_fingerprint
            ),
            "permission_snapshot_reference": (
                target.permission_snapshot_reference
            ),
            "permission_snapshot_fingerprint": (
                target.access_decision_reference
            ),
            "iam_decision_reference": decision.decision_reference,
            "iam_decision_version": decision.permission_version,
            "validated_at": decision.decided_at,
            "expires_at": expires_at,
        }
        evidence_fingerprint = payload_access_evidence_fingerprint(
            **values,
        )
        token = object()
        self._pending_token = token
        try:
            return PayloadAccessDecisionEvidence(
                evidence_fingerprint=evidence_fingerprint,
                **values,
                _issuer=self,
                _construction_token=token,
            )
        finally:
            self._pending_token = None

    def _consume_construction_token(self, token: object) -> bool:
        return token is not None and self._pending_token is token

    def _verify(self, evidence: "PayloadAccessDecisionEvidence") -> bool:
        return bool(
            self._iam._is_production_adapter()
            and hmac.compare_digest(
                evidence._authority_signature,
                _payload_access_authority_signature(evidence, issuer=self),
            )
        )

    def __copy__(self) -> "_PayloadAccessEvidenceIssuer":
        _invalid("payload_access_issuer.copy")

    def __deepcopy__(
        self,
        memo: dict[int, object],
    ) -> "_PayloadAccessEvidenceIssuer":
        del memo
        _invalid("payload_access_issuer.copy")


@dataclass(frozen=True, slots=True, kw_only=True, init=False)
class PayloadAccessDecisionEvidence:
    allowed: bool
    evidence_fingerprint: str
    request_fingerprint: str
    object_id: str
    object_version: str
    checksum: str
    size_bytes: int
    tenant_id: str = field(repr=False)
    target_fingerprint: str
    admission_authority_reference: str = field(repr=False)
    permission_snapshot_reference: str = field(repr=False)
    permission_snapshot_fingerprint: str = field(repr=False)
    iam_decision_reference: str = field(repr=False)
    iam_decision_version: str = field(repr=False)
    validated_at: datetime
    expires_at: datetime
    _authority_seal: object = field(init=False, repr=False, compare=False)
    _authority_signature: bytes = field(init=False, repr=False, compare=False)

    def __init__(
        self,
        *,
        allowed: bool,
        evidence_fingerprint: str,
        request_fingerprint: str,
        object_id: str,
        object_version: str,
        checksum: str,
        size_bytes: int,
        tenant_id: str,
        target_fingerprint: str,
        admission_authority_reference: str,
        permission_snapshot_reference: str,
        permission_snapshot_fingerprint: str,
        iam_decision_reference: str,
        iam_decision_version: str,
        validated_at: datetime,
        expires_at: datetime,
        _issuer: object | None = None,
        _construction_token: object | None = None,
    ) -> None:
        if (
            type(self) is not PayloadAccessDecisionEvidence
            or type(_issuer) is not _PayloadAccessEvidenceIssuer
            or not _issuer._consume_construction_token(_construction_token)
        ):
            _invalid("payload_access.issuer")
        for name, value in (
            ("allowed", allowed),
            ("evidence_fingerprint", evidence_fingerprint),
            ("request_fingerprint", request_fingerprint),
            ("object_id", object_id),
            ("object_version", object_version),
            ("checksum", checksum),
            ("size_bytes", size_bytes),
            ("tenant_id", tenant_id),
            ("target_fingerprint", target_fingerprint),
            ("admission_authority_reference", admission_authority_reference),
            ("permission_snapshot_reference", permission_snapshot_reference),
            ("permission_snapshot_fingerprint", permission_snapshot_fingerprint),
            ("iam_decision_reference", iam_decision_reference),
            ("iam_decision_version", iam_decision_version),
            ("validated_at", validated_at),
            ("expires_at", expires_at),
            ("_authority_seal", _issuer),
            ("_authority_signature", b""),
        ):
            object.__setattr__(self, name, value)
        self.__post_init__()
        object.__setattr__(
            self,
            "_authority_signature",
            _payload_access_authority_signature(self, issuer=_issuer),
        )

    def __post_init__(self) -> None:
        if type(self.allowed) is not bool:
            _invalid("payload_access.allowed")
        for name in (
            "evidence_fingerprint", "request_fingerprint", "object_id",
            "object_version", "checksum", "target_fingerprint",
            "tenant_id", "admission_authority_reference",
            "permission_snapshot_reference", "iam_decision_reference",
            "permission_snapshot_fingerprint", "iam_decision_version",
        ):
            _text(getattr(self, name), f"payload_access.{name}")
        _nonnegative(self.size_bytes, "payload_access.size_bytes")
        validated_at = utc(self.validated_at, "payload_access.validated_at")
        expires_at = utc(self.expires_at, "payload_access.expires_at")
        if expires_at <= validated_at:
            _invalid("payload_access.expires_at")
        object.__setattr__(self, "validated_at", validated_at)
        object.__setattr__(self, "expires_at", expires_at)
        if self.evidence_fingerprint != payload_access_evidence_fingerprint(
            allowed=self.allowed,
            request_fingerprint=self.request_fingerprint,
            object_id=self.object_id,
            object_version=self.object_version,
            checksum=self.checksum,
            size_bytes=self.size_bytes,
            tenant_id=self.tenant_id,
            target_fingerprint=self.target_fingerprint,
            admission_authority_reference=self.admission_authority_reference,
            permission_snapshot_reference=self.permission_snapshot_reference,
            permission_snapshot_fingerprint=self.permission_snapshot_fingerprint,
            iam_decision_reference=self.iam_decision_reference,
            iam_decision_version=self.iam_decision_version,
            validated_at=self.validated_at,
            expires_at=self.expires_at,
        ):
            _invalid("payload_access.evidence_fingerprint")

    def is_production_authority(self) -> bool:
        return (
            type(self) is PayloadAccessDecisionEvidence
            and type(self._authority_seal) is _PayloadAccessEvidenceIssuer
            and self._authority_seal._verify(self)
        )

    def __copy__(self) -> "PayloadAccessDecisionEvidence":
        del self
        _invalid("payload_access.copy")

    def __deepcopy__(
        self,
        memo: dict[int, object],
    ) -> "PayloadAccessDecisionEvidence":
        del self, memo
        _invalid("payload_access.copy")

def _payload_access_authority_signature(
    evidence: PayloadAccessDecisionEvidence,
    *,
    issuer: _PayloadAccessEvidenceIssuer,
) -> bytes:
    payload = json.dumps({
        "allowed": evidence.allowed,
        "evidence_fingerprint": evidence.evidence_fingerprint,
        "request_fingerprint": evidence.request_fingerprint,
        "object_id": evidence.object_id,
        "object_version": evidence.object_version,
        "checksum": evidence.checksum,
        "size_bytes": evidence.size_bytes,
        "tenant_id": evidence.tenant_id,
        "target_fingerprint": evidence.target_fingerprint,
        "admission_authority_reference": (
            evidence.admission_authority_reference
        ),
        "permission_snapshot_reference": (
            evidence.permission_snapshot_reference
        ),
        "permission_snapshot_fingerprint": (
            evidence.permission_snapshot_fingerprint
        ),
        "iam_decision_reference": evidence.iam_decision_reference,
        "iam_decision_version": evidence.iam_decision_version,
        "validated_at": evidence.validated_at.isoformat(),
        "expires_at": evidence.expires_at.isoformat(),
    }, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hmac.new(
        issuer._key,
        payload,
        hashlib.sha256,
    ).digest()


@dataclass(frozen=True, slots=True, kw_only=True)
class PayloadValidationResult:
    valid: bool
    evidence_fingerprint: str
    object_id: str | None
    object_version: str | None
    checksum: str
    tenant_id: str = field(repr=False)
    request_binding_fingerprint: str
    target_binding_fingerprint: str
    access_decision_evidence: PayloadAccessDecisionEvidence | None = field(
        default=None,
        repr=False,
    )

    def __post_init__(self) -> None:
        if type(self.valid) is not bool:
            _invalid("payload_validation.valid")
        for name in (
            "evidence_fingerprint", "checksum", "tenant_id",
            "request_binding_fingerprint", "target_binding_fingerprint",
        ):
            _text(getattr(self, name), f"payload_validation.{name}")
        if self.object_id is not None:
            _text(self.object_id, "payload_validation.object_id")
        if self.object_version is not None:
            _text(self.object_version, "payload_validation.object_version")
        if (
            self.access_decision_evidence is not None
            and type(self.access_decision_evidence)
            is not PayloadAccessDecisionEvidence
        ):
            _invalid("payload_validation.access_decision_evidence")


@dataclass(frozen=True, slots=True, kw_only=True)
class OutboundDeliveryMaterial:
    payload: PayloadGroup = field(repr=False)
    evidence_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.payload, PayloadGroup):
            _invalid("outbound_material.payload")
        _text(self.evidence_fingerprint, "outbound_material.evidence_fingerprint")


@dataclass(frozen=True, slots=True, kw_only=True)
class OutboundDeliveryPayload:
    envelope: Envelope = field(repr=False)
    canonical_bytes: bytes = field(repr=False)
    envelope_digest: str
    evidence_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.envelope, Envelope) or not isinstance(self.canonical_bytes, bytes):
            _invalid("outbound_payload.envelope")
        if self.canonical_bytes != canonical_serialize(self.envelope):
            _invalid("outbound_payload.canonical_bytes")
        if self.envelope_digest != canonical_checksum(self.envelope):
            _invalid("outbound_payload.envelope_digest")
        _text(self.evidence_fingerprint, "outbound_payload.evidence_fingerprint")


@dataclass(frozen=True, slots=True, kw_only=True)
class LocalDeliveryTarget:
    runtime_id: str
    connection_id: str
    session_id: str
    connection_epoch: int
    tenant_id: str = field(repr=False)
    identity: str = field(repr=False)
    active: bool
    protocol: ProtocolGroup
    protocol_schema_key: str
    access_decision_reference: str = field(repr=False)
    permission_snapshot_reference: str = field(repr=False)
    permission_version: str = field(repr=False)

    def __post_init__(self) -> None:
        for name in (
            "runtime_id", "connection_id", "session_id", "tenant_id", "identity",
            "protocol_schema_key",
            "access_decision_reference",
            "permission_snapshot_reference", "permission_version",
        ):
            _text(getattr(self, name), f"target.{name}")
        _nonnegative(self.connection_epoch, "target.connection_epoch")
        if type(self.active) is not bool:
            _invalid("target.active")
        if type(self.protocol) is not ProtocolGroup:
            _invalid("target.protocol")


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
    async def validate(
        self, delivery: DeliveryRecord, *, target: LocalDeliveryTarget,
    ) -> PayloadValidationResult:
        raise NotImplementedError


class DeliveryPayloadResolver(ABC):
    @abstractmethod
    async def resolve(self, delivery: DeliveryRecord) -> OutboundDeliveryMaterial:
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
    ) -> DeliveryTransportWriteResult:
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
    *,
    target: LocalDeliveryTarget,
    now: datetime,
) -> bool:
    if (not isinstance(delivery, DeliveryRecord)
            or not isinstance(result, PayloadValidationResult)
            or not isinstance(target, LocalDeliveryTarget)):
        _invalid("payload_authority")
    evidence = delivery.payload_evidence
    if (
        not result.valid
        or result.evidence_fingerprint != evidence.evidence_fingerprint
        or result.checksum != evidence.checksum
        or result.tenant_id != delivery.tenant_id
        or result.request_binding_fingerprint
        != delivery.policy_decision.request_fingerprint
        or result.target_binding_fingerprint != delivery.target_fingerprint
    ):
        return False
    if evidence.kind is PayloadKind.REFERENCE:
        access = result.access_decision_evidence
        current = utc(now, "payload_authority.now")
        return (
            result.object_id == evidence.object_id
            and result.object_version == evidence.object_version
            and type(access) is PayloadAccessDecisionEvidence
            and access.is_production_authority()
            and access.allowed
            and access.request_fingerprint
            == payload_access_decision_request_fingerprint(delivery, target=target)
            and access.object_id == evidence.object_id
            and access.object_version == evidence.object_version
            and access.checksum == evidence.checksum
            and access.size_bytes == evidence.size_bytes
            and access.tenant_id == delivery.tenant_id
            and access.target_fingerprint == delivery.target_fingerprint
            and access.admission_authority_reference
            == delivery.policy_decision.request_fingerprint
            and access.permission_snapshot_reference
            == target.permission_snapshot_reference
            and access.permission_snapshot_fingerprint
            == target.access_decision_reference
            and access.iam_decision_version == target.permission_version
            and access.validated_at <= current < access.expires_at
            and evidence.expires_at is not None
            and current < evidence.expires_at
        )
    return (
        result.object_id is None
        and result.object_version is None
        and result.access_decision_evidence is None
    )


def payload_access_decision_request_fingerprint(
    delivery: DeliveryRecord, *, target: LocalDeliveryTarget,
) -> str:
    """Bind one real-time object access decision to this send request."""

    if not isinstance(delivery, DeliveryRecord) or not isinstance(target, LocalDeliveryTarget):
        _invalid("payload_access_decision_request")
    evidence = delivery.payload_evidence
    raw = json.dumps({
        "object_id": evidence.object_id,
        "object_version": evidence.object_version,
        "checksum": evidence.checksum,
        "size_bytes": evidence.size_bytes,
        "tenant_id": delivery.tenant_id,
        "admission_authority_reference": delivery.policy_decision.request_fingerprint,
        "request_binding_fingerprint": delivery.policy_decision.request_fingerprint,
        "target_binding_fingerprint": delivery.target_fingerprint,
        "target_runtime_id": target.runtime_id,
        "target_connection_id": target.connection_id,
        "target_session_id": target.session_id,
        "target_connection_epoch": target.connection_epoch,
        "target_tenant_id": target.tenant_id,
        "target_identity": target.identity,
        "current_permission_snapshot_reference": target.permission_snapshot_reference,
        "current_permission_version": target.permission_version,
        "current_permission_snapshot_fingerprint": target.access_decision_reference,
    }, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def payload_access_evidence_fingerprint(
    *,
    allowed: bool,
    request_fingerprint: str,
    object_id: str,
    object_version: str,
    checksum: str,
    size_bytes: int,
    tenant_id: str,
    target_fingerprint: str,
    admission_authority_reference: str,
    permission_snapshot_reference: str,
    permission_snapshot_fingerprint: str,
    iam_decision_reference: str,
    iam_decision_version: str,
    validated_at: datetime,
    expires_at: datetime,
) -> str:
    raw = json.dumps({
        "allowed": allowed,
        "request_fingerprint": request_fingerprint,
        "object_id": object_id,
        "object_version": object_version,
        "checksum": checksum,
        "size_bytes": size_bytes,
        "tenant_id": tenant_id,
        "target_fingerprint": target_fingerprint,
        "admission_authority_reference": admission_authority_reference,
        "permission_snapshot_reference": permission_snapshot_reference,
        "permission_snapshot_fingerprint": permission_snapshot_fingerprint,
        "iam_decision_reference": iam_decision_reference,
        "iam_decision_version": iam_decision_version,
        "validated_at": utc(validated_at, "payload_access.validated_at").isoformat(),
        "expires_at": utc(expires_at, "payload_access.expires_at").isoformat(),
    }, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def validate_outbound_payload(
    delivery: DeliveryRecord,
    payload: OutboundDeliveryPayload,
) -> bool:
    if not isinstance(delivery, DeliveryRecord) or not isinstance(payload, OutboundDeliveryPayload):
        _invalid("outbound_authority")
    return (
        payload.envelope.message.message_id == delivery.message_id
        and payload.envelope.message == policy_message_group(delivery)
        and payload.envelope.source == delivery.envelope_authority.source
        and payload.envelope.auth_context == delivery.envelope_authority.auth_context
        and payload.envelope.trace == delivery.envelope_authority.trace
        and payload.envelope.protocol == delivery.envelope_authority.protocol
        and payload.envelope.delivery is not None
        and payload.envelope.delivery.delivery_id == delivery.delivery_id
        and payload.envelope.delivery.attempt == delivery.attempt_count
        and payload.envelope.target is not None
        and payload.envelope.target.connection_id == delivery.binding.connection_id
        and payload.envelope.target.connection_epoch == delivery.binding.connection_epoch
        and payload.evidence_fingerprint == delivery.payload_evidence.evidence_fingerprint
    )


def policy_message_group(delivery: DeliveryRecord) -> MessageGroup:
    """Preserve stable inbound identity while rebuilding policy authority."""

    if not isinstance(delivery, DeliveryRecord):
        _invalid("policy_message.delivery")
    inbound = delivery.envelope_authority.message
    priority = {
        "low": -10,
        "normal": 0,
        "high": 10,
        "critical": 20,
    }[delivery.policy_decision.priority.value]
    return MessageGroup(
        message_id=inbound.message_id,
        type=inbound.type,
        category=inbound.category,
        priority=priority,
        created_at=inbound.created_at,
        expires_at=delivery.policy_decision.expires_at.isoformat(),
        reliability=delivery.policy_decision.reliability.value,
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
    "DeliveryTransportWriter", "DeliveryTransportWriteResult",
    "DeliveryTransportWriteState",
    "LeaseRenewOutcome", "LeaseRenewResult", "LocalDeliveryTarget",
    "OutboundDeliveryMaterial", "OutboundDeliveryPayload", "OwnerRiskGuard",
    "PayloadAccessDecisionEvidence", "PayloadValidationResult",
    "SendOutcome", "SendResult", "SendingTransition",
    "payload_access_decision_request_fingerprint",
    "payload_access_evidence_fingerprint", "policy_message_group",
    "validate_outbound_payload", "validate_payload_authority",
)
