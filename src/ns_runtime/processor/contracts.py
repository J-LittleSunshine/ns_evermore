# -*- coding: utf-8 -*-
"""PC-1 processor contracts with explicit, per-runtime dependencies."""

from __future__ import annotations

import hashlib
import json
import math
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import TYPE_CHECKING, Mapping

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import NsValidationError
from ns_common.time import Clock
from ns_common.iam import IamPrincipalType
from ns_runtime.protocol import Envelope, ProtocolVersion, TargetGroup

if TYPE_CHECKING:
    from ns_runtime.connection.session import SessionContext
    from .audit import AuditSink
    from .event_bus import EventBus


_NAME = re.compile(r"[a-z][a-z0-9_]*(?:[.:-][a-z0-9_]+)*")
_SAFE_REFERENCE = re.compile(r"sha256:[0-9a-f]{16}")
_DECISION_REFERENCE = re.compile(r"sha256:[0-9a-f]{64}")


class ProcessorStage(str, Enum):
    SECURITY_VALIDATION = "security_validation"
    AUTHORIZATION = "authorization"
    RATE_LIMIT_ENTRY = "rate_limit_entry"
    IDEMPOTENCY_PRECHECK = "idempotency_precheck"
    AUDIT_MARKER = "audit_marker"
    ROUTING_PREPARATION = "routing_preparation"
    MESSAGE_PROCESSOR = "message_processor"
    RESPONSE_FINALIZE = "response_finalize"


class AuthorizationDecisionOutcome(str, Enum):
    """The only successful stage-two authorization outcome."""

    ALLOW = "allow"


PROCESSOR_STAGE_ORDER: tuple[ProcessorStage, ...] = (
    ProcessorStage.SECURITY_VALIDATION,
    ProcessorStage.AUTHORIZATION,
    ProcessorStage.RATE_LIMIT_ENTRY,
    ProcessorStage.IDEMPOTENCY_PRECHECK,
    ProcessorStage.AUDIT_MARKER,
    ProcessorStage.ROUTING_PREPARATION,
    ProcessorStage.MESSAGE_PROCESSOR,
    ProcessorStage.RESPONSE_FINALIZE,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessorTraceReference:
    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str) or not self.value or len(self.value) > 512:
            _invalid("trace.value")

    @classmethod
    def from_envelope(cls, envelope: Envelope) -> "ProcessorTraceReference":
        if not isinstance(envelope, Envelope):
            _invalid("envelope")
        trace = envelope.trace
        if trace is not None:
            for value in (
                trace.trace_id,
                trace.correlation_id,
                trace.request_id,
                trace.span_id,
            ):
                if value:
                    return cls(value=value)
        digest = hashlib.sha256(
            envelope.message.message_id.encode("utf-8"),
        ).hexdigest()[:16]
        return cls(value=f"sha256:{digest}")


@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessorSafeSummary:
    message_type: str
    category: str
    object_reference: str

    def __post_init__(self) -> None:
        for name in ("message_type", "category"):
            value = getattr(self, name)
            if not isinstance(value, str) or _NAME.fullmatch(value) is None:
                _invalid(f"safe_summary.{name}")
        if (
            not isinstance(self.object_reference, str)
            or re.fullmatch(r"sha256:[0-9a-f]{16}", self.object_reference) is None
        ):
            _invalid("safe_summary.object_reference")

    @classmethod
    def from_envelope(cls, envelope: Envelope) -> "ProcessorSafeSummary":
        if not isinstance(envelope, Envelope):
            _invalid("envelope")
        digest = hashlib.sha256(
            envelope.message.message_id.encode("utf-8"),
        ).hexdigest()[:16]
        return cls(
            message_type=envelope.message.type,
            category=envelope.message.category,
            object_reference=f"sha256:{digest}",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class AuthorizationDecisionEvidence:
    """Immutable ALLOW evidence bound to one message authorization check."""

    message_binding_reference: str = field(repr=False)
    semantic_decision_reference: str = field(repr=False)
    semantic_access_check_reference: str = field(repr=False)
    decision_version: str
    decision_outcome: AuthorizationDecisionOutcome
    decision_reason: str
    message_reference: str
    message_type: str
    principal_tenant_id: str = field(repr=False)
    effective_tenant_id: str = field(repr=False)
    cross_tenant_authorized: bool
    authorized_target_reference: str = field(repr=False)
    session_permission_snapshot_ref: str = field(repr=False)
    session_permission_snapshot_version: str = field(repr=False)
    effective_permission_snapshot_ref: str = field(repr=False)
    effective_permission_snapshot_version: str = field(repr=False)

    def __post_init__(self) -> None:
        for name in (
            "message_binding_reference",
            "semantic_decision_reference",
            "semantic_access_check_reference",
        ):
            if _DECISION_REFERENCE.fullmatch(getattr(self, name)) is None:
                _invalid(f"authorization_evidence.{name}")
        if _SAFE_REFERENCE.fullmatch(self.message_reference) is None:
            _invalid("authorization_evidence.message_reference")
        if _SAFE_REFERENCE.fullmatch(self.authorized_target_reference) is None:
            _invalid("authorization_evidence.authorized_target_reference")
        for name in (
            "decision_version", "decision_reason",
            "message_type", "principal_tenant_id", "effective_tenant_id",
            "session_permission_snapshot_ref",
            "session_permission_snapshot_version",
            "effective_permission_snapshot_ref",
            "effective_permission_snapshot_version",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value or len(value) > 512:
                _invalid(f"authorization_evidence.{name}")
        if self.decision_outcome is not AuthorizationDecisionOutcome.ALLOW:
            _invalid("authorization_evidence.decision_outcome")
        if type(self.cross_tenant_authorized) is not bool:
            _invalid("authorization_evidence.cross_tenant_authorized")
        if (
            self.effective_permission_snapshot_ref
            != self.session_permission_snapshot_ref
        ):
            _invalid("authorization_evidence.permission_snapshot_ref_refresh")
        if not self.has_valid_semantic_decision():
            _invalid("authorization_evidence.semantic_decision_reference")
        if not self.has_valid_message_binding():
            _invalid("authorization_evidence.message_binding_reference")

    @classmethod
    def bound(
        cls,
        *,
        decision_version: str,
        decision_outcome: AuthorizationDecisionOutcome,
        decision_reason: str,
        semantic_access_check_reference: str,
        message_reference: str,
        message_type: str,
        principal_tenant_id: str,
        effective_tenant_id: str,
        cross_tenant_authorized: bool,
        authorized_target_reference: str,
        session_permission_snapshot_ref: str,
        session_permission_snapshot_version: str,
        effective_permission_snapshot_ref: str,
        effective_permission_snapshot_version: str,
    ) -> "AuthorizationDecisionEvidence":
        if decision_outcome is not AuthorizationDecisionOutcome.ALLOW:
            _invalid("authorization_evidence.decision_outcome")
        semantic_values = {
            "decision_version": decision_version,
            "decision_outcome": decision_outcome.value,
            "decision_reason": decision_reason,
            "semantic_access_check_reference": semantic_access_check_reference,
            "message_type": message_type,
            "principal_tenant_id": principal_tenant_id,
            "effective_tenant_id": effective_tenant_id,
            "cross_tenant_authorized": cross_tenant_authorized,
            "authorized_target_reference": authorized_target_reference,
            "effective_permission_snapshot_ref": effective_permission_snapshot_ref,
            "effective_permission_snapshot_version": effective_permission_snapshot_version,
        }
        semantic_decision_reference = cls._reference(semantic_values)
        binding_values = {
            "message_reference": message_reference,
            "message_type": message_type,
            "principal_tenant_id": principal_tenant_id,
            "effective_tenant_id": effective_tenant_id,
            "cross_tenant_authorized": cross_tenant_authorized,
            "authorized_target_reference": authorized_target_reference,
            "session_permission_snapshot_ref": session_permission_snapshot_ref,
            "session_permission_snapshot_version": session_permission_snapshot_version,
            "effective_permission_snapshot_ref": effective_permission_snapshot_ref,
            "effective_permission_snapshot_version": effective_permission_snapshot_version,
            "semantic_decision_reference": semantic_decision_reference,
        }
        return cls(
            message_binding_reference=cls._reference(binding_values),
            semantic_decision_reference=semantic_decision_reference,
            semantic_access_check_reference=semantic_access_check_reference,
            decision_version=decision_version,
            decision_outcome=decision_outcome,
            decision_reason=decision_reason,
            message_reference=message_reference,
            message_type=message_type,
            principal_tenant_id=principal_tenant_id,
            effective_tenant_id=effective_tenant_id,
            cross_tenant_authorized=cross_tenant_authorized,
            authorized_target_reference=authorized_target_reference,
            session_permission_snapshot_ref=session_permission_snapshot_ref,
            session_permission_snapshot_version=session_permission_snapshot_version,
            effective_permission_snapshot_ref=effective_permission_snapshot_ref,
            effective_permission_snapshot_version=effective_permission_snapshot_version,
        )

    def has_valid_semantic_decision(self) -> bool:
        return self.semantic_decision_reference == self._reference({
            "decision_version": self.decision_version,
            "decision_outcome": self.decision_outcome.value,
            "decision_reason": self.decision_reason,
            "semantic_access_check_reference": self.semantic_access_check_reference,
            "message_type": self.message_type,
            "principal_tenant_id": self.principal_tenant_id,
            "effective_tenant_id": self.effective_tenant_id,
            "cross_tenant_authorized": self.cross_tenant_authorized,
            "authorized_target_reference": self.authorized_target_reference,
            "effective_permission_snapshot_ref": self.effective_permission_snapshot_ref,
            "effective_permission_snapshot_version": self.effective_permission_snapshot_version,
        })

    def has_valid_message_binding(self) -> bool:
        return self.message_binding_reference == self._reference({
            "message_reference": self.message_reference,
            "message_type": self.message_type,
            "principal_tenant_id": self.principal_tenant_id,
            "effective_tenant_id": self.effective_tenant_id,
            "cross_tenant_authorized": self.cross_tenant_authorized,
            "authorized_target_reference": self.authorized_target_reference,
            "session_permission_snapshot_ref": self.session_permission_snapshot_ref,
            "session_permission_snapshot_version": self.session_permission_snapshot_version,
            "effective_permission_snapshot_ref": self.effective_permission_snapshot_ref,
            "effective_permission_snapshot_version": self.effective_permission_snapshot_version,
            "semantic_decision_reference": self.semantic_decision_reference,
        })

    def has_valid_binding(self) -> bool:
        return self.has_valid_semantic_decision() and self.has_valid_message_binding()

    @staticmethod
    def _reference(values: Mapping[str, object]) -> str:
        canonical = json.dumps(values, sort_keys=True, separators=(",", ":"))
        return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @staticmethod
    def target_reference(target: TargetGroup | None, *, session_tenant_id: str) -> str:
        if not isinstance(session_tenant_id, str) or not session_tenant_id:
            _invalid("authorization_evidence.session_tenant_id")
        if target is not None and not isinstance(target, TargetGroup):
            _invalid("authorization_evidence.target")
        payload = (
            {"kind": "session", "tenant_id": session_tenant_id}
            if target is None
            else target.to_dict()
        )
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


class ProcessorAuthorization(ABC):
    """Return validated ALLOW evidence or raise; DENY is not a success value."""

    @abstractmethod
    async def authorize(
        self,
        context: "ProcessorContext",
    ) -> AuthorizationDecisionEvidence:
        raise NotImplementedError


class RateLimitEntry(ABC):
    """P07 interface only; implementations must not create authority state."""

    @abstractmethod
    async def enter(self, context: "ProcessorContext") -> None:
        raise NotImplementedError


class IdempotencyPrecheck(ABC):
    """P07 interface only; no idempotency store exists in this phase."""

    @abstractmethod
    async def precheck(self, context: "ProcessorContext") -> None:
        raise NotImplementedError


class RoutingPreparation(ABC):
    """Prepare one trusted routing result for the fixed pipeline stage."""

    @abstractmethod
    async def prepare(
        self,
        context: "ProcessorContext",
        value: object,
    ) -> "RoutingPreparationResult":
        raise NotImplementedError


class RoutingPreparationOutcome(str, Enum):
    NO_ROUTING_REQUIRED = "no_routing_required"
    RESOLVED = "resolved"
    REJECTED = "rejected"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True, kw_only=True)
class RoutingPreparationResult:
    outcome: RoutingPreparationOutcome
    plan: object | None = field(default=None, repr=False)
    failure: object | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, RoutingPreparationOutcome):
            _invalid("routing_result.outcome")
        if self.outcome is RoutingPreparationOutcome.NO_ROUTING_REQUIRED:
            if self.plan is not None or self.failure is not None:
                _invalid("routing_result.no_routing_payload")
        elif self.outcome is RoutingPreparationOutcome.RESOLVED:
            if self.plan is None or self.failure is not None:
                _invalid("routing_result.resolved_payload")
        elif self.plan is not None or self.failure is None:
            _invalid("routing_result.failure_payload")

    @classmethod
    def no_routing_required(cls) -> "RoutingPreparationResult":
        return cls(outcome=RoutingPreparationOutcome.NO_ROUTING_REQUIRED)

    @classmethod
    def resolved(cls, plan: object) -> "RoutingPreparationResult":
        return cls(outcome=RoutingPreparationOutcome.RESOLVED, plan=plan)

    @classmethod
    def rejected(cls, failure: object) -> "RoutingPreparationResult":
        return cls(outcome=RoutingPreparationOutcome.REJECTED, failure=failure)

    @classmethod
    def unavailable(cls, failure: object) -> "RoutingPreparationResult":
        return cls(outcome=RoutingPreparationOutcome.UNAVAILABLE, failure=failure)


class MessageProcessor(ABC):
    """Message-specific binding executed only by the fixed pipeline stage."""

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def process(self, context: "ProcessorContext", value: object) -> object:
        raise NotImplementedError


class MessageProcessorExecutionBoundary(ABC):
    """Marker contract required for MESSAGE_PROCESSOR registry entries."""

    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    async def process(self, context: "ProcessorContext", value: object) -> object:
        raise NotImplementedError


class ResponseFinalizer(ABC):
    @abstractmethod
    async def finalize(self, context: "ProcessorContext", response: object) -> object:
        raise NotImplementedError


class ProcessorErrorMapper(ABC):
    @abstractmethod
    def map_error(self, error: Exception) -> Exception:
        raise NotImplementedError


@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessorDependencies:
    authorization: ProcessorAuthorization
    rate_limit: RateLimitEntry
    idempotency: IdempotencyPrecheck
    routing: RoutingPreparation
    response_finalizer: ResponseFinalizer
    error_mapper: ProcessorErrorMapper
    principal_type: IamPrincipalType
    audit_sink: AuditSink = field(repr=False)
    event_bus: EventBus = field(repr=False)
    task_supervisor: TaskSupervisor = field(repr=False)

    def __post_init__(self) -> None:
        expected = (
            (self.authorization, ProcessorAuthorization, "authorization"),
            (self.rate_limit, RateLimitEntry, "rate_limit"),
            (self.idempotency, IdempotencyPrecheck, "idempotency"),
            (self.routing, RoutingPreparation, "routing"),
            (self.response_finalizer, ResponseFinalizer, "response_finalizer"),
            (self.error_mapper, ProcessorErrorMapper, "error_mapper"),
            (self.task_supervisor, TaskSupervisor, "task_supervisor"),
        )
        for value, value_type, name in expected:
            if not isinstance(value, value_type):
                _invalid(f"dependencies.{name}")
        if not isinstance(self.principal_type, IamPrincipalType):
            _invalid("dependencies.principal_type")
        from .audit import AuditSink
        from .event_bus import EventBus

        if not isinstance(self.audit_sink, AuditSink):
            _invalid("dependencies.audit_sink")
        if not isinstance(self.event_bus, EventBus):
            _invalid("dependencies.event_bus")


@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessorContext:
    normalized_envelope: Envelope = field(repr=False)
    session: SessionContext = field(repr=False)
    trace: ProcessorTraceReference
    config_version: str
    policy_version: str
    clock: Clock = field(repr=False)
    dependencies: ProcessorDependencies = field(repr=False)

    def __post_init__(self) -> None:
        from ns_runtime.connection.session import SessionContext

        if not isinstance(self.normalized_envelope, Envelope):
            _invalid("normalized_envelope")
        if self.normalized_envelope.source is None or self.normalized_envelope.auth_context is None:
            _invalid("normalized_envelope.authority")
        if not isinstance(self.session, SessionContext):
            _invalid("session")
        if not isinstance(self.trace, ProcessorTraceReference):
            _invalid("trace")
        for name in ("config_version", "policy_version"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value or len(value) > 256:
                _invalid(name)
        if not isinstance(self.clock, Clock):
            _invalid("clock")
        if not isinstance(self.dependencies, ProcessorDependencies):
            _invalid("dependencies")

    @property
    def envelope(self) -> Envelope:
        return self.normalized_envelope

    @property
    def protocol_version(self) -> ProtocolVersion:
        return ProtocolVersion.from_group(self.normalized_envelope.protocol)


@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessorExecutionPolicy:
    timeout_seconds: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.timeout_seconds, bool)
            or not isinstance(self.timeout_seconds, (int, float))
            or not math.isfinite(float(self.timeout_seconds))
            or float(self.timeout_seconds) <= 0
        ):
            _invalid("timeout_seconds")
        object.__setattr__(self, "timeout_seconds", float(self.timeout_seconds))


def freeze_feature_flags(value: Mapping[str, bool]) -> Mapping[str, bool]:
    if not isinstance(value, Mapping):
        _invalid("feature_flags")
    frozen: dict[str, bool] = {}
    for name, enabled in value.items():
        if not isinstance(name, str) or _NAME.fullmatch(name) is None:
            _invalid("feature_flags.name")
        if type(enabled) is not bool:
            _invalid("feature_flags.enabled")
        frozen[name] = enabled
    return MappingProxyType(frozen)


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Processor contract value is invalid.",
        details={"component": "processor", "field": field_name},
    )


__all__ = (
    "AuthorizationDecisionOutcome",
    "AuthorizationDecisionEvidence",
    "IdempotencyPrecheck",
    "MessageProcessor",
    "MessageProcessorExecutionBoundary",
    "PROCESSOR_STAGE_ORDER",
    "ProcessorAuthorization",
    "ProcessorContext",
    "ProcessorDependencies",
    "ProcessorErrorMapper",
    "ProcessorExecutionPolicy",
    "ProcessorSafeSummary",
    "ProcessorStage",
    "ProcessorTraceReference",
    "RateLimitEntry",
    "ResponseFinalizer",
    "RoutingPreparation",
    "RoutingPreparationOutcome",
    "RoutingPreparationResult",
    "freeze_feature_flags",
)
