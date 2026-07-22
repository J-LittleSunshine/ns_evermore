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
    InlinePayload, PayloadDependencyDisposition, PayloadReference,
    RejectionReason,
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

    def __post_init__(self) -> None:
        for name in ("config_version", "policy_version"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value or len(value) > 256:
                _invalid(f"config.{name}")
        for name in ("max_inline_bytes", "max_json_depth",
                     "min_delivery_window_seconds", "max_ack_timeout_seconds",
                     "dedup_ttl_seconds"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                _invalid(f"config.{name}")
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
    payload: InlinePayload | PayloadReference = field(repr=False)
    requested_priority: AdmissionPriority | None
    requested_reliability: AdmissionReliability | None
    requested_expires_at: datetime
    requested_ack_timeout_seconds: int
    requested_target_strategy: RoutingStrategy

    def __init__(
        self, *, plan: ResolvedRoutingPlan, message_id: str, tenant_id: str,
        source_identity: str, authorization_binding_reference: str,
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
            ("payload", payload), ("requested_priority", requested_priority),
            ("requested_reliability", requested_reliability),
            ("requested_expires_at", requested_expires_at),
            ("requested_ack_timeout_seconds", requested_ack_timeout_seconds),
            ("requested_target_strategy", requested_target_strategy),
        ):
            object.__setattr__(self, name, value)
        self.__post_init__()

    @classmethod
    def from_stage_six(
        cls, *, stage_six: object, message_id: str, tenant_id: str,
        source_identity: str, authorization_binding_reference: str,
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
            payload=payload, requested_priority=requested_priority,
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
        payload = self.payload
        descriptor = (
            {"kind": "inline", "media_type": payload.media_type,
             "application_limit": payload.application_limit_bytes,
             "transport_limit": payload.transport_limit_bytes}
            if isinstance(payload, InlinePayload)
            else {"kind": "payload_ref", "object_id": payload.object_id,
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
            "source_identity": self.source_identity,
            "authorization_binding_reference": self.authorization_binding_reference,
            "payload": descriptor,
            "requested_priority": self.requested_priority.value if self.requested_priority else None,
            "requested_reliability": self.requested_reliability.value if self.requested_reliability else None,
            "requested_expires_at": self.requested_expires_at.isoformat(),
            "requested_ack_timeout_seconds": self.requested_ack_timeout_seconds,
            "requested_target_strategy": self.requested_target_strategy.value,
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
        if request.requested_expires_at <= now:
            reason = RejectionReason.EXPIRED
        elif request.requested_expires_at < now + timedelta(
            seconds=config.min_delivery_window_seconds
        ):
            reason = RejectionReason.WINDOW_TOO_SHORT
        priority = request.requested_priority or config.default_priority
        reliability = request.requested_reliability or config.default_reliability
        dependency = {
            AdmissionReliability.BEST_EFFORT: PayloadDependencyDisposition.REJECT,
            AdmissionReliability.AT_LEAST_ONCE: PayloadDependencyDisposition.WAIT,
            AdmissionReliability.CRITICAL: PayloadDependencyDisposition.DEAD_LETTER,
        }[reliability]
        return AdmissionPolicyDecision(
            request_fingerprint=request.fingerprint,
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
    if (decision.request_fingerprint != request.fingerprint
            or decision.config_version != config.config_version
            or decision.policy_version != config.policy_version
            or decision.target_strategy is not request.plan.effective_strategy
            or decision.dedup_ttl_seconds != config.dedup_ttl_seconds
            or decision.max_inline_bytes != config.max_inline_bytes
            or decision.max_json_depth != config.max_json_depth
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
