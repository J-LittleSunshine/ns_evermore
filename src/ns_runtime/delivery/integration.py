# -*- coding: utf-8 -*-
"""PC-1 stage-six to P10 admission adapter (not production-registered)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from ns_common.exceptions import NsValidationError
from ns_runtime.processor import (
    MessageProcessor, ProcessorContext, RoutingPreparationOutcome,
    RoutingPreparationResult,
)
from ns_runtime.routing import ResolvedRoutingPlan

from .models import (
    AdmissionOutcome, AdmissionPriority, AdmissionReliability, AdmissionTrace,
    InlinePayload,
    PayloadReference,
)
from .dispatch import LocalDeliveryDispatchCoordinator
from .policy import AdmissionPolicyConfig, AdmissionRequest
from .service import DeliveryAdmissionService


class AdmissionRequestFactory(ABC):
    @abstractmethod
    def from_stage_six(
        self, *, context: ProcessorContext, stage_six: "StageSixAdmissionInput",
    ) -> AdmissionRequest:
        raise NotImplementedError


_STAGE_SIX_ISSUER = object()


@dataclass(frozen=True, slots=True, init=False)
class StageSixAdmissionInput:
    """Typed hand-off token; raw plans and wire mappings are never accepted."""

    plan: ResolvedRoutingPlan = field(repr=False)

    def __init__(self, *, plan: ResolvedRoutingPlan, _issuer: object = None) -> None:
        if _issuer is not _STAGE_SIX_ISSUER:
            _invalid("stage_six.issuer")
        if not isinstance(plan, ResolvedRoutingPlan):
            _invalid("stage_six.plan")
        object.__setattr__(self, "plan", plan)

    @classmethod
    def from_result(cls, value: object) -> "StageSixAdmissionInput":
        if (not isinstance(value, RoutingPreparationResult)
                or value.outcome is not RoutingPreparationOutcome.RESOLVED
                or not isinstance(value.plan, ResolvedRoutingPlan)
                or value.failure is not None):
            _invalid("stage_six.result")
        return cls(plan=value.plan, _issuer=_STAGE_SIX_ISSUER)

    def __post_init__(self) -> None:
        if not isinstance(self.plan, ResolvedRoutingPlan):
            _invalid("stage_six.plan")


class EnvelopeAdmissionRequestFactory(AdmissionRequestFactory):
    """Map frozen ENV-1 groups into requests; it never alters the RP-1 plan."""

    def __init__(self, *, config: AdmissionPolicyConfig) -> None:
        if not isinstance(config, AdmissionPolicyConfig):
            _invalid("factory.config")
        self._config = config

    def from_stage_six(
        self, *, context: ProcessorContext, stage_six: StageSixAdmissionInput,
    ) -> AdmissionRequest:
        if not isinstance(context, ProcessorContext):
            _invalid("factory.context")
        if not isinstance(stage_six, StageSixAdmissionInput):
            _invalid("factory.stage_six")
        plan = stage_six.plan
        envelope = context.envelope
        if envelope.message.type != "task.dispatch" or envelope.payload is None:
            _invalid("factory.message_contract")
        payload_group = envelope.payload
        if payload_group.mode == "inline":
            payload = InlinePayload(
                value=payload_group.inline, media_type=payload_group.content_type or "application/json",
                application_limit_bytes=self._config.max_inline_bytes,
                transport_limit_bytes=self._config.max_inline_bytes,
            )
        else:
            raw = payload_group.payload_ref
            if raw is None or set(raw) != {"object_id", "owner_identity"}:
                _invalid("factory.payload_ref")
            object_id = raw.get("object_id")
            owner_identity = raw.get("owner_identity")
            if (not isinstance(object_id, str) or not isinstance(owner_identity, str)
                    or payload_group.version is None or payload_group.checksum is None):
                _invalid("factory.payload_ref_metadata")
            payload = PayloadReference(
                object_id=object_id, version=payload_group.version,
                checksum=payload_group.checksum,
                owner_identity=owner_identity,
                callback_message_type=(
                    envelope.callback.message_type if envelope.callback else None
                ),
            )
        requested_expires_at = (
            _parse_time(envelope.message.expires_at)
            if envelope.message.expires_at is not None
            else context.clock.utc_now() + timedelta(seconds=max(
                self._config.min_delivery_window_seconds,
                self._config.max_ack_timeout_seconds,
            ))
        )
        return AdmissionRequest.from_stage_six(
            stage_six=stage_six, message_id=envelope.message.message_id,
            tenant_id=plan.authorization_evidence.effective_tenant_id,
            source_identity=context.session.identity,
            authorization_binding_reference=(
                plan.authorization_evidence.message_binding_reference
            ),
            payload=payload,
            requested_priority=_priority(envelope.message.priority),
            requested_reliability=_reliability(envelope.message.reliability),
            requested_expires_at=requested_expires_at,
            requested_ack_timeout_seconds=self._config.max_ack_timeout_seconds,
            requested_target_strategy=plan.requested_strategy,
        )


class DeliveryAdmissionMessageProcessor(MessageProcessor):
    """Consumes exactly RoutingPreparationResult.RESOLVED from PC-1 stage six.

    It is not production-registered while ``task.dispatch`` remains disabled.
    P10/P11 tests and local experiments may compose it explicitly.
    """

    def __init__(self, *, service: DeliveryAdmissionService,
                 request_factory: AdmissionRequestFactory) -> None:
        if not isinstance(service, DeliveryAdmissionService):
            _invalid("processor.service")
        if not isinstance(request_factory, AdmissionRequestFactory):
            _invalid("processor.request_factory")
        self._service = service
        self._factory = request_factory

    @property
    def name(self) -> str:
        return "delivery.admission.dr1"

    async def process(self, context: ProcessorContext, value: object) -> object:
        if not isinstance(context, ProcessorContext):
            _invalid("processor.context")
        stage_six = StageSixAdmissionInput.from_result(value)
        request = self._factory.from_stage_six(context=context, stage_six=stage_six)
        if not isinstance(request, AdmissionRequest) or request.plan is not stage_six.plan:
            _invalid("processor.request_factory_result")
        return await self._service.admit(
            request, trace=AdmissionTrace(trace_id=context.trace.value),
        )


class LocalTaskDispatchExperimentalProcessor(MessageProcessor):
    """P11 local-only admission plus supervised dispatch wakeup.

    The returned value remains the frozen P10 admission result. Scheduling is
    post-commit and cannot rewrite an accepted result during shutdown.
    """

    def __init__(
        self,
        *,
        admission: DeliveryAdmissionMessageProcessor,
        coordinator: LocalDeliveryDispatchCoordinator,
    ) -> None:
        if not isinstance(admission, DeliveryAdmissionMessageProcessor):
            _invalid("experimental.admission")
        if not isinstance(coordinator, LocalDeliveryDispatchCoordinator):
            _invalid("experimental.coordinator")
        self._admission = admission
        self._coordinator = coordinator

    @property
    def name(self) -> str:
        return "delivery.local_dispatch.p11.experimental"

    async def process(self, context: ProcessorContext, value: object) -> object:
        stage_six = StageSixAdmissionInput.from_result(value)
        result = await self._admission.process(context, value)
        if result.outcome is AdmissionOutcome.ACCEPTED and result.committed:
            self._coordinator.schedule(
                tenant_id=stage_six.plan.authorization_evidence.effective_tenant_id,
            )
        return result


def _priority(value: int) -> AdmissionPriority:
    if isinstance(value, bool) or not isinstance(value, int):
        _invalid("factory.priority")
    if value <= 0:
        return AdmissionPriority.LOW
    if value == 1:
        return AdmissionPriority.NORMAL
    if value == 2:
        return AdmissionPriority.HIGH
    return AdmissionPriority.CRITICAL


def _reliability(value: str) -> AdmissionReliability:
    mapping = {
        "best_effort": AdmissionReliability.BEST_EFFORT,
        "at_least_once": AdmissionReliability.AT_LEAST_ONCE,
        "critical": AdmissionReliability.CRITICAL,
    }
    try:
        return mapping[value]
    except (KeyError, TypeError):
        _invalid("factory.reliability")


def _parse_time(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        _invalid("factory.expires_at")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        _invalid("factory.expires_at")
    return parsed.astimezone(timezone.utc)


def _invalid(field: str) -> None:
    raise NsValidationError(
        "P10 processor integration value is invalid.",
        details={"component": "delivery_admission_integration", "field": field},
    )


__all__ = (
    "AdmissionRequestFactory", "DeliveryAdmissionMessageProcessor",
    "EnvelopeAdmissionRequestFactory", "StageSixAdmissionInput",
    "LocalTaskDispatchExperimentalProcessor",
)
