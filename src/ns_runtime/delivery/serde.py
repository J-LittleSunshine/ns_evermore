# -*- coding: utf-8 -*-
"""Bounded StateStore serialization for DR-1 and P11 delivery authority."""

from __future__ import annotations

from datetime import datetime

from ns_common.exceptions import NsValidationError
from ns_runtime.routing import (
    RebindPolicy,
    RoutingIdentityReference,
    RoutingStrategy,
    SelectedRoutingBinding,
)

from .models import (
    AdmissionPolicyDecision,
    AdmissionPriority,
    AdmissionReliability,
    DeliveryActivationEvidence,
    DeliveryAttempt,
    DeliveryAttemptStatus,
    DeliveryOwner,
    DeliveryOwnerRisk,
    DeliveryRecord,
    DeliveryRecordStatus,
    DeliverySummaryStatus,
    DeliveryWriteFailure,
    DeliveryEnvelopeAuthority,
    AdmissionTrace,
    MessageDeliverySummary,
    PayloadDependencyDisposition,
    PayloadEvidence,
    PayloadKind,
    RejectionReason,
    TargetRejection,
    LEGACY_DR1_SCHEMA_VERSION,
)


def delivery_to_dict(value: DeliveryRecord) -> dict[str, object]:
    if not isinstance(value, DeliveryRecord):
        _invalid("delivery")
    return {
        "schema_version": value.schema_version,
        "delivery_id": value.delivery_id,
        "summary_id": value.summary_id,
        "root_summary_id": value.root_summary_id,
        "shard_index": value.shard_index,
        "message_id": value.message_id,
        "tenant_id": value.tenant_id,
        "plan_id": value.plan_id,
        "plan_version": value.plan_version,
        "plan_decision_fingerprint": value.plan_decision_fingerprint,
        "target_fingerprint": value.target_fingerprint,
        "target_set_fingerprint": value.target_set_fingerprint,
        "target_index": value.target_index,
        "binding": _binding_to_dict(value.binding),
        "status": value.status.value,
        "payload_evidence": payload_evidence_to_dict(value.payload_evidence),
        "policy_decision": policy_decision_to_dict(value.policy_decision),
        "envelope_authority": {
            "message_type": value.envelope_authority.message_type,
            "source_identity": value.envelope_authority.source_identity,
            "authorization_binding_reference": value.envelope_authority.authorization_binding_reference,
            "permission_snapshot_ref": value.envelope_authority.permission_snapshot_ref,
            "permission_snapshot_version": value.envelope_authority.permission_snapshot_version,
            "iam_decision_reference": value.envelope_authority.iam_decision_reference,
            "iam_decision_version": value.envelope_authority.iam_decision_version,
            "trace": value.envelope_authority.trace.to_wire(),
        },
        "state_version": value.state_version,
        "created_at": value.created_at.isoformat(),
        "updated_at": value.updated_at.isoformat(),
        "activation": (
            None if value.activation is None else _activation_to_dict(value.activation)
        ),
        "owner": None if value.owner is None else _owner_to_dict(value.owner),
        "current_attempt_id": value.current_attempt_id,
        "attempt_count": value.attempt_count,
        "ack_deadline": (
            None if value.ack_deadline is None else value.ack_deadline.isoformat()
        ),
        "last_failure": (
            None if value.last_failure is None else value.last_failure.value
        ),
    }


def delivery_from_dict(raw: object) -> DeliveryRecord:
    values = _mapping(raw, "delivery")
    if values.get("schema_version") == LEGACY_DR1_SCHEMA_VERSION:
        _invalid("delivery.schema_migration_required")
    try:
        return DeliveryRecord(
            schema_version=values["schema_version"],
            delivery_id=values["delivery_id"],
            summary_id=values["summary_id"],
            root_summary_id=values["root_summary_id"],
            shard_index=values["shard_index"],
            message_id=values["message_id"],
            tenant_id=values["tenant_id"],
            plan_id=values["plan_id"],
            plan_version=values["plan_version"],
            plan_decision_fingerprint=values["plan_decision_fingerprint"],
            target_fingerprint=values["target_fingerprint"],
            target_set_fingerprint=values["target_set_fingerprint"],
            target_index=values["target_index"],
            binding=_binding_from_dict(values["binding"]),
            status=DeliveryRecordStatus(values["status"]),
            payload_evidence=payload_evidence_from_dict(values["payload_evidence"]),
            policy_decision=policy_decision_from_dict(values["policy_decision"]),
            envelope_authority=_envelope_authority_from_dict(values["envelope_authority"]),
            state_version=values["state_version"],
            created_at=_time(values["created_at"], "delivery.created_at"),
            updated_at=_time(values["updated_at"], "delivery.updated_at"),
            activation=(
                None if values.get("activation") is None
                else _activation_from_dict(values["activation"])
            ),
            owner=(
                None if values.get("owner") is None
                else _owner_from_dict(values["owner"])
            ),
            current_attempt_id=values.get("current_attempt_id"),
            attempt_count=values.get("attempt_count", 0),
            ack_deadline=(
                None if values.get("ack_deadline") is None
                else _time(values["ack_deadline"], "delivery.ack_deadline")
            ),
            last_failure=(
                None if values.get("last_failure") is None
                else DeliveryWriteFailure(values["last_failure"])
            ),
        )
    except (KeyError, TypeError, ValueError):
        _invalid("delivery.fields")


def summary_to_dict(value: MessageDeliverySummary) -> dict[str, object]:
    if not isinstance(value, MessageDeliverySummary):
        _invalid("summary")
    return {
        "schema_version": value.schema_version,
        "summary_id": value.summary_id,
        "root_summary_id": value.root_summary_id,
        "shard_index": value.shard_index,
        "shard_count": value.shard_count,
        "message_id": value.message_id,
        "tenant_id": value.tenant_id,
        "plan_id": value.plan_id,
        "plan_version": value.plan_version,
        "plan_decision_fingerprint": value.plan_decision_fingerprint,
        "target_fingerprint": value.target_fingerprint,
        "status": value.status.value,
        "total_count": value.total_count,
        "accepted_count": value.accepted_count,
        "rejected_count": value.rejected_count,
        "prepared_count": value.prepared_count,
        "cancelled_count": value.cancelled_count,
        "not_initialized_count": value.not_initialized_count,
        "active_count": value.active_count,
        "inflight_count": value.inflight_count,
        "queued_count": value.queued_count,
        "sending_count": value.sending_count,
        "ack_waiting_count": value.ack_waiting_count,
        "write_failed_count": value.write_failed_count,
        "payload_evidence": (
            None if value.payload_evidence is None
            else payload_evidence_to_dict(value.payload_evidence)
        ),
        "policy_decision": policy_decision_to_dict(value.policy_decision),
        "rejection_evidence": [
            {
                "target_fingerprint": item.target_fingerprint,
                "reason": item.reason.value,
            }
            for item in value.rejection_evidence
        ],
        "state_version": value.state_version,
        "created_at": value.created_at.isoformat(),
        "updated_at": value.updated_at.isoformat(),
    }


def summary_from_dict(raw: object) -> MessageDeliverySummary:
    values = _mapping(raw, "summary")
    if values.get("schema_version") == LEGACY_DR1_SCHEMA_VERSION:
        _invalid("summary.schema_migration_required")
    try:
        rejection_values = values["rejection_evidence"]
        if not isinstance(rejection_values, list):
            _invalid("summary.rejection_evidence")
        return MessageDeliverySummary(
            schema_version=values["schema_version"],
            summary_id=values["summary_id"],
            root_summary_id=values["root_summary_id"],
            shard_index=values["shard_index"],
            shard_count=values["shard_count"],
            message_id=values["message_id"],
            tenant_id=values["tenant_id"],
            plan_id=values["plan_id"],
            plan_version=values["plan_version"],
            plan_decision_fingerprint=values["plan_decision_fingerprint"],
            target_fingerprint=values["target_fingerprint"],
            status=DeliverySummaryStatus(values["status"]),
            total_count=values["total_count"],
            accepted_count=values["accepted_count"],
            rejected_count=values["rejected_count"],
            prepared_count=values["prepared_count"],
            cancelled_count=values["cancelled_count"],
            not_initialized_count=values["not_initialized_count"],
            active_count=values["active_count"],
            inflight_count=values["inflight_count"],
            queued_count=values.get("queued_count", 0),
            sending_count=values.get("sending_count", 0),
            ack_waiting_count=values.get("ack_waiting_count", 0),
            write_failed_count=values.get("write_failed_count", 0),
            payload_evidence=(
                None if values["payload_evidence"] is None
                else payload_evidence_from_dict(values["payload_evidence"])
            ),
            policy_decision=policy_decision_from_dict(values["policy_decision"]),
            rejection_evidence=tuple(
                TargetRejection(
                    target_fingerprint=_mapping(item, "summary.rejection")["target_fingerprint"],
                    reason=RejectionReason(_mapping(item, "summary.rejection")["reason"]),
                )
                for item in rejection_values
            ),
            state_version=values["state_version"],
            created_at=_time(values["created_at"], "summary.created_at"),
            updated_at=_time(values["updated_at"], "summary.updated_at"),
        )
    except (KeyError, TypeError, ValueError):
        _invalid("summary.fields")


def attempt_to_dict(value: DeliveryAttempt) -> dict[str, object]:
    if not isinstance(value, DeliveryAttempt):
        _invalid("attempt")
    return {
        "schema_version": value.schema_version,
        "attempt_id": value.attempt_id,
        "delivery_id": value.delivery_id,
        "tenant_id": value.tenant_id,
        "attempt_number": value.attempt_number,
        "owner_runtime_id": value.owner_runtime_id,
        "owner_worker_id": value.owner_worker_id,
        "owner_claim_token": value.owner_claim_token,
        "owner_fencing": value.owner_fencing,
        "config_version": value.config_version,
        "policy_version": value.policy_version,
        "target_fingerprint": value.target_fingerprint,
        "status": value.status.value,
        "started_at": value.started_at.isoformat(),
        "ack_deadline": value.ack_deadline.isoformat(),
        "completed_at": (
            None if value.completed_at is None else value.completed_at.isoformat()
        ),
        "failure": None if value.failure is None else value.failure.value,
    }


def attempt_from_dict(raw: object) -> DeliveryAttempt:
    values = _mapping(raw, "attempt")
    try:
        return DeliveryAttempt(
            schema_version=values["schema_version"],
            attempt_id=values["attempt_id"],
            delivery_id=values["delivery_id"],
            tenant_id=values["tenant_id"],
            attempt_number=values["attempt_number"],
            owner_runtime_id=values["owner_runtime_id"],
            owner_worker_id=values["owner_worker_id"],
            owner_claim_token=values["owner_claim_token"],
            owner_fencing=values["owner_fencing"],
            config_version=values["config_version"],
            policy_version=values["policy_version"],
            target_fingerprint=values["target_fingerprint"],
            status=DeliveryAttemptStatus(values["status"]),
            started_at=_time(values["started_at"], "attempt.started_at"),
            ack_deadline=_time(values["ack_deadline"], "attempt.ack_deadline"),
            completed_at=(
                None if values["completed_at"] is None
                else _time(values["completed_at"], "attempt.completed_at")
            ),
            failure=(
                None if values["failure"] is None
                else DeliveryWriteFailure(values["failure"])
            ),
        )
    except (KeyError, TypeError, ValueError):
        _invalid("attempt.fields")


def policy_decision_to_dict(value: AdmissionPolicyDecision) -> dict[str, object]:
    if not isinstance(value, AdmissionPolicyDecision):
        _invalid("policy_decision")
    return {
        "request_fingerprint": value.request_fingerprint,
        "config_version": value.config_version,
        "policy_version": value.policy_version,
        "accepted": value.accepted,
        "priority": value.priority.value,
        "reliability": value.reliability.value,
        "expires_at": value.expires_at.isoformat(),
        "ack_timeout_seconds": value.ack_timeout_seconds,
        "target_strategy": value.target_strategy.value,
        "dedup_ttl_seconds": value.dedup_ttl_seconds,
        "max_inline_bytes": value.max_inline_bytes,
        "max_json_depth": value.max_json_depth,
        "payload_dependency_disposition": value.payload_dependency_disposition.value,
        "fanout_shard_threshold": value.fanout_shard_threshold,
        "shard_bucket_size": value.shard_bucket_size,
        "initialization_batch_size": value.initialization_batch_size,
        "activation_batch_size": value.activation_batch_size,
        "rejection_reason": (
            None if value.rejection_reason is None else value.rejection_reason.value
        ),
    }


def policy_decision_from_dict(raw: object) -> AdmissionPolicyDecision:
    values = _mapping(raw, "policy_decision")
    try:
        return AdmissionPolicyDecision(
            request_fingerprint=values["request_fingerprint"],
            config_version=values["config_version"],
            policy_version=values["policy_version"],
            accepted=values["accepted"],
            priority=AdmissionPriority(values["priority"]),
            reliability=AdmissionReliability(values["reliability"]),
            expires_at=_time(values["expires_at"], "policy_decision.expires_at"),
            ack_timeout_seconds=values["ack_timeout_seconds"],
            target_strategy=RoutingStrategy(values["target_strategy"]),
            dedup_ttl_seconds=values["dedup_ttl_seconds"],
            max_inline_bytes=values["max_inline_bytes"],
            max_json_depth=values["max_json_depth"],
            payload_dependency_disposition=PayloadDependencyDisposition(
                values["payload_dependency_disposition"]
            ),
            fanout_shard_threshold=values["fanout_shard_threshold"],
            shard_bucket_size=values["shard_bucket_size"],
            initialization_batch_size=values["initialization_batch_size"],
            activation_batch_size=values["activation_batch_size"],
            rejection_reason=(
                None if values["rejection_reason"] is None
                else RejectionReason(values["rejection_reason"])
            ),
        )
    except (KeyError, TypeError, ValueError):
        _invalid("policy_decision.fields")


def payload_evidence_to_dict(value: PayloadEvidence) -> dict[str, object]:
    if not isinstance(value, PayloadEvidence):
        _invalid("payload_evidence")
    return value.safe_dict()


def payload_evidence_from_dict(raw: object) -> PayloadEvidence:
    values = _mapping(raw, "payload_evidence")
    try:
        return PayloadEvidence(
            schema_version=values["schema_version"],
            kind=PayloadKind(values["kind"]),
            media_type=values["media_type"],
            size_bytes=values["size_bytes"],
            digest=values["digest"],
            checksum=values["checksum"],
            evidence_fingerprint=values["evidence_fingerprint"],
            object_id=values.get("object_id"),
            object_version=values.get("object_version"),
            tenant_id=values.get("tenant_id"),
            validated_at=(
                None if values.get("validated_at") is None
                else _time(values["validated_at"], "payload_evidence.validated_at")
            ),
            expires_at=(
                None if values.get("expires_at") is None
                else _time(values["expires_at"], "payload_evidence.expires_at")
            ),
            body_ref=values.get("body_ref"),
            request_binding_fingerprint=values["request_binding_fingerprint"],
            target_binding_fingerprint=values["target_binding_fingerprint"],
        )
    except (KeyError, TypeError, ValueError):
        _invalid("payload_evidence.fields")


def _binding_to_dict(value: SelectedRoutingBinding) -> dict[str, object]:
    return {
        "runtime_id": value.runtime_id,
        "connection_id": value.connection_id,
        "session_id": value.session_id,
        "connection_epoch": value.connection_epoch,
        "tenant_id": value.tenant_id,
        "identity": value.identity_reference.value,
        "required_capabilities": sorted(value.required_capabilities),
        "component_type": value.component_type,
        "binding_rebind_policy": value.binding_rebind_policy.value,
    }


def _envelope_authority_from_dict(raw: object) -> DeliveryEnvelopeAuthority:
    values = _mapping(raw, "envelope_authority")
    trace_values = _mapping(values.get("trace"), "envelope_authority.trace")
    try:
        return DeliveryEnvelopeAuthority(
            message_type=values["message_type"],
            source_identity=values["source_identity"],
            authorization_binding_reference=values["authorization_binding_reference"],
            permission_snapshot_ref=values["permission_snapshot_ref"],
            permission_snapshot_version=values["permission_snapshot_version"],
            iam_decision_reference=values["iam_decision_reference"],
            iam_decision_version=values["iam_decision_version"],
            trace=AdmissionTrace(
                trace_id=trace_values["trace_id"],
                correlation_id=trace_values.get("correlation_id"),
            ),
        )
    except (KeyError, TypeError, ValueError):
        _invalid("envelope_authority.fields")


def _binding_from_dict(raw: object) -> SelectedRoutingBinding:
    values = _mapping(raw, "binding")
    capabilities = values.get("required_capabilities")
    if not isinstance(capabilities, list):
        _invalid("binding.required_capabilities")
    try:
        return SelectedRoutingBinding(
            runtime_id=values["runtime_id"],
            connection_id=values["connection_id"],
            session_id=values["session_id"],
            connection_epoch=values["connection_epoch"],
            tenant_id=values["tenant_id"],
            identity_reference=RoutingIdentityReference(value=values["identity"]),
            required_capabilities=frozenset(capabilities),
            component_type=values["component_type"],
            binding_rebind_policy=RebindPolicy(values["binding_rebind_policy"]),
        )
    except (KeyError, TypeError, ValueError):
        _invalid("binding.fields")


def _activation_to_dict(value: DeliveryActivationEvidence) -> dict[str, object]:
    return {
        "schema_version": value.schema_version,
        "config_version": value.config_version,
        "policy_version": value.policy_version,
        "reason": value.reason,
        "batch_size": value.batch_size,
        "candidate_count": value.candidate_count,
        "activated_at": value.activated_at.isoformat(),
    }


def _activation_from_dict(raw: object) -> DeliveryActivationEvidence:
    values = _mapping(raw, "activation")
    try:
        return DeliveryActivationEvidence(
            schema_version=values["schema_version"],
            config_version=values["config_version"],
            policy_version=values["policy_version"],
            reason=values["reason"],
            batch_size=values["batch_size"],
            candidate_count=values["candidate_count"],
            activated_at=_time(values["activated_at"], "activation.activated_at"),
        )
    except (KeyError, TypeError, ValueError):
        _invalid("activation.fields")


def _owner_to_dict(value: DeliveryOwner) -> dict[str, object]:
    return {
        "schema_version": value.schema_version,
        "runtime_id": value.runtime_id,
        "worker_id": value.worker_id,
        "claim_token": value.claim_token,
        "claimed_at": value.claimed_at.isoformat(),
        "lease_expires_at": value.lease_expires_at.isoformat(),
        "renew_failures": value.renew_failures,
        "risk": value.risk.value,
        "fencing": value.fencing,
        "risk_since": None if value.risk_since is None else value.risk_since.isoformat(),
        "protection_until": (
            None if value.protection_until is None else value.protection_until.isoformat()
        ),
    }


def _owner_from_dict(raw: object) -> DeliveryOwner:
    values = _mapping(raw, "owner")
    try:
        return DeliveryOwner(
            schema_version=values["schema_version"],
            runtime_id=values["runtime_id"],
            worker_id=values["worker_id"],
            claim_token=values["claim_token"],
            claimed_at=_time(values["claimed_at"], "owner.claimed_at"),
            lease_expires_at=_time(values["lease_expires_at"], "owner.lease_expires_at"),
            renew_failures=values["renew_failures"],
            risk=DeliveryOwnerRisk(values["risk"]),
            fencing=values["fencing"],
            risk_since=(
                None if values["risk_since"] is None
                else _time(values["risk_since"], "owner.risk_since")
            ),
            protection_until=(
                None if values["protection_until"] is None
                else _time(values["protection_until"], "owner.protection_until")
            ),
        )
    except (KeyError, TypeError, ValueError):
        _invalid("owner.fields")


def _mapping(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict) or any(type(key) is not str for key in value):
        _invalid(field)
    return value


def _time(value: object, field: str) -> datetime:
    if type(value) is not str:
        _invalid(field)
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        _invalid(field)


def _invalid(field: str):
    raise NsValidationError(
        "Delivery authority document is invalid.",
        details={"component": "delivery_serde", "field": field},
    )


__all__ = (
    "attempt_from_dict",
    "attempt_to_dict",
    "delivery_from_dict",
    "delivery_to_dict",
    "payload_evidence_from_dict",
    "payload_evidence_to_dict",
    "policy_decision_from_dict",
    "policy_decision_to_dict",
    "summary_from_dict",
    "summary_to_dict",
)
