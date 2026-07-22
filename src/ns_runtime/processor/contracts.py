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
    """Immutable stage-two value bound to one message authorization check."""

    decision_reference: str = field(repr=False)
    decision_version: str
    message_reference: str
    message_type: str
    principal_tenant_id: str = field(repr=False)
    effective_tenant_id: str = field(repr=False)
    cross_tenant_authorized: bool
    authorized_target_reference: str = field(repr=False)
    permission_snapshot_ref: str = field(repr=False)
    permission_snapshot_version: str = field(repr=False)

    def __post_init__(self) -> None:
        if _DECISION_REFERENCE.fullmatch(self.decision_reference) is None:
            _invalid("authorization_evidence.decision_reference")
        if _SAFE_REFERENCE.fullmatch(self.message_reference) is None:
            _invalid("authorization_evidence.message_reference")
        if _SAFE_REFERENCE.fullmatch(self.authorized_target_reference) is None:
            _invalid("authorization_evidence.authorized_target_reference")
        for name in (
            "decision_version", "message_type", "principal_tenant_id",
            "effective_tenant_id",
            "permission_snapshot_ref", "permission_snapshot_version",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value or len(value) > 512:
                _invalid(f"authorization_evidence.{name}")
        if type(self.cross_tenant_authorized) is not bool:
            _invalid("authorization_evidence.cross_tenant_authorized")

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
