# -*- coding: utf-8 -*-
"""DR-1 immutable delivery admission contracts.

These values are deliberately not wire decoders.  P10 accepts only the typed
RP-1 plan produced by processor stage six and stores only bounded evidence.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from ns_common.exceptions import NsValidationError
from ns_runtime.routing import ResolvedRoutingPlan, RoutingStrategy, SelectedRoutingBinding


LEGACY_DR1_SCHEMA_VERSION = "dr-1"
DR1_SCHEMA_VERSION = "dr-2"
PAYLOAD_EVIDENCE_VERSION = "payload-evidence-1"
DEDUP_EVIDENCE_VERSION = "dedup-evidence-1"
ADMISSION_RESPONSE_VERSION = "delivery-admission-response-1"
ADMISSION_RESULT_VERSION = "delivery-admission-result-1"
ATOMIC_ADMISSION_VERSION = "delivery-admission-atomic-1"
P11_ATTEMPT_SCHEMA_VERSION = "delivery-attempt-1"
P11_ACTIVATION_SCHEMA_VERSION = "delivery-activation-1"
P11_OWNER_SCHEMA_VERSION = "delivery-owner-1"
MAX_ACTIVATION_BATCH_SIZE = 1000
_TEXT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:@/-]{0,511}")
_DIGEST = re.compile(r"sha256:[0-9a-f]{64}")


class DeliverySummaryStatus(str, Enum):
    INITIALIZING = "initializing"
    PENDING = "pending"
    PARTIAL_ACKED = "partial_acked"
    ALL_ACKED = "all_acked"
    PARTIAL_FAILED = "partial_failed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeliveryRecordStatus(str, Enum):
    PREPARED = "prepared"
    QUEUED = "queued"
    SENDING = "sending"
    ACK_WAITING = "ack_waiting"
    WRITE_FAILED = "write_failed"
    EXPIRED = "expired"
    PAYLOAD_REJECTED = "payload_rejected"
    TARGET_WAITING = "target_waiting"
    WRITE_UNCERTAIN = "write_uncertain"
    # Contract placeholder only. P11 has no production transition into retry.
    RETRY_SCHEDULED = "retry_scheduled"
    CANCELLED = "cancelled"


class DeliveryOwnerRisk(str, Enum):
    HEALTHY = "healthy"
    AT_RISK = "at_risk"


class DeliveryAttemptStatus(str, Enum):
    WRITING = "writing"
    WRITE_SUCCEEDED = "write_succeeded"
    WRITE_FAILED = "write_failed"
    WRITE_UNCERTAIN = "write_uncertain"


class DeliveryWriteFailure(str, Enum):
    TARGET_DISCONNECTED = "target_disconnected"
    TARGET_IDENTITY_MISMATCH = "target_identity_mismatch"
    PAYLOAD_INVALID = "payload_invalid"
    DELIVERY_EXPIRED = "delivery_expired"
    POLICY_VERSION_MISMATCH = "policy_version_mismatch"
    OWNER_AT_RISK = "owner_at_risk"
    TRANSPORT_WRITE_FAILED = "transport_write_failed"
    TRANSPORT_WRITE_TIMEOUT = "transport_write_timeout"
    SHUTDOWN_INTERRUPTED = "shutdown_interrupted"
    AUTHORITY_CONFLICT_AFTER_WRITE = "authority_conflict_after_write"


class PayloadKind(str, Enum):
    INLINE = "inline"
    REFERENCE = "payload_ref"


class AdmissionPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"


class AdmissionReliability(str, Enum):
    BEST_EFFORT = "best_effort"
    AT_LEAST_ONCE = "at_least_once"
    CRITICAL = "critical"


class PayloadDependencyDisposition(str, Enum):
    REJECT = "reject"
    WAIT_REQUIRED = "wait_required"
    DEAD_LETTER_REQUIRED = "dead_letter_required"
    DEPENDENCY_UNAVAILABLE = "dependency_unavailable"


class AdmissionOutcome(str, Enum):
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"
    WAIT_REQUIRED = "wait_required"
    DEAD_LETTER_REQUIRED = "dead_letter_required"
    UNAVAILABLE = "unavailable"


class DuplicateLifecycle(str, Enum):
    IN_PROGRESS = "in_progress"
    ACKED = "acked"
    DEAD = "dead"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class RejectionReason(str, Enum):
    EXPIRED = "expired"
    WINDOW_TOO_SHORT = "window_too_short"
    POLICY_REJECTED = "policy_rejected"
    INLINE_TYPE_INVALID = "inline_type_invalid"
    INLINE_TOO_LARGE = "inline_too_large"
    INLINE_TOO_DEEP = "inline_too_deep"
    PAYLOAD_REF_INVALID = "payload_ref_invalid"
    PAYLOAD_REF_UNAUTHORIZED = "payload_ref_unauthorized"
    PAYLOAD_REF_TENANT_MISMATCH = "payload_ref_tenant_mismatch"
    PAYLOAD_REF_UNAVAILABLE = "payload_ref_unavailable"
    INITIALIZATION_FAILED = "initialization_failed"
    NO_TARGET_ACCEPTED = "no_target_accepted"


@dataclass(frozen=True, slots=True, kw_only=True)
class AdmissionTrace:
    trace_id: str
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        _text(self.trace_id, "trace.trace_id")
        if self.correlation_id is not None:
            _text(self.correlation_id, "trace.correlation_id")

    def to_wire(self) -> dict[str, str]:
        result = {"trace_id": self.trace_id}
        if self.correlation_id is not None:
            result["correlation_id"] = self.correlation_id
        return result


@dataclass(frozen=True, slots=True, kw_only=True)
class DeliveryEnvelopeAuthority:
    message_type: str
    source_identity: str = field(repr=False)
    authorization_binding_reference: str = field(repr=False)
    permission_snapshot_ref: str = field(repr=False)
    permission_snapshot_version: str
    iam_decision_reference: str = field(repr=False)
    iam_decision_version: str
    trace: AdmissionTrace

    def __post_init__(self) -> None:
        for name in (
            "message_type", "source_identity", "authorization_binding_reference",
            "permission_snapshot_ref", "permission_snapshot_version",
            "iam_decision_reference", "iam_decision_version",
        ):
            _text(getattr(self, name), f"envelope_authority.{name}")
        if not isinstance(self.trace, AdmissionTrace):
            _invalid("envelope_authority.trace")


@dataclass(frozen=True, slots=True, kw_only=True)
class InlinePayload:
    value: object = field(repr=False)
    media_type: str
    application_limit_bytes: int
    transport_limit_bytes: int

    def __post_init__(self) -> None:
        _text(self.media_type, "inline.media_type")
        _positive(self.application_limit_bytes, "inline.application_limit_bytes")
        _positive(self.transport_limit_bytes, "inline.transport_limit_bytes")
        if self.media_type == "application/octet-stream":
            if not isinstance(self.value, bytes):
                _invalid("inline.value")
        elif self.media_type == "application/json":
            if not _json_root(self.value):
                _invalid("inline.value")
        else:
            _invalid("inline.media_type")


@dataclass(frozen=True, slots=True, kw_only=True)
class PayloadReference:
    object_id: str
    version: str
    checksum: str
    owner_identity: str = field(repr=False)
    callback_message_type: str | None = None

    def __post_init__(self) -> None:
        for name in ("object_id", "version", "checksum", "owner_identity"):
            _text(getattr(self, name), f"payload_ref.{name}")
        if self.callback_message_type is not None:
            _text(self.callback_message_type, "payload_ref.callback_message_type")


@dataclass(frozen=True, slots=True, kw_only=True)
class PayloadEvidence:
    schema_version: str
    kind: PayloadKind
    media_type: str
    size_bytes: int
    digest: str
    checksum: str
    evidence_fingerprint: str
    object_id: str | None = None
    object_version: str | None = None
    tenant_id: str | None = field(default=None, repr=False)
    validated_at: datetime | None = None
    expires_at: datetime | None = None
    body_ref: str | None = field(default=None, repr=False)
    request_binding_fingerprint: str = ""
    target_binding_fingerprint: str = ""

    def __post_init__(self) -> None:
        if self.schema_version != PAYLOAD_EVIDENCE_VERSION:
            _invalid("payload_evidence.schema_version")
        if not isinstance(self.kind, PayloadKind):
            _invalid("payload_evidence.kind")
        _text(self.media_type, "payload_evidence.media_type")
        _nonnegative(self.size_bytes, "payload_evidence.size_bytes")
        _digest(self.digest, "payload_evidence.digest")
        _text(self.checksum, "payload_evidence.checksum")
        _digest(self.evidence_fingerprint, "payload_evidence.evidence_fingerprint")
        _digest(self.request_binding_fingerprint, "payload_evidence.request_binding_fingerprint")
        _digest(self.target_binding_fingerprint, "payload_evidence.target_binding_fingerprint")
        refs = (self.object_id, self.object_version, self.tenant_id,
                self.validated_at, self.expires_at)
        if self.kind is PayloadKind.INLINE:
            if any(value is not None for value in refs):
                _invalid("payload_evidence.inline_reference")
            _text(self.body_ref, "payload_evidence.body_ref")
            if self.checksum != self.digest:
                _invalid("payload_evidence.inline_checksum")
        else:
            if any(value is None for value in refs) or self.body_ref is not None:
                _invalid("payload_evidence.reference_metadata")
            for name in ("object_id", "object_version", "tenant_id"):
                _text(getattr(self, name), f"payload_evidence.{name}")
            object.__setattr__(self, "validated_at", _utc(self.validated_at, "payload_evidence.validated_at"))
            object.__setattr__(self, "expires_at", _utc(self.expires_at, "payload_evidence.expires_at"))
            if self.expires_at <= self.validated_at:  # type: ignore[operator]
                _invalid("payload_evidence.expiry")
        if self.evidence_fingerprint != compute_payload_evidence_fingerprint(
            kind=self.kind, media_type=self.media_type,
            size_bytes=self.size_bytes, digest=self.digest,
            checksum=self.checksum, object_id=self.object_id,
            object_version=self.object_version, tenant_id=self.tenant_id,
            validated_at=self.validated_at, expires_at=self.expires_at,
            body_ref=self.body_ref,
            request_binding_fingerprint=self.request_binding_fingerprint,
            target_binding_fingerprint=self.target_binding_fingerprint,
        ):
            _invalid("payload_evidence.evidence_fingerprint")

    def safe_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "schema_version": self.schema_version,
            "kind": self.kind.value,
            "media_type": self.media_type,
            "size_bytes": self.size_bytes,
            "digest": self.digest,
            "checksum": self.checksum,
            "evidence_fingerprint": self.evidence_fingerprint,
            "request_binding_fingerprint": self.request_binding_fingerprint,
            "target_binding_fingerprint": self.target_binding_fingerprint,
        }
        if self.kind is PayloadKind.REFERENCE:
            result.update({
                "object_id": self.object_id,
                "object_version": self.object_version,
                "tenant_id": self.tenant_id,
                "validated_at": self.validated_at.isoformat(),  # type: ignore[union-attr]
                "expires_at": self.expires_at.isoformat(),  # type: ignore[union-attr]
            })
        else:
            result["body_ref"] = self.body_ref
        return result


@dataclass(frozen=True, slots=True, kw_only=True)
class AdmissionPolicyDecision:
    request_fingerprint: str
    config_version: str
    policy_version: str
    accepted: bool
    priority: AdmissionPriority
    reliability: AdmissionReliability
    expires_at: datetime
    ack_timeout_seconds: int
    target_strategy: RoutingStrategy
    dedup_ttl_seconds: int
    max_inline_bytes: int
    max_json_depth: int
    payload_dependency_disposition: PayloadDependencyDisposition
    fanout_shard_threshold: int
    shard_bucket_size: int
    initialization_batch_size: int
    activation_batch_size: int
    rejection_reason: RejectionReason | None = None

    def __post_init__(self) -> None:
        _digest(self.request_fingerprint, "policy_decision.request_fingerprint")
        _text(self.config_version, "policy_decision.config_version")
        _text(self.policy_version, "policy_decision.policy_version")
        if type(self.accepted) is not bool:
            _invalid("policy_decision.accepted")
        for name, typ in (("priority", AdmissionPriority),
                          ("reliability", AdmissionReliability),
                          ("target_strategy", RoutingStrategy),
                          ("payload_dependency_disposition", PayloadDependencyDisposition)):
            if not isinstance(getattr(self, name), typ):
                _invalid(f"policy_decision.{name}")
        object.__setattr__(self, "expires_at", _utc(self.expires_at, "policy_decision.expires_at"))
        for name in ("ack_timeout_seconds", "dedup_ttl_seconds", "max_inline_bytes", "max_json_depth",
                     "fanout_shard_threshold", "shard_bucket_size",
                     "initialization_batch_size", "activation_batch_size"):
            _positive(getattr(self, name), f"policy_decision.{name}")
        if self.activation_batch_size > MAX_ACTIVATION_BATCH_SIZE:
            _invalid("policy_decision.activation_batch_size")
        if self.accepted is (self.rejection_reason is not None):
            _invalid("policy_decision.rejection_reason")
        if self.rejection_reason is not None and not isinstance(self.rejection_reason, RejectionReason):
            _invalid("policy_decision.rejection_reason")


@dataclass(frozen=True, slots=True, kw_only=True)
class TargetRejection:
    target_fingerprint: str
    reason: RejectionReason

    def __post_init__(self) -> None:
        _digest(self.target_fingerprint, "target_rejection.target_fingerprint")
        if not isinstance(self.reason, RejectionReason):
            _invalid("target_rejection.reason")


@dataclass(frozen=True, slots=True, kw_only=True)
class DeliveryActivationEvidence:
    schema_version: str
    config_version: str
    policy_version: str
    reason: str
    batch_size: int
    candidate_count: int
    activated_at: datetime

    def __post_init__(self) -> None:
        if self.schema_version != P11_ACTIVATION_SCHEMA_VERSION:
            _invalid("activation.schema_version")
        for name in ("config_version", "policy_version", "reason"):
            _text(getattr(self, name), f"activation.{name}")
        _positive(self.batch_size, "activation.batch_size")
        _positive(self.candidate_count, "activation.candidate_count")
        object.__setattr__(self, "activated_at", _utc(self.activated_at, "activation.activated_at"))


@dataclass(frozen=True, slots=True, kw_only=True)
class DeliveryOwner:
    schema_version: str
    runtime_id: str
    worker_id: str
    claim_token: str = field(repr=False)
    claimed_at: datetime
    lease_expires_at: datetime
    renew_failures: int
    risk: DeliveryOwnerRisk
    fencing: int
    risk_since: datetime | None = None
    protection_until: datetime | None = None

    def __post_init__(self) -> None:
        if self.schema_version != P11_OWNER_SCHEMA_VERSION:
            _invalid("owner.schema_version")
        for name in ("runtime_id", "worker_id", "claim_token"):
            _text(getattr(self, name), f"owner.{name}")
        object.__setattr__(self, "claimed_at", _utc(self.claimed_at, "owner.claimed_at"))
        object.__setattr__(self, "lease_expires_at", _utc(self.lease_expires_at, "owner.lease_expires_at"))
        if self.lease_expires_at <= self.claimed_at:
            _invalid("owner.lease_expires_at")
        _nonnegative(self.renew_failures, "owner.renew_failures")
        _positive(self.fencing, "owner.fencing")
        if not isinstance(self.risk, DeliveryOwnerRisk):
            _invalid("owner.risk")
        if self.risk is DeliveryOwnerRisk.HEALTHY:
            if self.risk_since is not None or self.protection_until is not None:
                _invalid("owner.healthy_risk_window")
        else:
            object.__setattr__(self, "risk_since", _utc(self.risk_since, "owner.risk_since"))
            object.__setattr__(self, "protection_until", _utc(self.protection_until, "owner.protection_until"))
            if self.protection_until <= self.risk_since:  # type: ignore[operator]
                _invalid("owner.protection_until")


@dataclass(frozen=True, slots=True, kw_only=True)
class DeliveryAttempt:
    schema_version: str
    attempt_id: str = field(repr=False)
    delivery_id: str = field(repr=False)
    tenant_id: str = field(repr=False)
    attempt_number: int
    owner_runtime_id: str
    owner_worker_id: str
    owner_claim_token: str = field(repr=False)
    owner_fencing: int
    config_version: str
    policy_version: str
    target_fingerprint: str
    status: DeliveryAttemptStatus
    started_at: datetime
    ack_deadline: datetime
    completed_at: datetime | None = None
    failure: DeliveryWriteFailure | None = None

    def __post_init__(self) -> None:
        if self.schema_version != P11_ATTEMPT_SCHEMA_VERSION:
            _invalid("attempt.schema_version")
        for name in (
            "attempt_id", "delivery_id", "tenant_id", "owner_runtime_id",
            "owner_worker_id", "owner_claim_token",
        ):
            _text(getattr(self, name), f"attempt.{name}")
        _positive(self.attempt_number, "attempt.attempt_number")
        _positive(self.owner_fencing, "attempt.owner_fencing")
        _text(self.config_version, "attempt.config_version")
        _text(self.policy_version, "attempt.policy_version")
        _digest(self.target_fingerprint, "attempt.target_fingerprint")
        if not isinstance(self.status, DeliveryAttemptStatus):
            _invalid("attempt.status")
        object.__setattr__(self, "started_at", _utc(self.started_at, "attempt.started_at"))
        object.__setattr__(self, "ack_deadline", _utc(self.ack_deadline, "attempt.ack_deadline"))
        if self.ack_deadline <= self.started_at:
            _invalid("attempt.ack_deadline")
        if self.status is DeliveryAttemptStatus.WRITING:
            if self.completed_at is not None or self.failure is not None:
                _invalid("attempt.writing_outcome")
        else:
            object.__setattr__(self, "completed_at", _utc(self.completed_at, "attempt.completed_at"))
            if self.completed_at < self.started_at:  # type: ignore[operator]
                _invalid("attempt.completed_at")
            if self.status is DeliveryAttemptStatus.WRITE_SUCCEEDED:
                if self.failure is not None:
                    _invalid("attempt.success_failure")
            elif not isinstance(self.failure, DeliveryWriteFailure):
                _invalid("attempt.failure")


@dataclass(frozen=True, slots=True, kw_only=True)
class MessageDeliverySummary:
    schema_version: str
    summary_id: str = field(repr=False)
    root_summary_id: str = field(repr=False)
    shard_index: int | None
    shard_count: int
    message_id: str
    tenant_id: str = field(repr=False)
    plan_id: str = field(repr=False)
    plan_version: int
    plan_decision_fingerprint: str
    target_fingerprint: str
    status: DeliverySummaryStatus
    total_count: int
    accepted_count: int
    rejected_count: int
    prepared_count: int
    cancelled_count: int
    not_initialized_count: int
    active_count: int
    inflight_count: int
    payload_evidence: PayloadEvidence | None
    policy_decision: AdmissionPolicyDecision
    rejection_evidence: tuple[TargetRejection, ...]
    state_version: int
    created_at: datetime
    updated_at: datetime
    queued_count: int = 0
    sending_count: int = 0
    ack_waiting_count: int = 0
    write_failed_count: int = 0

    def __post_init__(self) -> None:
        if self.schema_version != DR1_SCHEMA_VERSION:
            _invalid("summary.schema_version")
        for name in ("summary_id", "root_summary_id", "message_id", "tenant_id", "plan_id"):
            _text(getattr(self, name), f"summary.{name}")
        _positive(self.plan_version, "summary.plan_version")
        _digest(self.plan_decision_fingerprint, "summary.plan_decision_fingerprint")
        _digest(self.target_fingerprint, "summary.target_fingerprint")
        if not isinstance(self.status, DeliverySummaryStatus):
            _invalid("summary.status")
        if self.shard_index is not None:
            _nonnegative(self.shard_index, "summary.shard_index")
            if self.summary_id == self.root_summary_id or self.shard_index >= self.shard_count:
                _invalid("summary.shard_identity")
        elif self.summary_id != self.root_summary_id:
            _invalid("summary.root_identity")
        _nonnegative(self.shard_count, "summary.shard_count")
        if self.shard_index is not None and self.shard_count == 0:
            _invalid("summary.shard_count")
        counts = (self.total_count, self.accepted_count, self.rejected_count,
                  self.prepared_count, self.cancelled_count,
                  self.not_initialized_count, self.active_count, self.inflight_count,
                  self.queued_count, self.sending_count,
                  self.ack_waiting_count, self.write_failed_count)
        for value in counts:
            _nonnegative(value, "summary.count")
        if self.total_count != self.accepted_count + self.rejected_count + self.not_initialized_count:
            _invalid("summary.total_count")
        if (
            self.prepared_count + self.queued_count + self.sending_count
            + self.ack_waiting_count + self.write_failed_count
            + self.cancelled_count != self.accepted_count
        ):
            _invalid("summary.delivery_count")
        if self.active_count != self.sending_count:
            _invalid("summary.active_count")
        if self.inflight_count != self.ack_waiting_count:
            _invalid("summary.inflight_count")
        if self.payload_evidence is not None and not isinstance(self.payload_evidence, PayloadEvidence):
            _invalid("summary.payload_evidence")
        if not isinstance(self.policy_decision, AdmissionPolicyDecision):
            _invalid("summary.policy_decision")
        if self.payload_evidence is not None and (
            self.payload_evidence.request_binding_fingerprint
            != self.policy_decision.request_fingerprint
            or self.payload_evidence.target_binding_fingerprint
            != self.target_fingerprint
        ):
            _invalid("summary.payload_binding")
        if not isinstance(self.rejection_evidence, tuple) or any(
            not isinstance(value, TargetRejection) for value in self.rejection_evidence
        ):
            _invalid("summary.rejection_evidence")
        _positive(self.state_version, "summary.state_version")
        object.__setattr__(self, "created_at", _utc(self.created_at, "summary.created_at"))
        object.__setattr__(self, "updated_at", _utc(self.updated_at, "summary.updated_at"))
        if self.updated_at < self.created_at:
            _invalid("summary.updated_at")
        _validate_summary_status(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class DeliveryRecord:
    schema_version: str
    delivery_id: str = field(repr=False)
    summary_id: str = field(repr=False)
    root_summary_id: str = field(repr=False)
    shard_index: int | None
    message_id: str
    tenant_id: str = field(repr=False)
    plan_id: str = field(repr=False)
    plan_version: int
    plan_decision_fingerprint: str
    target_fingerprint: str
    target_set_fingerprint: str
    target_index: int
    binding: SelectedRoutingBinding = field(repr=False)
    status: DeliveryRecordStatus
    payload_evidence: PayloadEvidence
    policy_decision: AdmissionPolicyDecision
    envelope_authority: DeliveryEnvelopeAuthority
    state_version: int
    created_at: datetime
    updated_at: datetime
    activation: DeliveryActivationEvidence | None = None
    owner: DeliveryOwner | None = field(default=None, repr=False)
    current_attempt_id: str | None = field(default=None, repr=False)
    attempt_count: int = 0
    ack_deadline: datetime | None = None
    last_failure: DeliveryWriteFailure | None = None

    def __post_init__(self) -> None:
        if self.schema_version != DR1_SCHEMA_VERSION:
            _invalid("delivery.schema_version")
        for name in ("delivery_id", "summary_id", "root_summary_id", "message_id", "tenant_id", "plan_id"):
            _text(getattr(self, name), f"delivery.{name}")
        for name in ("plan_version", "state_version"):
            _positive(getattr(self, name), f"delivery.{name}")
        if self.shard_index is not None:
            _nonnegative(self.shard_index, "delivery.shard_index")
        _nonnegative(self.target_index, "delivery.target_index")
        if (self.shard_index is None) is not (self.summary_id == self.root_summary_id):
            _invalid("delivery.summary_binding")
        for name in ("plan_decision_fingerprint", "target_fingerprint", "target_set_fingerprint"):
            _digest(getattr(self, name), f"delivery.{name}")
        if not isinstance(self.binding, SelectedRoutingBinding):
            _invalid("delivery.binding")
        if not isinstance(self.status, DeliveryRecordStatus):
            _invalid("delivery.status")
        if not isinstance(self.payload_evidence, PayloadEvidence):
            _invalid("delivery.payload_evidence")
        if not isinstance(self.policy_decision, AdmissionPolicyDecision):
            _invalid("delivery.policy_decision")
        if not isinstance(self.envelope_authority, DeliveryEnvelopeAuthority):
            _invalid("delivery.envelope_authority")
        if (self.payload_evidence.request_binding_fingerprint
                != self.policy_decision.request_fingerprint
                or self.payload_evidence.target_binding_fingerprint
                != self.target_set_fingerprint):
            _invalid("delivery.payload_binding")
        object.__setattr__(self, "created_at", _utc(self.created_at, "delivery.created_at"))
        object.__setattr__(self, "updated_at", _utc(self.updated_at, "delivery.updated_at"))
        if self.updated_at < self.created_at:
            _invalid("delivery.updated_at")
        _nonnegative(self.attempt_count, "delivery.attempt_count")
        if self.current_attempt_id is not None:
            _text(self.current_attempt_id, "delivery.current_attempt_id")
        if self.ack_deadline is not None:
            object.__setattr__(self, "ack_deadline", _utc(self.ack_deadline, "delivery.ack_deadline"))
        if self.last_failure is not None and not isinstance(self.last_failure, DeliveryWriteFailure):
            _invalid("delivery.last_failure")
        _validate_delivery_dispatch_state(self)


@dataclass(frozen=True, slots=True, kw_only=True)
class DedupEvidence:
    schema_version: str
    tenant_id: str = field(repr=False)
    message_id: str
    target_fingerprint: str
    summary_id: str = field(repr=False)
    lifecycle: DuplicateLifecycle
    registered_at: datetime
    expires_at: datetime
    evidence_fingerprint: str

    def __post_init__(self) -> None:
        if self.schema_version != DEDUP_EVIDENCE_VERSION:
            _invalid("dedup.schema_version")
        for name in ("tenant_id", "message_id", "summary_id"):
            _text(getattr(self, name), f"dedup.{name}")
        _digest(self.target_fingerprint, "dedup.target_fingerprint")
        _digest(self.evidence_fingerprint, "dedup.evidence_fingerprint")
        if not isinstance(self.lifecycle, DuplicateLifecycle):
            _invalid("dedup.lifecycle")
        object.__setattr__(self, "registered_at", _utc(self.registered_at, "dedup.registered_at"))
        object.__setattr__(self, "expires_at", _utc(self.expires_at, "dedup.expires_at"))
        if self.expires_at <= self.registered_at:
            _invalid("dedup.expires_at")
        if self.evidence_fingerprint != compute_dedup_evidence_fingerprint(
            tenant_id=self.tenant_id, message_id=self.message_id,
            target_fingerprint=self.target_fingerprint, summary_id=self.summary_id,
            lifecycle=self.lifecycle, registered_at=self.registered_at,
            expires_at=self.expires_at,
        ):
            _invalid("dedup.evidence_fingerprint")


def compute_target_fingerprint(plan: ResolvedRoutingPlan) -> str:
    if not isinstance(plan, ResolvedRoutingPlan):
        _invalid("target_fingerprint.plan")
    values = [_binding_projection(value) for value in plan.selected_bindings]
    return _sha({"selected_bindings": values})


def compute_binding_fingerprint(binding: SelectedRoutingBinding) -> str:
    if not isinstance(binding, SelectedRoutingBinding):
        _invalid("binding_fingerprint.binding")
    return _sha(_binding_projection(binding))


def compute_dedup_evidence_fingerprint(**values: object) -> str:
    lifecycle = values.get("lifecycle")
    registered_at = values.get("registered_at")
    expires_at = values.get("expires_at")
    if not isinstance(lifecycle, DuplicateLifecycle):
        _invalid("dedup_fingerprint.lifecycle")
    return _sha({
        "tenant_id": values.get("tenant_id"),
        "message_id": values.get("message_id"),
        "target_fingerprint": values.get("target_fingerprint"),
        "summary_id": values.get("summary_id"),
        "lifecycle": lifecycle.value,
        "registered_at": _utc(registered_at, "dedup_fingerprint.registered_at").isoformat(),
        "expires_at": _utc(expires_at, "dedup_fingerprint.expires_at").isoformat(),
    })


def compute_payload_evidence_fingerprint(
    *, kind: PayloadKind, media_type: str, size_bytes: int,
    digest: str, checksum: str, object_id: str | None = None,
    object_version: str | None = None, tenant_id: str | None = None,
    validated_at: datetime | None = None, expires_at: datetime | None = None,
    body_ref: str | None = None, request_binding_fingerprint: str,
    target_binding_fingerprint: str,
) -> str:
    if not isinstance(kind, PayloadKind):
        _invalid("payload_fingerprint.kind")
    return _sha({
        "kind": kind.value, "media_type": media_type,
        "size_bytes": size_bytes, "digest": digest, "checksum": checksum,
        "object_id": object_id, "object_version": object_version,
        "tenant_id": tenant_id,
        "validated_at": (validated_at.isoformat() if validated_at else None),
        "expires_at": (expires_at.isoformat() if expires_at else None),
        "body_ref": body_ref,
        "request_binding_fingerprint": request_binding_fingerprint,
        "target_binding_fingerprint": target_binding_fingerprint,
    })


def validate_initialization_graph(
    *, plan: ResolvedRoutingPlan, root: MessageDeliverySummary,
    shards: tuple[MessageDeliverySummary, ...],
    deliveries: tuple[DeliveryRecord, ...], dedup: DedupEvidence,
) -> None:
    if not isinstance(plan, ResolvedRoutingPlan):
        _invalid("initialization.plan")
    if not isinstance(root, MessageDeliverySummary) or root.shard_index is not None:
        _invalid("initialization.root")
    if not isinstance(shards, tuple) or any(not isinstance(value, MessageDeliverySummary) for value in shards):
        _invalid("initialization.shards")
    if not isinstance(deliveries, tuple) or any(not isinstance(value, DeliveryRecord) for value in deliveries):
        _invalid("initialization.deliveries")
    if not isinstance(dedup, DedupEvidence):
        _invalid("initialization.dedup")
    target_fingerprint = compute_target_fingerprint(plan)
    expected_message_reference = "sha256:" + hashlib.sha256(
        root.message_id.encode("utf-8")
    ).hexdigest()[:16]
    if (expected_message_reference != plan.message_reference or root.plan_id != plan.plan_id
            or root.plan_version != plan.plan_version
            or root.plan_decision_fingerprint != plan.decision_fingerprint
            or root.target_fingerprint != target_fingerprint
            or dedup.tenant_id != root.tenant_id or dedup.message_id != root.message_id
            or dedup.target_fingerprint != target_fingerprint
            or dedup.summary_id != root.summary_id):
        _invalid("initialization.authority_chain")
    threshold = root.policy_decision.fanout_shard_threshold
    bucket_size = root.policy_decision.shard_bucket_size
    expected_shards = 0 if root.total_count <= threshold else (
        root.total_count + bucket_size - 1
    ) // bucket_size
    if root.shard_count != expected_shards or len(shards) != expected_shards:
        _invalid("initialization.shard_count")
    if tuple(value.shard_index for value in shards) != tuple(range(expected_shards)):
        _invalid("initialization.shard_order")
    if any(value.root_summary_id != root.summary_id for value in shards):
        _invalid("initialization.shard_root")
    if expected_shards and sum(value.total_count for value in shards) != root.total_count:
        _invalid("initialization.shard_totals")
    root_fields = (
        "schema_version", "root_summary_id", "shard_count", "message_id",
        "tenant_id", "plan_id", "plan_version", "plan_decision_fingerprint",
        "target_fingerprint", "payload_evidence", "policy_decision",
    )
    if any(
        any(getattr(value, field_name) != getattr(root, field_name)
            for field_name in root_fields)
        for value in shards
    ):
        _invalid("initialization.shard_authority_chain")
    if len(deliveries) != root.prepared_count:
        _invalid("initialization.delivery_count")
    selected = plan.selected_bindings
    delivery_indexes = tuple(value.target_index for value in deliveries)
    if (
        len(set(delivery_indexes)) != len(delivery_indexes)
        or any(index >= len(selected) for index in delivery_indexes)
        or any(selected[value.target_index] != value.binding for value in deliveries)
    ):
        _invalid("initialization.delivery_target_index")
    if any(
        value.status is not DeliveryRecordStatus.PREPARED
        or value.root_summary_id != root.summary_id
        or (expected_shards == 0 and value.summary_id != root.summary_id)
        or (expected_shards > 0 and value.summary_id == root.summary_id)
        or value.message_id != root.message_id
        or value.tenant_id != root.tenant_id
        or value.plan_id != root.plan_id
        or value.plan_version != root.plan_version
        or value.plan_decision_fingerprint != root.plan_decision_fingerprint
        or value.payload_evidence != root.payload_evidence
        or value.policy_decision != root.policy_decision
        or value.target_fingerprint != compute_binding_fingerprint(value.binding)
        or value.target_set_fingerprint != root.target_fingerprint
        for value in deliveries
    ):
        _invalid("initialization.delivery_authority_chain")
    selected_fingerprints = tuple(compute_binding_fingerprint(value) for value in selected)
    fingerprint_indexes = {
        value: index for index, value in enumerate(selected_fingerprints)
    }
    rejected_fingerprints = tuple(value.target_fingerprint for value in root.rejection_evidence)
    if (
        len(fingerprint_indexes) != len(selected_fingerprints)
        or
        root.rejected_count != len(rejected_fingerprints)
        or len(set(rejected_fingerprints)) != len(rejected_fingerprints)
        or any(value not in fingerprint_indexes for value in rejected_fingerprints)
        or set(delivery_indexes) | {
            fingerprint_indexes[value] for value in rejected_fingerprints
        } != set(range(root.total_count))
        or set(delivery_indexes) & {
            fingerprint_indexes[value] for value in rejected_fingerprints
        }
    ):
        _invalid("initialization.target_partition")
    for shard in shards:
        start = shard.shard_index * bucket_size
        end = min(root.total_count, start + bucket_size)
        indexes = set(range(start, end))
        shard_deliveries = tuple(value for value in deliveries if value.target_index in indexes)
        shard_rejections = tuple(
            value for value in root.rejection_evidence
            if fingerprint_indexes[value.target_fingerprint] in indexes
        )
        if (
            shard.total_count != end - start
            or shard.accepted_count != len(shard_deliveries)
            or shard.prepared_count != len(shard_deliveries)
            or shard.rejected_count != len(shard_rejections)
            or shard.rejection_evidence != shard_rejections
            or any(value.shard_index != shard.shard_index
                   or value.summary_id != shard.summary_id
                   for value in shard_deliveries)
        ):
            _invalid("initialization.shard_partition")


def _validate_summary_status(value: MessageDeliverySummary) -> None:
    if value.status is DeliverySummaryStatus.INITIALIZING:
        if (
            value.cancelled_count
            or value.prepared_count != value.accepted_count
            or any((value.queued_count, value.sending_count,
                    value.ack_waiting_count, value.write_failed_count))
        ):
            _invalid("summary.initializing_counts")
    elif value.status is DeliverySummaryStatus.PENDING:
        if not value.accepted_count:
            _invalid("summary.pending_counts")
    elif value.status is DeliverySummaryStatus.FAILED:
        if value.accepted_count or value.prepared_count or value.cancelled_count:
            _invalid("summary.failed_counts")
    elif value.status is DeliverySummaryStatus.CANCELLED:
        if (
            value.prepared_count
            or value.cancelled_count != value.accepted_count
            or any((value.queued_count, value.sending_count,
                    value.ack_waiting_count, value.write_failed_count))
        ):
            _invalid("summary.cancelled_counts")


def _validate_delivery_dispatch_state(value: DeliveryRecord) -> None:
    status = value.status
    if status in {
        DeliveryRecordStatus.PREPARED,
        DeliveryRecordStatus.CANCELLED,
    }:
        if any((value.activation, value.owner, value.current_attempt_id,
                value.ack_deadline, value.last_failure)) or value.attempt_count:
            _invalid("delivery.pre_dispatch_fields")
        return
    if not isinstance(value.activation, DeliveryActivationEvidence):
        _invalid("delivery.activation")
    if status is DeliveryRecordStatus.QUEUED:
        if (
            value.current_attempt_id is not None
            or value.attempt_count
            or value.ack_deadline is not None
            or value.last_failure is not None
        ):
            _invalid("delivery.queued_fields")
        if value.owner is not None and not isinstance(value.owner, DeliveryOwner):
            _invalid("delivery.owner")
        return
    if status in {DeliveryRecordStatus.SENDING, DeliveryRecordStatus.ACK_WAITING}:
        if (
            not isinstance(value.owner, DeliveryOwner)
            or value.current_attempt_id is None
            or value.attempt_count <= 0
            or value.ack_deadline is None
            or value.last_failure is not None
        ):
            _invalid("delivery.inflight_fields")
        return
    if status in {DeliveryRecordStatus.EXPIRED, DeliveryRecordStatus.PAYLOAD_REJECTED,
                  DeliveryRecordStatus.TARGET_WAITING}:
        if (value.owner is not None or value.current_attempt_id is not None
                or value.attempt_count or value.ack_deadline is not None
                or not isinstance(value.last_failure, DeliveryWriteFailure)):
            _invalid("delivery.precheck_terminal_fields")
        return
    if status in {DeliveryRecordStatus.WRITE_FAILED,
                  DeliveryRecordStatus.WRITE_UNCERTAIN}:
        if (
            value.owner is not None
            or value.current_attempt_id is None
            or value.attempt_count <= 0
            or value.ack_deadline is not None
            or not isinstance(value.last_failure, DeliveryWriteFailure)
        ):
            _invalid("delivery.write_failed_fields")
        return
    if status is DeliveryRecordStatus.RETRY_SCHEDULED:
        _invalid("delivery.retry_scheduled_reserved")


def _binding_projection(value: SelectedRoutingBinding) -> dict[str, object]:
    return {
        "runtime_id": value.runtime_id, "connection_id": value.connection_id,
        "session_id": value.session_id, "connection_epoch": value.connection_epoch,
        "tenant_id": value.tenant_id,
        "identity_value": value.identity_reference.value,
        "required_capabilities": sorted(value.required_capabilities),
        "component_type": value.component_type,
        "binding_rebind_policy": value.binding_rebind_policy.value,
    }


def cancel_initializing_graph(
    *, root: MessageDeliverySummary,
    shards: tuple[MessageDeliverySummary, ...],
    created_deliveries: tuple[DeliveryRecord, ...],
    cancelled_at: datetime,
) -> tuple[MessageDeliverySummary, tuple[MessageDeliverySummary, ...], tuple[DeliveryRecord, ...]]:
    """The only P10 cancellation: fail/cancel an initializing message graph."""
    import dataclasses
    cancelled_at = _utc(cancelled_at, "initializing_cancel.cancelled_at")
    if (not isinstance(root, MessageDeliverySummary)
            or root.status is not DeliverySummaryStatus.INITIALIZING):
        _invalid("initializing_cancel.root")
    if not isinstance(shards, tuple) or any(
        not isinstance(value, MessageDeliverySummary)
        or value.status is not DeliverySummaryStatus.INITIALIZING
        or value.root_summary_id != root.summary_id
        for value in shards
    ):
        _invalid("initializing_cancel.shards")
    if not isinstance(created_deliveries, tuple) or any(
        not isinstance(value, DeliveryRecord)
        or value.status is not DeliveryRecordStatus.PREPARED
        or value.root_summary_id != root.summary_id
        for value in created_deliveries
    ):
        _invalid("initializing_cancel.deliveries")
    by_shard: dict[int, int] = {}
    for value in created_deliveries:
        shard_key = value.shard_index if value.shard_index is not None else -1
        by_shard[shard_key] = by_shard.get(shard_key, 0) + 1
    cancelled_shards = []
    for shard in shards:
        created = by_shard.get(shard.shard_index or 0, 0)
        intended = shard.accepted_count + shard.not_initialized_count
        if created > intended:
            _invalid("initializing_cancel.shard_created_count")
        cancelled_shards.append(dataclasses.replace(
            shard, status=DeliverySummaryStatus.CANCELLED,
            accepted_count=created, prepared_count=0, cancelled_count=created,
            not_initialized_count=intended - created,
            state_version=shard.state_version + 1, updated_at=cancelled_at,
        ))
    created = len(created_deliveries)
    intended = root.accepted_count + root.not_initialized_count
    if created != sum(by_shard.values()) or created > intended:
        _invalid("initializing_cancel.created_count")
    cancelled_root = dataclasses.replace(
        root, status=DeliverySummaryStatus.CANCELLED,
        accepted_count=created, prepared_count=0, cancelled_count=created,
        not_initialized_count=intended - created,
        state_version=root.state_version + 1, updated_at=cancelled_at,
    )
    cancelled_deliveries = tuple(dataclasses.replace(
        value, status=DeliveryRecordStatus.CANCELLED,
        state_version=value.state_version + 1, updated_at=cancelled_at,
    ) for value in created_deliveries)
    return cancelled_root, tuple(cancelled_shards), cancelled_deliveries


def canonical_inline_payload(payload: InlinePayload, *, max_depth: int) -> bytes:
    if not isinstance(payload, InlinePayload):
        _invalid("inline_payload")
    _positive(max_depth, "inline.max_depth")
    if payload.media_type == "application/octet-stream":
        return bytes(payload.value)  # type: ignore[arg-type]
    _validate_json(payload.value, max_depth=max_depth)
    try:
        return json.dumps(payload.value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError, UnicodeError):
        _invalid("inline.value")


def _validate_json(value: object, *, max_depth: int) -> None:
    stack = [(value, 1)]
    seen: set[int] = set()
    while stack:
        item, depth = stack.pop()
        if depth > max_depth:
            raise _PayloadDepthError
        if item is None or type(item) in {bool, int, float, str}:
            continue
        if isinstance(item, (list, dict)):
            marker = id(item)
            if marker in seen:
                _invalid("inline.cycle")
            seen.add(marker)
            if isinstance(item, dict):
                if any(not isinstance(key, str) for key in item):
                    _invalid("inline.key_type")
                stack.extend((child, depth + 1) for child in item.values())
            else:
                stack.extend((child, depth + 1) for child in item)
            continue
        _invalid("inline.value_type")


class _PayloadDepthError(ValueError):
    pass


def _json_root(value: object) -> bool:
    return value is None or type(value) in {bool, int, float, str} or isinstance(value, (list, dict))


def _sha(value: object) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _text(value: object, field_name: str) -> None:
    if not isinstance(value, str) or _TEXT.fullmatch(value) is None:
        _invalid(field_name)


def _digest(value: object, field_name: str) -> None:
    if not isinstance(value, str) or _DIGEST.fullmatch(value) is None:
        _invalid(field_name)


def _positive(value: object, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        _invalid(field_name)


def _nonnegative(value: object, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        _invalid(field_name)


def _utc(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        _invalid(field_name)
    return value.astimezone(timezone.utc)


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "DR-1 delivery contract value is invalid.",
        details={"component": "delivery_admission", "field": field_name},
    )


__all__ = (
    "ADMISSION_RESPONSE_VERSION", "ADMISSION_RESULT_VERSION",
    "ATOMIC_ADMISSION_VERSION", "DEDUP_EVIDENCE_VERSION",
    "DR1_SCHEMA_VERSION", "MAX_ACTIVATION_BATCH_SIZE",
    "PAYLOAD_EVIDENCE_VERSION", "P11_ACTIVATION_SCHEMA_VERSION",
    "P11_ATTEMPT_SCHEMA_VERSION", "P11_OWNER_SCHEMA_VERSION",
    "AdmissionOutcome", "AdmissionPriority",
    "AdmissionReliability", "AdmissionPolicyDecision", "AdmissionTrace",
    "DedupEvidence", "DeliveryActivationEvidence", "DeliveryAttempt",
    "DeliveryAttemptStatus", "DeliveryOwner", "DeliveryOwnerRisk",
    "DeliveryRecord", "DeliveryRecordStatus", "DeliveryWriteFailure",
    "DeliverySummaryStatus", "DuplicateLifecycle", "InlinePayload",
    "MessageDeliverySummary", "PayloadDependencyDisposition",
    "PayloadEvidence", "PayloadKind", "PayloadReference", "RejectionReason",
    "TargetRejection", "cancel_initializing_graph",
    "canonical_inline_payload", "compute_binding_fingerprint",
    "compute_dedup_evidence_fingerprint", "compute_payload_evidence_fingerprint",
    "compute_target_fingerprint",
    "validate_initialization_graph",
)
