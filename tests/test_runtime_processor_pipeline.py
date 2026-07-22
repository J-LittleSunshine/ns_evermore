# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import dataclasses
import unittest
from datetime import datetime, timedelta, timezone

from ns_common.async_runtime import TaskSupervisor
from ns_common.exceptions import (
    NsRuntimeIamDeniedError,
    NsRuntimeProcessorFailedError,
    NsRuntimeProcessorTimeoutError,
    NsRuntimeProtocolViolationError,
    NsRuntimeRouteRejectedError,
    NsRuntimeRouteUnavailableError,
    NsValidationError,
)
from ns_common.iam import IamPrincipalType
from ns_common.identifiers import IdentifierFactory, NsIdentifierKind
from ns_common.time import ControlledClock
from ns_runtime.connection import LogicalConnectionState, SessionContext
from ns_runtime.processor import (
    AuthorizationDecisionEvidence,
    AuditAction,
    AuditConsistency,
    DefaultProcessorErrorMapper,
    DeterministicTestAuditSink,
    EventBus,
    InterfaceOnlyIdempotencyPrecheck,
    InterfaceOnlyRateLimitEntry,
    InterfaceOnlyRoutingPreparation,
    MessageProcessor,
    MessageProcessorStageProcessor,
    PROCESSOR_STAGE_ORDER,
    PassthroughResponseFinalizer,
    PipelineProcessor,
    ProcessorContext,
    ProcessorDependencies,
    ProcessorExecutionPolicy,
    ProcessorPipeline,
    ProcessorAuditRecord,
    ProcessorRegistration,
    ProcessorRegistry,
    ProcessorStage,
    ProcessorTraceReference,
    RoutingPreparation,
    RoutingPreparationResult,
    build_standard_stage_processors,
)
from ns_runtime.processor.integration import DeterministicTestProcessorAuthorization
from ns_runtime.processor.integration import TransportResponseEmitter
from ns_runtime.protocol import (
    AuthContextGroup,
    Envelope,
    MessageGroup,
    ProtocolGroup,
    ProtocolVersion,
    SourceGroup,
)
from tests.test_runtime_connection_accepted import _CaptureTransport
from ns_runtime.routing import (
    LaterActionSuggestion,
    ResolutionHint,
    RoutingFailureReason,
    RoutingFailureOutcome,
    RoutingFailureReport,
)


NOW = datetime(2026, 7, 22, tzinfo=timezone.utc)


class _StageProcessor(PipelineProcessor):
    def __init__(self, stage: ProcessorStage, calls: list[ProcessorStage], action=None) -> None:
        self.stage = stage
        self.calls = calls
        self.action = action

    @property
    def name(self) -> str:
        return f"test.{self.stage.value}"

    async def process(self, context: ProcessorContext, value: object) -> object:
        self.calls.append(self.stage)
        if self.action is not None:
            return await self.action(context, value)
        if self.stage is ProcessorStage.MESSAGE_PROCESSOR:
            return "processed"
        return value


class _MessageProcessorBinding(MessageProcessor):
    def __init__(self, calls: list[ProcessorStage], action=None) -> None:
        self.calls = calls
        self.action = action

    @property
    def name(self) -> str:
        return "test.message_processor"

    async def process(self, context: ProcessorContext, value: object) -> object:
        self.calls.append(ProcessorStage.MESSAGE_PROCESSOR)
        if self.action is not None:
            return await self.action(context, value)
        return "processed"


class _RoutingResultPreparation(RoutingPreparation):
    def __init__(self, result: RoutingPreparationResult, calls: list[str]) -> None:
        self.result = result
        self.calls = calls

    async def prepare(self, context, value):
        self.calls.append("routing")
        return self.result


class ProcessorPipelineTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.supervisor = TaskSupervisor(shutdown_timeout_seconds=1)
        self.clock = ControlledClock(utc_start=NOW)
        self.sink = DeterministicTestAuditSink()
        self.execution_id = 0

    async def asyncTearDown(self) -> None:
        await self.supervisor.shutdown(timeout_seconds=1)

    async def test_fixed_order_and_exactly_one_final_audit(self) -> None:
        calls: list[ProcessorStage] = []
        pipeline, context = self._pipeline(calls=calls)
        result = await self._execute(pipeline, context)
        self.assertTrue(result.succeeded)
        self.assertEqual("processed", result.response)
        self.assertEqual(list(PROCESSOR_STAGE_ORDER), calls)
        self.assertEqual(PROCESSOR_STAGE_ORDER, result.completed_stages)
        self.assertEqual(1, self.sink.attempted_count)
        self.assertEqual(1, len(self.sink.records))
        record = self.sink.records[0]
        self.assertIs(AuditAction.SUCCEEDED, record.action)
        self.assertEqual("config-v7", record.config_version)
        self.assertEqual("policy-v7", record.policy_version)

    async def test_authorization_evidence_is_preserved_through_stages_three_to_five(self) -> None:
        calls: list[ProcessorStage] = []
        _, context = self._pipeline(calls=calls)
        standard = build_standard_stage_processors(
            message_processor=_MessageProcessorBinding(calls),
        )
        value = await standard[ProcessorStage.AUTHORIZATION].process(context, None)
        self.assertIsInstance(value, AuthorizationDecisionEvidence)
        for stage in (
            ProcessorStage.RATE_LIMIT_ENTRY,
            ProcessorStage.IDEMPOTENCY_PRECHECK,
            ProcessorStage.AUDIT_MARKER,
        ):
            retained = await standard[stage].process(context, value)
            self.assertIs(value, retained)

    def test_standard_stage_contract_contains_exact_fixed_order(self) -> None:
        binding = _MessageProcessorBinding([])
        standard = build_standard_stage_processors(
            message_processor=binding,
        )

        self.assertEqual(PROCESSOR_STAGE_ORDER, tuple(standard))
        self.assertIsInstance(
            standard[ProcessorStage.MESSAGE_PROCESSOR],
            MessageProcessorStageProcessor,
        )
        self.assertEqual(
            binding.name,
            standard[ProcessorStage.MESSAGE_PROCESSOR].name,
        )

    async def test_reject_stops_later_stages_and_maps_stable_error(self) -> None:
        calls: list[ProcessorStage] = []

        async def reject(context, value):
            raise NsRuntimeIamDeniedError(details={"reason": "test"})

        pipeline, context = self._pipeline(
            calls=calls,
            actions={ProcessorStage.AUTHORIZATION: reject},
        )
        result = await self._execute(pipeline, context)
        self.assertIsInstance(result.error, NsRuntimeIamDeniedError)
        self.assertEqual([
            ProcessorStage.SECURITY_VALIDATION,
            ProcessorStage.AUTHORIZATION,
        ], calls)
        self.assertEqual(1, self.sink.attempted_count)
        self.assertIs(AuditAction.REJECTED, self.sink.records[0].action)

    async def test_security_reject_stops_before_authorization(self) -> None:
        calls: list[ProcessorStage] = []

        async def reject(context, value):
            raise NsRuntimeProtocolViolationError(
                details={"reason": "test_security_reject"},
            )

        pipeline, context = self._pipeline(
            calls=calls,
            actions={ProcessorStage.SECURITY_VALIDATION: reject},
        )

        result = await self._execute(pipeline, context)

        self.assertIsInstance(result.error, NsRuntimeProtocolViolationError)
        self.assertEqual([ProcessorStage.SECURITY_VALIDATION], calls)
        self.assertEqual((), result.completed_stages)
        self.assertEqual(1, self.sink.attempted_count)
        self.assertIs(AuditAction.REJECTED, self.sink.records[0].action)

    async def test_timeout_cancels_supervised_processor_and_audits_once(self) -> None:
        calls: list[ProcessorStage] = []
        blocked = asyncio.Event()

        async def wait_forever(context, value):
            await blocked.wait()

        pipeline, context = self._pipeline(
            calls=calls,
            actions={ProcessorStage.MESSAGE_PROCESSOR: wait_forever},
            timeout_seconds=0.01,
        )
        result = await self._execute(pipeline, context)
        self.assertIsInstance(result.error, NsRuntimeProcessorTimeoutError)
        self.assertNotIn(ProcessorStage.RESPONSE_FINALIZE, calls)
        self.assertEqual(1, self.sink.attempted_count)
        self.assertIs(AuditAction.TIMED_OUT, self.sink.records[0].action)

    async def test_caller_cancellation_propagates_after_final_audit(self) -> None:
        calls: list[ProcessorStage] = []
        entered = asyncio.Event()
        blocked = asyncio.Event()

        async def wait_forever(context, value):
            entered.set()
            await blocked.wait()

        pipeline, context = self._pipeline(
            calls=calls,
            actions={ProcessorStage.MESSAGE_PROCESSOR: wait_forever},
        )
        self.execution_id += 1
        caller = asyncio.create_task(pipeline.execute(
            context,
            feature_flags={"message_family.connection": True},
            audit_consistency=AuditConsistency.ORDINARY,
            execution_id=str(self.execution_id),
        ))
        await entered.wait()
        caller.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await caller
        self.assertEqual(1, self.sink.attempted_count)
        self.assertIs(AuditAction.CANCELLED, self.sink.records[0].action)

    async def test_hostile_exception_is_isolated_and_never_leaks(self) -> None:
        calls: list[ProcessorStage] = []
        secret = "token=processor-secret"

        async def fail(context, value):
            raise RuntimeError(secret)

        pipeline, context = self._pipeline(
            calls=calls,
            actions={ProcessorStage.MESSAGE_PROCESSOR: fail},
        )
        result = await self._execute(pipeline, context)
        self.assertIsInstance(result.error, NsRuntimeProcessorFailedError)
        public = repr(result.error) + str(result.error) + repr(result) + repr(self.sink.records)
        self.assertNotIn(secret, public)
        self.assertEqual("RUNTIME_PROCESSOR_FAILED", self.sink.records[0].error)
        self.assertNotIn(ProcessorStage.RESPONSE_FINALIZE, calls)

    async def test_missing_message_processor_maps_stable_failure(self) -> None:
        calls: list[ProcessorStage] = []

        async def partial_routing_value(context, value):
            return "routing-partial-must-not-escape"

        pipeline, context = self._pipeline(
            calls=calls,
            actions={
                ProcessorStage.ROUTING_PREPARATION: partial_routing_value,
            },
            omit_stage=ProcessorStage.MESSAGE_PROCESSOR,
        )

        result = await self._execute(pipeline, context)

        self.assertFalse(result.succeeded)
        self.assertIsNone(result.response)
        self.assertIsInstance(result.error, NsRuntimeProcessorFailedError)
        self.assertEqual(
            tuple(PROCESSOR_STAGE_ORDER[:6]),
            result.completed_stages,
        )
        self.assertEqual(list(PROCESSOR_STAGE_ORDER[:6]), calls)
        self.assertNotIn(ProcessorStage.RESPONSE_FINALIZE, calls)
        self.assertEqual(1, self.sink.attempted_count)
        self.assertEqual(
            "message_processor.unresolved",
            self.sink.records[0].processor,
        )
        self.assertEqual(
            "RUNTIME_PROCESSOR_FAILED",
            self.sink.records[0].error,
        )

    async def test_audit_sink_failure_differs_for_ordinary_and_strong(self) -> None:
        for consistency, should_fail in (
            (AuditConsistency.ORDINARY, False),
            (AuditConsistency.STRONG_REQUIRED, True),
        ):
            with self.subTest(consistency=consistency):
                sink = DeterministicTestAuditSink()
                sink.failure = RuntimeError("credential=never-copy")
                calls: list[ProcessorStage] = []
                pipeline, context = self._pipeline(calls=calls, sink=sink)
                self.execution_id += 1
                result = await pipeline.execute(
                    context,
                    feature_flags={"message_family.connection": True},
                    audit_consistency=consistency,
                    execution_id=str(self.execution_id),
                )
                self.assertEqual(1, sink.attempted_count)
                self.assertFalse(result.audit.succeeded)
                self.assertEqual(should_fail, isinstance(
                    result.error,
                    NsRuntimeProcessorFailedError,
                ))

    async def test_strong_audit_failure_clears_response_before_emission(self) -> None:
        sink = DeterministicTestAuditSink()
        sink.failure = RuntimeError("strong-audit-unavailable")

        async def envelope_response(context, value):
            return _envelope()

        pipeline, context = self._pipeline(
            calls=[],
            actions={ProcessorStage.MESSAGE_PROCESSOR: envelope_response},
            sink=sink,
        )
        self.execution_id += 1
        result = await pipeline.execute(
            context,
            feature_flags={"message_family.connection": True},
            audit_consistency=AuditConsistency.STRONG_REQUIRED,
            execution_id=str(self.execution_id),
        )
        transport = _CaptureTransport()
        emitted = await TransportResponseEmitter(transport=transport).emit(result)

        self.assertFalse(result.succeeded)
        self.assertIsNone(result.response)
        self.assertFalse(emitted)
        self.assertEqual([], transport.sent)
        self.assertEqual(PROCESSOR_STAGE_ORDER, result.completed_stages)

    async def test_stage_six_rejected_and_unavailable_short_circuit(self) -> None:
        for outcome, reason, error_type in (
            (
                "rejected",
                RoutingFailureReason.STRATEGY_NOT_PERMITTED,
                NsRuntimeRouteRejectedError,
            ),
            (
                "unavailable",
                RoutingFailureReason.NO_CANDIDATE,
                NsRuntimeRouteUnavailableError,
            ),
        ):
            with self.subTest(outcome=outcome):
                routing_calls: list[str] = []
                failure = RoutingFailureReport(
                    outcome=(
                        RoutingFailureOutcome.REJECTED
                        if outcome == "rejected"
                        else RoutingFailureOutcome.UNAVAILABLE
                    ),
                    reason=reason,
                    original_target_safe_reference="sha256:fedcba9876543210",
                    safe_message_reference="sha256:0123456789abcdef",
                    config_version="config-v1",
                    policy_version="policy-v1",
                    index_mutation_sequence=None,
                    resolution_hint=ResolutionHint.LOCAL,
                    later_action=LaterActionSuggestion.DO_NOT_RETRY_UNCHANGED,
                    occurred_at=NOW,
                )
                contract = (
                    RoutingPreparationResult.rejected(failure)
                    if outcome == "rejected"
                    else RoutingPreparationResult.unavailable(failure)
                )
                stage_calls: list[ProcessorStage] = []
                pipeline, context = self._pipeline(
                    calls=stage_calls,
                    routing_dependency=_RoutingResultPreparation(
                        contract,
                        routing_calls,
                    ),
                    use_standard_routing=True,
                )
                execution = await self._execute(pipeline, context)
                self.assertIsInstance(execution.error, error_type)
                self.assertEqual(["routing"], routing_calls)
                self.assertNotIn(ProcessorStage.MESSAGE_PROCESSOR, stage_calls)
                self.assertNotIn(ProcessorStage.RESPONSE_FINALIZE, stage_calls)
                self.assertEqual(
                    tuple(PROCESSOR_STAGE_ORDER[:5]),
                    execution.completed_stages,
                )

    async def test_resolved_plan_is_propagated_once_to_message_processor(self) -> None:
        plan = object()
        seen: list[object] = []

        async def consume(context, value):
            self.assertIsInstance(value, RoutingPreparationResult)
            self.assertIs(plan, value.plan)
            seen.append(value.plan)
            return "processed-with-plan"

        calls: list[ProcessorStage] = []
        pipeline, context = self._pipeline(
            calls=calls,
            actions={ProcessorStage.MESSAGE_PROCESSOR: consume},
            routing_dependency=_RoutingResultPreparation(
                RoutingPreparationResult.resolved(plan),
                [],
            ),
            use_standard_routing=True,
        )
        execution = await self._execute(pipeline, context)
        self.assertTrue(execution.succeeded)
        self.assertEqual("processed-with-plan", execution.response)
        self.assertEqual([plan], seen)

    def test_context_exposes_only_explicit_dependencies_and_redacted_repr(self) -> None:
        calls: list[ProcessorStage] = []
        _, context = self._pipeline(calls=calls)
        field_names = {item.name for item in dataclasses.fields(ProcessorContext)}
        self.assertEqual({
            "normalized_envelope", "session", "trace", "config_version",
            "policy_version", "clock", "dependencies",
        }, field_names)
        public = repr(context)
        self.assertNotIn("identity:test", public)
        self.assertNotIn("permission:test", public)

    def test_dependencies_require_typed_audit_and_event_boundaries(self) -> None:
        _, context = self._pipeline(calls=[])
        self.assertEqual(
            "AuditSink",
            ProcessorDependencies.__annotations__["audit_sink"],
        )
        self.assertEqual(
            "EventBus",
            ProcessorDependencies.__annotations__["event_bus"],
        )
        self.assertIs(context.dependencies.audit_sink, self.sink)
        self.assertIsInstance(context.dependencies.event_bus, EventBus)
        with self.assertRaises(NsValidationError):
            dataclasses.replace(context.dependencies, audit_sink=object())
        with self.assertRaises(NsValidationError):
            dataclasses.replace(context.dependencies, event_bus=object())

    def test_audit_schema_excludes_sensitive_fields(self) -> None:
        field_names = {item.name for item in dataclasses.fields(ProcessorAuditRecord)}
        self.assertEqual({
            "safe_summary",
            "processor",
            "action",
            "error",
            "trace",
            "config_version",
            "policy_version",
            "required_consistency",
            "occurred_at",
        }, field_names)
        for forbidden in (
            "token",
            "credential",
            "payload",
            "iam_response",
            "raw_envelope",
        ):
            self.assertNotIn(forbidden, field_names)

    def _pipeline(
        self,
        *,
        calls: list[ProcessorStage],
        actions: dict[ProcessorStage, object] | None = None,
        timeout_seconds: float = 1,
        sink: DeterministicTestAuditSink | None = None,
        omit_stage: ProcessorStage | None = None,
        routing_dependency: RoutingPreparation | None = None,
        use_standard_routing: bool = False,
    ) -> tuple[ProcessorPipeline, ProcessorContext]:
        registry = ProcessorRegistry()
        version = ProtocolVersion(1, 0, 0)
        message_action = None if actions is None else actions.get(
            ProcessorStage.MESSAGE_PROCESSOR,
        )
        standard = build_standard_stage_processors(
            message_processor=_MessageProcessorBinding(calls, message_action),
        )
        for stage in PROCESSOR_STAGE_ORDER:
            if stage is omit_stage:
                continue
            processor = (
                standard[stage]
                if stage is ProcessorStage.MESSAGE_PROCESSOR
                or (
                    stage is ProcessorStage.ROUTING_PREPARATION
                    and use_standard_routing
                )
                else _StageProcessor(
                    stage,
                    calls,
                    None if actions is None else actions.get(stage),
                )
            )
            registry.register(ProcessorRegistration(
                message_type="connection.drain",
                stage=stage,
                minimum_version=version,
                maximum_version=version,
                feature_flag="message_family.connection",
                feature_enabled=True,
                processor=processor,
            ))
        registry.freeze()
        effective_sink = sink or self.sink
        dependencies = ProcessorDependencies(
            authorization=DeterministicTestProcessorAuthorization(),
            rate_limit=InterfaceOnlyRateLimitEntry(),
            idempotency=InterfaceOnlyIdempotencyPrecheck(),
            routing=routing_dependency or InterfaceOnlyRoutingPreparation(),
            response_finalizer=PassthroughResponseFinalizer(),
            error_mapper=DefaultProcessorErrorMapper(),
            principal_type=IamPrincipalType.CLIENT,
            audit_sink=effective_sink,
            event_bus=EventBus(
                task_supervisor=self.supervisor,
                default_timeout_seconds=0.1,
            ),
            task_supervisor=self.supervisor,
        )
        context = ProcessorContext(
            normalized_envelope=_envelope(),
            session=_session(),
            trace=ProcessorTraceReference(value="trace:test"),
            config_version="config-v7",
            policy_version="policy-v7",
            clock=self.clock,
            dependencies=dependencies,
        )
        return (
            ProcessorPipeline(
                registry=registry,
                policy=ProcessorExecutionPolicy(timeout_seconds=timeout_seconds),
            ),
            context,
        )

    async def _execute(self, pipeline: ProcessorPipeline, context: ProcessorContext):
        self.execution_id += 1
        return await pipeline.execute(
            context,
            feature_flags={"message_family.connection": True},
            audit_consistency=AuditConsistency.ORDINARY,
            execution_id=str(self.execution_id),
        )


def _session() -> SessionContext:
    identifiers = IdentifierFactory()
    return SessionContext(
        connection_id=identifiers.generate(NsIdentifierKind.CONNECTION_ID),
        session_id=identifiers.generate(NsIdentifierKind.SESSION_ID),
        connection_epoch=0,
        identity="identity:test",
        tenant_id="tenant:test",
        component_type="client",
        protocol_version=ProtocolVersion(1, 0, 0),
        protocol_schema_key="json.v1/protocol-1.0",
        wire_codec="json.v1",
        capabilities=frozenset({"runtime.connection"}),
        permission_snapshot_ref="permission:test",
        permission_digest="sha256:test",
        permission_version="version:test",
        iam_mode="test",
        authorization_issued_at=NOW,
        session_expires_at=NOW + timedelta(minutes=5),
        resume_eligible=True,
        established_state=LogicalConnectionState.AUTHENTICATED,
        created_at=NOW,
    )


def _envelope() -> Envelope:
    session = _session()
    return Envelope(
        protocol=ProtocolGroup(major=1, minor=0, patch=0),
        message=MessageGroup(
            message_id="message-test",
            type="connection.drain",
            category="connection",
            priority=0,
            created_at="2026-07-22T00:00:00Z",
        ),
        source=SourceGroup(
            runtime_id="runtime-test",
            connection_id=session.connection_id,
            identity_digest="sha256:identity",
            tenant_id=session.tenant_id,
            component_type=session.component_type,
            capabilities_digest="sha256:capabilities",
        ),
        auth_context=AuthContextGroup(
            permission_snapshot_ref=session.permission_snapshot_ref,
            permission_digest=session.permission_digest,
            iam_mode=session.iam_mode,
            issued_at="2026-07-22T00:00:00Z",
            expires_at="2026-07-22T00:05:00Z",
        ),
    )


if __name__ == "__main__":
    unittest.main()
