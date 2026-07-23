# -*- coding: utf-8 -*-
"""Trusted P10 admission policy; sender fields are requests, never authority."""

from __future__ import annotations

import hashlib
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from ns_common.exceptions import NsValidationError
from ns_runtime.routing import ResolvedRoutingPlan, RoutingStrategy

from .models import (
    AdmissionPolicyDecision, AdmissionPriority, AdmissionReliability,
    DeliveryEnvelopeAuthority, InlinePayload, InlinePayloadDescriptor,
    PayloadDependencyDisposition, PayloadReference, RejectionReason,
    MAX_ACTIVATION_BATCH_SIZE, describe_inline_payload,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class AdmissionPolicyConfig:
    config_version: str
    policy_version: str
    max_inline_bytes: int = 1_048_576
    max_json_depth: int = 32
    min_delivery_window_seconds: int = 5
    max_ack_timeout_seconds: int = 300
    dedup_ttl_seconds: int = 86_400
    default_priority: AdmissionPriority = AdmissionPriority.NORMAL
    default_reliability: AdmissionReliability = AdmissionReliability.AT_LEAST_ONCE
    fanout_shard_threshold: int = 5000
    shard_bucket_size: int = 1000
    initialization_batch_size: int = 500
    activation_batch_size: int = 200
    authority_bucket_count: int = 8

    def __post_init__(self) -> None:
        for name in ("config_version", "policy_version"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value or len(value) > 256:
                _invalid(f"config.{name}")
        for name in ("max_inline_bytes", "max_json_depth",
                     "min_delivery_window_seconds", "max_ack_timeout_seconds",
                     "dedup_ttl_seconds", "fanout_shard_threshold",
                     "shard_bucket_size", "initialization_batch_size",
                     "activation_batch_size", "authority_bucket_count"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                _invalid(f"config.{name}")
        if self.activation_batch_size > MAX_ACTIVATION_BATCH_SIZE:
            _invalid("config.activation_batch_size")
        if not isinstance(self.default_priority, AdmissionPriority):
            _invalid("config.default_priority")
        if not isinstance(self.default_reliability, AdmissionReliability):
            _invalid("config.default_reliability")


_ADMISSION_REQUEST_ISSUER = object()


@dataclass(frozen=True, slots=True, init=False)
class AdmissionRequest:
    plan: ResolvedRoutingPlan = field(repr=False)
    message_id: str
    tenant_id: str = field(repr=False)
    source_identity: str = field(repr=False)
    authorization_binding_reference: str = field(repr=False)
    envelope_authority: DeliveryEnvelopeAuthority = field(repr=False)
    payload: InlinePayload | PayloadReference = field(repr=False)
    inline_descriptor: InlinePayloadDescriptor | None = field(repr=False)
    requested_priority: AdmissionPriority | None
    requested_reliability: AdmissionReliability | None
    requested_expires_at: datetime
    requested_ack_timeout_seconds: int
    requested_target_strategy: RoutingStrategy

    def __init__(
        self, *, plan: ResolvedRoutingPlan, message_id: str, tenant_id: str,
        source_identity: str, authorization_binding_reference: str,
        envelope_authority: DeliveryEnvelopeAuthority,
        payload: InlinePayload | PayloadReference,
        requested_priority: AdmissionPriority | None,
        requested_reliability: AdmissionReliability | None,
        requested_expires_at: datetime, requested_ack_timeout_seconds: int,
        requested_target_strategy: RoutingStrategy, _issuer: object = None,
    ) -> None:
        if _issuer is not _ADMISSION_REQUEST_ISSUER:
            _invalid("request.issuer")
        for name, value in (
            ("plan", plan), ("message_id", message_id),
            ("tenant_id", tenant_id), ("source_identity", source_identity),
            ("authorization_binding_reference", authorization_binding_reference),
            ("envelope_authority", envelope_authority),
            ("payload", payload), ("requested_priority", requested_priority),
            ("requested_reliability", requested_reliability),
            ("requested_expires_at", requested_expires_at),
            ("requested_ack_timeout_seconds", requested_ack_timeout_seconds),
            ("requested_target_strategy", requested_target_strategy),
        ):
            object.__setattr__(self, name, value)
        object.__setattr__(
            self, "inline_descriptor",
            describe_inline_payload(payload) if isinstance(payload, InlinePayload) else None,
        )
        self.__post_init__()

    @classmethod
    def from_stage_six(
        cls, *, stage_six: object, message_id: str, tenant_id: str,
        source_identity: str, authorization_binding_reference: str,
        envelope_authority: DeliveryEnvelopeAuthority,
        payload: InlinePayload | PayloadReference,
        requested_priority: AdmissionPriority | None,
        requested_reliability: AdmissionReliability | None,
        requested_expires_at: datetime, requested_ack_timeout_seconds: int,
        requested_target_strategy: RoutingStrategy,
    ) -> "AdmissionRequest":
        from .integration import StageSixAdmissionInput
        if not isinstance(stage_six, StageSixAdmissionInput):
            _invalid("request.stage_six")
        return cls(
            plan=stage_six.plan, message_id=message_id, tenant_id=tenant_id,
            source_identity=source_identity,
            authorization_binding_reference=authorization_binding_reference,
            envelope_authority=envelope_authority,
            payload=payload,
            requested_priority=requested_priority,
            requested_reliability=requested_reliability,
            requested_expires_at=requested_expires_at,
            requested_ack_timeout_seconds=requested_ack_timeout_seconds,
            requested_target_strategy=requested_target_strategy,
            _issuer=_ADMISSION_REQUEST_ISSUER,
        )

    def __post_init__(self) -> None:
        if not isinstance(self.plan, ResolvedRoutingPlan):
            _invalid("request.plan")
        for name in ("message_id", "tenant_id", "source_identity",
                     "authorization_binding_reference"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value or len(value) > 512:
                _invalid(f"request.{name}")
        authorization = self.plan.authorization_evidence
        expected_message_reference = "sha256:" + hashlib.sha256(
            self.message_id.encode("utf-8")
        ).hexdigest()[:16]
        if (expected_message_reference != self.plan.message_reference
                or self.tenant_id != authorization.effective_tenant_id
                or self.authorization_binding_reference
                != authorization.message_binding_reference):
            _invalid("request.plan_authority_chain")
        if not isinstance(self.payload, (InlinePayload, PayloadReference)):
            _invalid("request.payload")
        if isinstance(self.payload, InlinePayload):
            if not isinstance(self.inline_descriptor, InlinePayloadDescriptor):
                _invalid("request.inline_descriptor")
        elif self.inline_descriptor is not None:
            _invalid("request.inline_descriptor")
        if type(self.envelope_authority) is not DeliveryEnvelopeAuthority:
            _invalid("request.envelope_authority")
        if (
            self.envelope_authority.message.message_id != self.message_id
            or self.envelope_authority.message.type != authorization.message_type
            or self.envelope_authority.source.tenant_id != self.tenant_id
        ):
            _invalid("request.envelope_authority_binding")
        if self.requested_priority is not None and not isinstance(
            self.requested_priority, AdmissionPriority
        ):
            _invalid("request.requested_priority")
        if self.requested_reliability is not None and not isinstance(
            self.requested_reliability, AdmissionReliability
        ):
            _invalid("request.requested_reliability")
        object.__setattr__(self, "requested_expires_at", _utc(
            self.requested_expires_at, "request.requested_expires_at"
        ))
        if (isinstance(self.requested_ack_timeout_seconds, bool)
                or not isinstance(self.requested_ack_timeout_seconds, int)
                or self.requested_ack_timeout_seconds <= 0):
            _invalid("request.requested_ack_timeout_seconds")
        if not isinstance(self.requested_target_strategy, RoutingStrategy):
            _invalid("request.requested_target_strategy")
        if self.requested_target_strategy is not self.plan.requested_strategy:
            _invalid("request.plan_strategy")

    @property
    def fingerprint(self) -> str:
        return self.fingerprint_for_config(None)

    def fingerprint_for_config(self, config: AdmissionPolicyConfig | None) -> str:
        payload = self.payload
        if isinstance(payload, InlinePayload):
            inline = self.inline_descriptor
            assert inline is not None
            descriptor = {"kind": "inline", "media_type": inline.media_type,
                          "size_bytes": inline.size_bytes,
                          "digest": inline.digest,
                          "observed_depth": inline.observed_depth,
                          "rejection_reason": (
                              None if inline.rejection_reason is None
                              else inline.rejection_reason.value
                          ),
                          "application_limit": payload.application_limit_bytes,
                          "transport_limit": payload.transport_limit_bytes}
        else:
            descriptor = (
                {"kind": "payload_ref", "object_id": payload.object_id,
                 "version": payload.version, "checksum": payload.checksum,
                 "owner_identity": payload.owner_identity,
                 "callback_message_type": payload.callback_message_type}
            )
        values = {
            "plan_id": self.plan.plan_id,
            "plan_message_reference": self.plan.message_reference,
            "plan_version": self.plan.plan_version,
            "plan_decision_fingerprint": self.plan.decision_fingerprint,
            "message_id": self.message_id, "tenant_id": self.tenant_id,
            "source": self.envelope_authority.source.to_dict(),
            "auth_context": self.envelope_authority.auth_context.to_dict(),
            "protocol": self.envelope_authority.protocol.to_dict(),
            "message": self.envelope_authority.message.to_dict(),
            "trace": self.envelope_authority.trace.to_dict(),
            "payload": descriptor,
            "requested_priority": self.requested_priority.value if self.requested_priority else None,
            "requested_reliability": self.requested_reliability.value if self.requested_reliability else None,
            "requested_expires_at": self.requested_expires_at.isoformat(),
            "requested_ack_timeout_seconds": self.requested_ack_timeout_seconds,
            "requested_target_strategy": self.requested_target_strategy.value,
            "delivery_policy": (None if config is None else {
                "config_version": config.config_version,
                "policy_version": config.policy_version,
                "fanout_shard_threshold": config.fanout_shard_threshold,
                "shard_bucket_size": config.shard_bucket_size,
                "initialization_batch_size": config.initialization_batch_size,
                "activation_batch_size": config.activation_batch_size,
                "authority_bucket_count": config.authority_bucket_count,
            }),
        }
        raw = json.dumps(values, sort_keys=True, separators=(",", ":")).encode()
        return "sha256:" + hashlib.sha256(raw).hexdigest()


class AdmissionPolicy(ABC):
    @abstractmethod
    def decide(
        self, request: AdmissionRequest, *, now: datetime,
        config: AdmissionPolicyConfig,
    ) -> AdmissionPolicyDecision:
        raise NotImplementedError


class DefaultAdmissionPolicy(AdmissionPolicy):
    """Deterministic trusted policy using one immutable config snapshot."""

    def decide(self, request: AdmissionRequest, *, now: datetime,
               config: AdmissionPolicyConfig) -> AdmissionPolicyDecision:
        if not isinstance(request, AdmissionRequest):
            _invalid("policy.request")
        if not isinstance(config, AdmissionPolicyConfig):
            _invalid("policy.config")
        now = _utc(now, "policy.now")
        reason = None
        if (request.inline_descriptor is not None
                and request.inline_descriptor.rejection_reason is not None):
            reason = request.inline_descriptor.rejection_reason
        elif (request.inline_descriptor is not None
              and request.inline_descriptor.observed_depth > config.max_json_depth):
            reason = RejectionReason.INLINE_TOO_DEEP
        elif request.requested_expires_at <= now:
            reason = RejectionReason.EXPIRED
        elif request.requested_expires_at < now + timedelta(
            seconds=config.min_delivery_window_seconds
        ):
            reason = RejectionReason.WINDOW_TOO_SHORT
        priority = request.requested_priority or config.default_priority
        reliability = request.requested_reliability or config.default_reliability
        dependency = {
            AdmissionReliability.BEST_EFFORT: PayloadDependencyDisposition.REJECT,
            AdmissionReliability.AT_LEAST_ONCE: PayloadDependencyDisposition.WAIT_REQUIRED,
            AdmissionReliability.CRITICAL: PayloadDependencyDisposition.DEAD_LETTER_REQUIRED,
        }[reliability]
        return AdmissionPolicyDecision(
            request_fingerprint=request.fingerprint_for_config(config),
            config_version=config.config_version,
            policy_version=config.policy_version,
            accepted=reason is None,
            priority=priority,
            reliability=reliability,
            expires_at=request.requested_expires_at,
            ack_timeout_seconds=min(
                request.requested_ack_timeout_seconds,
                config.max_ack_timeout_seconds,
            ),
            target_strategy=request.plan.effective_strategy,
            dedup_ttl_seconds=config.dedup_ttl_seconds,
            max_inline_bytes=config.max_inline_bytes,
            max_json_depth=config.max_json_depth,
            payload_dependency_disposition=dependency,
            fanout_shard_threshold=config.fanout_shard_threshold,
            shard_bucket_size=config.shard_bucket_size,
            initialization_batch_size=config.initialization_batch_size,
            activation_batch_size=config.activation_batch_size,
            authority_bucket_count=config.authority_bucket_count,
            rejection_reason=reason,
        )


def validate_policy_decision(
    decision: object, *, request: AdmissionRequest,
    config: AdmissionPolicyConfig, now: datetime,
) -> AdmissionPolicyDecision:
    """Revalidate a custom policy response against trusted config and RP-1."""
    if not isinstance(decision, AdmissionPolicyDecision):
        _invalid("policy_result.type")
    now = _utc(now, "policy_result.now")
    if (decision.request_fingerprint != request.fingerprint_for_config(config)
            or decision.config_version != config.config_version
            or decision.policy_version != config.policy_version
            or decision.target_strategy is not request.plan.effective_strategy
            or decision.dedup_ttl_seconds != config.dedup_ttl_seconds
            or decision.max_inline_bytes != config.max_inline_bytes
            or decision.max_json_depth != config.max_json_depth
            or decision.fanout_shard_threshold != config.fanout_shard_threshold
            or decision.shard_bucket_size != config.shard_bucket_size
            or decision.initialization_batch_size != config.initialization_batch_size
            or decision.activation_batch_size != config.activation_batch_size
            or decision.authority_bucket_count != config.authority_bucket_count
            or decision.ack_timeout_seconds > config.max_ack_timeout_seconds
            or decision.ack_timeout_seconds > request.requested_ack_timeout_seconds
            or decision.expires_at != request.requested_expires_at):
        _invalid("policy_result.authority")
    expired = request.requested_expires_at <= now
    short = request.requested_expires_at < now + timedelta(
        seconds=config.min_delivery_window_seconds
    )
    if decision.accepted and (expired or short):
        _invalid("policy_result.expiry_bypass")
    if decision.accepted and request.inline_descriptor is not None and (
        request.inline_descriptor.rejection_reason is not None
        or request.inline_descriptor.observed_depth > config.max_json_depth
    ):
        _invalid("policy_result.inline_descriptor_bypass")
    if (not decision.accepted and decision.rejection_reason is None):
        _invalid("policy_result.rejection")
    return decision


def _utc(value: object, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        _invalid(name)
    return value.astimezone(timezone.utc)


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "P10 admission policy value is invalid.",
        details={"component": "delivery_admission_policy", "field": field_name},
    )


__all__ = (
    "AdmissionPolicy", "AdmissionPolicyConfig", "AdmissionRequest",
    "DefaultAdmissionPolicy", "validate_policy_decision",
)
