# -*- coding: utf-8 -*-
"""Adapters that place existing connection processors behind PC-1."""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING, Callable, Mapping

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import NsRuntimeIamDeniedError, NsValidationError
from ns_common.iam import IamAccessCheckRequest, IamPrincipalType, IamTargetContext
from ns_common.time import Clock
from ns_runtime.protocol import (
    BUILTIN_MESSAGE_REGISTRY,
    Envelope,
    ErrorEnvelopeContext,
    FeatureDisabledProcessor,
    MessageCategory,
    MessageDirection,
    MessageTypeContract,
    MessageTypeRegistry,
    ProtocolVersion,
    canonical_serialize,
)
from ns_runtime.transport import TransportSession

from .audit import AuditConsistency, AuditSink
from .contracts import (
    PROCESSOR_STAGE_ORDER,
    AuthorizationDecisionEvidence,
    ProcessorAuthorization,
    ProcessorContext,
    ProcessorDependencies,
    ProcessorErrorMapper,
    ProcessorExecutionPolicy,
    ProcessorSafeSummary,
    MessageProcessor,
    ProcessorStage,
    ResponseFinalizer,
    IdempotencyPrecheck,
    RateLimitEntry,
    RoutingPreparation,
    RoutingPreparationOutcome,
    RoutingPreparationResult,
)
from .event_bus import EventBus
from .pipeline import ProcessorExecutionResult, ProcessorPipeline, build_standard_stage_processors
from .registry import PipelineProcessor, ProcessorRegistration, ProcessorRegistry

if TYPE_CHECKING:
    from ns_runtime.connection.processors import ConnectionLifecycleProcessorRegistry
    from ns_runtime.connection.session import SessionContext
    from ns_runtime.iam import MessageAuthorizationService, OperationRiskContext


class IamProcessorAuthorization(ProcessorAuthorization):
    def __init__(
        self,
        *,
        service: MessageAuthorizationService,
        protocol_registry: MessageTypeRegistry = BUILTIN_MESSAGE_REGISTRY,
    ) -> None:
        from ns_runtime.iam import MessageAuthorizationService

        if not isinstance(service, MessageAuthorizationService):
            _invalid("authorization.service")
        if not isinstance(protocol_registry, MessageTypeRegistry):
            _invalid("authorization.protocol_registry")
        self._service = service
        self._registry = protocol_registry

    async def authorize(
        self,
        context: ProcessorContext,
    ) -> AuthorizationDecisionEvidence:
        from ns_runtime.iam import PermissionSnapshot

        if not isinstance(context, ProcessorContext):
            _invalid("authorization.context")
        contract = self._registry.require(context.envelope.message.type)
        session = context.session
        target = _target_context(context)
        crosses_tenant = (
            target.tenant_id is not None
            and target.tenant_id != session.tenant_id
        )
        management = (
            "runtime.management" in contract.required_capabilities
            or contract.category in {
                MessageCategory.CONTROL,
                MessageCategory.CLUSTER,
                MessageCategory.CONFIG,
                MessageCategory.MANAGEMENT,
            }
        )
        request = IamAccessCheckRequest(
            identity=session.identity,
            tenant_id=session.tenant_id,
            permission_snapshot_ref=session.permission_snapshot_ref,
            permission_version=session.permission_version,
            message_type=contract.message_type,
            target=target,
            cross_tenant=crosses_tenant,
            management=management,
            task_creation=contract.message_type == "task.dispatch",
        )
        snapshot = PermissionSnapshot(
            identity=session.identity,
            tenant_id=session.tenant_id,
            principal_type=context.dependencies.principal_type,
            component_type=session.component_type,
            capabilities=session.capabilities,
            permission_snapshot_ref=session.permission_snapshot_ref,
            permission_digest=session.permission_digest,
            permission_version=session.permission_version,
            iam_mode=session.iam_mode,
            issued_at=session.authorization_issued_at,
            expires_at=session.session_expires_at,
            resume_eligible=session.resume_eligible,
        )
        effective, decision = await self._service.authorize(
            snapshot=snapshot,
            request=request,
            risk=_risk_context(contract, crosses_tenant=crosses_tenant),
        )
        return _authorization_evidence(
            context=context,
            request=request,
            effective_snapshot=effective,
            decision=decision,
        )


class DeterministicTestProcessorAuthorization(ProcessorAuthorization):
    """Explicit test boundary; production composition uses IAM-R1 above."""

    def __init__(
        self,
        *,
        allowed: bool = True,
        authorize_cross_tenant: bool = False,
    ) -> None:
        if type(allowed) is not bool or type(authorize_cross_tenant) is not bool:
            _invalid("test_authorization.allowed")
        self.allowed = allowed
        self.authorize_cross_tenant = authorize_cross_tenant
        self.calls: list[ProcessorContext] = []

    async def authorize(
        self,
        context: ProcessorContext,
    ) -> AuthorizationDecisionEvidence:
        if not isinstance(context, ProcessorContext):
            _invalid("test_authorization.context")
        self.calls.append(context)
        if not self.allowed:
            raise NsRuntimeIamDeniedError(
                details={
                    "component": "processor_authorization",
                    "operation": "authorize",
                    "reason": "deterministic_test_denial",
                },
            )
        target = context.envelope.target
        target_reference = AuthorizationDecisionEvidence.target_reference(
            target,
            session_tenant_id=context.session.tenant_id,
        )
        message_reference = ProcessorSafeSummary.from_envelope(
            context.envelope,
        ).object_reference
        target_tenant = None if target is None else target.tenant_id
        crosses_tenant = (
            target_tenant is not None
            and target_tenant != context.session.tenant_id
        )
        if crosses_tenant and not self.authorize_cross_tenant:
            raise NsRuntimeIamDeniedError(
                details={
                    "component": "processor_authorization",
                    "operation": "authorize",
                    "reason": "cross_tenant_not_authorized_by_test_policy",
                },
            )
        semantic_access_payload = {
            "identity": context.session.identity,
            "tenant_id": context.session.tenant_id,
            "message_type": context.envelope.message.type,
            "permission_snapshot_ref": context.session.permission_snapshot_ref,
            "permission_version": context.session.permission_version,
            "target_reference": target_reference,
            "cross_tenant": crosses_tenant,
            "management": False,
            "task_creation": context.envelope.message.type == "task.dispatch",
        }
        return AuthorizationDecisionEvidence.bound(
            decision_version="authorization-decision.v1",
            decision_classification="allow",
            decision_reason="deterministic_allow",
            semantic_access_check_reference=_decision_digest(
                semantic_access_payload,
            ),
            message_reference=message_reference,
            message_type=context.envelope.message.type,
            principal_tenant_id=context.session.tenant_id,
            effective_tenant_id=(target_tenant if crosses_tenant else context.session.tenant_id),
            cross_tenant_authorized=(
                self.authorize_cross_tenant if crosses_tenant else False
            ),
            authorized_target_reference=target_reference,
            session_permission_snapshot_ref=(
                context.session.permission_snapshot_ref
            ),
            session_permission_snapshot_version=context.session.permission_version,
            effective_permission_snapshot_ref=(
                context.session.permission_snapshot_ref
            ),
            effective_permission_snapshot_version=context.session.permission_version,
        )


class CanonicalResponseFinalizer(ResponseFinalizer):
    """Pure stage-eight response construction; it has no transport owner."""
    async def finalize(self, context: ProcessorContext, response: object) -> object:
        if not isinstance(context, ProcessorContext):
            _invalid("response_finalizer.context")
        if isinstance(response, Envelope):
            canonical_serialize(response)
        return response


class TransportResponseEmitter:
    """Composition-owned transport side effect after final audit succeeds."""

    def __init__(self, *, transport: TransportSession) -> None:
        if not isinstance(transport, TransportSession):
            _invalid("response_emitter.transport")
        self._transport = transport

    async def emit(self, result: ProcessorExecutionResult) -> bool:
        if not isinstance(result, ProcessorExecutionResult):
            _invalid("response_emitter.result")
        if not result.succeeded or result.response is None:
            return False
        if not isinstance(result.response, Envelope):
            return False
        await self._transport.send(
            canonical_serialize(result.response).decode("utf-8"),
        )
        return True


class LifecycleMessageProcessorAdapter(MessageProcessor):
    def __init__(self, *, registry: ConnectionLifecycleProcessorRegistry, contract: MessageTypeContract) -> None:
        from ns_runtime.connection.processors import ConnectionLifecycleProcessorRegistry

        if not isinstance(registry, ConnectionLifecycleProcessorRegistry):
            _invalid("lifecycle.registry")
        if not isinstance(contract, MessageTypeContract):
            _invalid("lifecycle.contract")
        self._registry = registry
        self._contract = contract

    @property
    def name(self) -> str:
        return self._contract.processor_key

    async def process(self, context: ProcessorContext, value: object) -> object:
        if (
            not isinstance(value, RoutingPreparationResult)
            or value.outcome is not RoutingPreparationOutcome.NO_ROUTING_REQUIRED
        ):
            _invalid("lifecycle.routing_result")
        return await self._registry.dispatch(context.envelope)


class FeatureDisabledMessageProcessorAdapter(MessageProcessor):
    def __init__(
        self,
        *,
        processor: FeatureDisabledProcessor,
        error_context_factory: Callable[[], ErrorEnvelopeContext],
    ) -> None:
        if not isinstance(processor, FeatureDisabledProcessor):
            _invalid("feature_disabled.processor")
        if not callable(error_context_factory):
            _invalid("feature_disabled.error_context_factory")
        self._processor = processor
        self._error_context_factory = error_context_factory

    @property
    def name(self) -> str:
        return self._processor.contract.processor_key

    async def process(self, context: ProcessorContext, value: object) -> object:
        return await self._processor.process(
            context.envelope,
            error_context=self._error_context_factory(),
        )


class ConnectionProcessorPipeline:
    """Per-session registry; shared infrastructure remains explicitly injected."""

    def __init__(
        self,
        *,
        session_context: SessionContext,
        dependencies: ProcessorDependencies,
        clock: Clock,
        config_version: str,
        policy_version: str,
        registry: ProcessorRegistry,
        feature_flags: Mapping[str, bool],
        execution_policy: ProcessorExecutionPolicy,
    ) -> None:
        from ns_runtime.connection.session import SessionContext

        if not isinstance(session_context, SessionContext):
            _invalid("pipeline.session_context")
        if not isinstance(dependencies, ProcessorDependencies):
            _invalid("pipeline.dependencies")
        if not isinstance(clock, Clock):
            _invalid("pipeline.clock")
        self._session = session_context
        self._dependencies = dependencies
        self._clock = clock
        self._config_version = config_version
        self._policy_version = policy_version
        self._feature_flags = feature_flags
        self._pipeline = ProcessorPipeline(registry=registry, policy=execution_policy)

    async def execute(self, envelope: Envelope, *, execution_id: str) -> ProcessorExecutionResult:
        from .contracts import ProcessorTraceReference

        if not isinstance(envelope, Envelope):
            _invalid("pipeline.envelope")
        context = ProcessorContext(
            normalized_envelope=envelope,
            session=self._session,
            trace=ProcessorTraceReference.from_envelope(envelope),
            config_version=self._config_version,
            policy_version=self._policy_version,
            clock=self._clock,
            dependencies=self._dependencies,
        )
        return await self._pipeline.execute(
            context,
            feature_flags=self._feature_flags,
            audit_consistency=audit_consistency_for(envelope.message.type),
            execution_id=execution_id,
        )


def build_connection_processor_pipeline(
    *,
    session_context: SessionContext,
    lifecycle_registry: ConnectionLifecycleProcessorRegistry,
    disabled_processors: Mapping[str, FeatureDisabledProcessor],
    error_context_factory: Callable[[], ErrorEnvelopeContext],
    authorization: ProcessorAuthorization,
    rate_limit: RateLimitEntry,
    idempotency: IdempotencyPrecheck,
    routing: RoutingPreparation,
    error_mapper: ProcessorErrorMapper,
    principal_type: IamPrincipalType,
    audit_sink: AuditSink,
    event_bus: EventBus,
    task_supervisor: TaskSupervisor,
    clock: Clock,
    config_version: str,
    policy_version: str,
    timeout_seconds: float,
    protocol_registry: MessageTypeRegistry = BUILTIN_MESSAGE_REGISTRY,
) -> ConnectionProcessorPipeline:
    from ns_runtime.connection.session import SessionContext
    from ns_runtime.connection.processors import ConnectionLifecycleProcessorRegistry

    if not isinstance(session_context, SessionContext):
        _invalid("build.session_context")
    if not isinstance(lifecycle_registry, ConnectionLifecycleProcessorRegistry):
        _invalid("build.lifecycle_registry")
    if not isinstance(protocol_registry, MessageTypeRegistry):
        _invalid("build.protocol_registry")
    if not isinstance(task_supervisor, TaskSupervisor):
        _invalid("build.task_supervisor")
    if not isinstance(clock, Clock):
        _invalid("build.clock")
    if not isinstance(principal_type, IamPrincipalType):
        _invalid("build.principal_type")
    registry = ProcessorRegistry()
    version = session_context.protocol_version
    feature_flags: dict[str, bool] = {}
    for contract in protocol_registry.contracts:
        if contract.direction is MessageDirection.OUTBOUND or contract.message_type == "connection.hello":
            continue
        previous = feature_flags.setdefault(contract.feature_flag, contract.feature_enabled)
        if previous is not contract.feature_enabled:
            _invalid("build.feature_flag_contract_conflict")
        if contract.feature_enabled:
            message_processor = LifecycleMessageProcessorAdapter(
                registry=lifecycle_registry,
                contract=contract,
            )
        else:
            disabled = disabled_processors.get(contract.processor_key)
            if disabled is None:
                _invalid("build.disabled_processor")
            message_processor = FeatureDisabledMessageProcessorAdapter(
                processor=disabled,
                error_context_factory=error_context_factory,
            )
        standard = build_standard_stage_processors(
            message_processor=message_processor,
        )
        for stage in PROCESSOR_STAGE_ORDER:
            registry.register(_registration(
                contract,
                stage,
                standard[stage],
                version,
            ))
    registry.freeze()
    dependencies = ProcessorDependencies(
        authorization=authorization,
        rate_limit=rate_limit,
        idempotency=idempotency,
        routing=routing,
        response_finalizer=CanonicalResponseFinalizer(),
        error_mapper=error_mapper,
        principal_type=principal_type,
        audit_sink=audit_sink,
        event_bus=event_bus,
        task_supervisor=task_supervisor,
    )
    return ConnectionProcessorPipeline(
        session_context=session_context,
        dependencies=dependencies,
        clock=clock,
        config_version=config_version,
        policy_version=policy_version,
        registry=registry,
        feature_flags=feature_flags,
        execution_policy=ProcessorExecutionPolicy(timeout_seconds=timeout_seconds),
    )


def audit_consistency_for(message_type: str) -> AuditConsistency:
    if not isinstance(message_type, str) or not message_type:
        _invalid("audit.message_type")
    if message_type == "runtime.control.health" or message_type == "status.query":
        return AuditConsistency.ORDINARY
    if message_type.startswith((
        "runtime.control.",
        "cluster.event.",
        "config.",
        "dead_letter.",
        "replay.",
        "cancel.",
        "hold.",
    )):
        return AuditConsistency.STRONG_REQUIRED
    return AuditConsistency.ORDINARY


def _registration(
    contract: MessageTypeContract,
    stage: ProcessorStage,
    processor: PipelineProcessor,
    version: ProtocolVersion,
) -> ProcessorRegistration:
    return ProcessorRegistration(
        message_type=contract.message_type,
        stage=stage,
        minimum_version=version,
        maximum_version=version,
        feature_flag=contract.feature_flag,
        feature_enabled=contract.feature_enabled,
        processor=processor,
    )


def _target_context(context: ProcessorContext) -> IamTargetContext:
    target = context.envelope.target
    if target is None:
        return IamTargetContext(
            kind="session",
            tenant_id=context.session.tenant_id,
            reference=AuthorizationDecisionEvidence.target_reference(
                None,
                session_tenant_id=context.session.tenant_id,
            ),
        )
    return IamTargetContext(
        kind=target.kind,
        tenant_id=target.tenant_id or context.session.tenant_id,
        reference=AuthorizationDecisionEvidence.target_reference(
            target,
            session_tenant_id=context.session.tenant_id,
        ),
    )


def _authorization_evidence(
    *,
    context: ProcessorContext,
    request: IamAccessCheckRequest,
    effective_snapshot: object,
    decision: object,
) -> AuthorizationDecisionEvidence:
    from ns_common.iam import IamAccessDecision
    from ns_runtime.iam import PermissionSnapshot

    if not isinstance(effective_snapshot, PermissionSnapshot):
        _invalid("authorization.effective_snapshot")
    if not isinstance(decision, IamAccessDecision) or not decision.allowed:
        _invalid("authorization.decision")
    message_reference = ProcessorSafeSummary.from_envelope(
        context.envelope,
    ).object_reference
    target_reference = AuthorizationDecisionEvidence.target_reference(
        context.envelope.target,
        session_tenant_id=context.session.tenant_id,
    )
    if request.target.reference != target_reference:
        _invalid("authorization.target_reference")
    effective_tenant_id = (
        request.target.tenant_id
        if request.cross_tenant
        else effective_snapshot.tenant_id
    )
    effective_request = request.to_wire()
    effective_request["permission_snapshot_ref"] = (
        effective_snapshot.permission_snapshot_ref
    )
    effective_request["permission_version"] = effective_snapshot.permission_version
    return AuthorizationDecisionEvidence.bound(
        decision_version="authorization-decision.v1",
        decision_classification="allow",
        decision_reason=decision.reason,
        semantic_access_check_reference=_decision_digest(effective_request),
        message_reference=message_reference,
        message_type=context.envelope.message.type,
        principal_tenant_id=context.session.tenant_id,
        effective_tenant_id=effective_tenant_id,
        cross_tenant_authorized=(decision.allowed and request.cross_tenant),
        authorized_target_reference=target_reference,
        session_permission_snapshot_ref=context.session.permission_snapshot_ref,
        session_permission_snapshot_version=context.session.permission_version,
        effective_permission_snapshot_ref=effective_snapshot.permission_snapshot_ref,
        effective_permission_snapshot_version=effective_snapshot.permission_version,
    )


def _decision_digest(payload: object) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _risk_context(contract: MessageTypeContract, *, crosses_tenant: bool) -> OperationRiskContext:
    from ns_runtime.iam import OperationRiskContext

    high_risk = audit_consistency_for(contract.message_type) is AuditConsistency.STRONG_REQUIRED
    return OperationRiskContext(
        high_risk_control=high_risk,
        cross_tenant=crosses_tenant,
        new_configuration=contract.message_type.startswith("config."),
        global_coordination_write=contract.message_type.startswith("cluster."),
    )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Connection processor integration value is invalid.",
        details={"component": "connection_processor_pipeline", "field": field_name},
    )


__all__ = (
    "ConnectionProcessorPipeline",
    "DeterministicTestProcessorAuthorization",
    "FeatureDisabledMessageProcessorAdapter",
    "IamProcessorAuthorization",
    "LifecycleMessageProcessorAdapter",
    "CanonicalResponseFinalizer",
    "TransportResponseEmitter",
    "audit_consistency_for",
    "build_connection_processor_pipeline",
)
