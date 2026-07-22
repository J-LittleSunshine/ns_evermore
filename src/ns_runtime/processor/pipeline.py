# -*- coding: utf-8 -*-
"""Fixed-order supervised processor pipeline and standard stage adapters."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from ns_common.exceptions import (
    NsRuntimeError,
    NsRuntimeProcessorFailedError,
    NsRuntimeProcessorTimeoutError,
    NsValidationError,
)

from .audit import (
    AuditAction,
    AuditConsistency,
    AuditWriteOutcome,
    ProcessorAuditBoundary,
    ProcessorAuditRecord,
)
from .contracts import (
    PROCESSOR_STAGE_ORDER,
    IdempotencyPrecheck,
    MessageProcessor,
    MessageProcessorExecutionBoundary,
    ProcessorContext,
    ProcessorErrorMapper,
    ProcessorExecutionPolicy,
    ProcessorSafeSummary,
    ProcessorStage,
    RateLimitEntry,
    ResponseFinalizer,
    RoutingPreparation,
    freeze_feature_flags,
)
from .registry import PipelineProcessor, ProcessorRegistry


@dataclass(frozen=True, slots=True, kw_only=True)
class ProcessorExecutionResult:
    response: object | None
    error: Exception | None
    audit: AuditWriteOutcome
    completed_stages: tuple[ProcessorStage, ...]

    @property
    def succeeded(self) -> bool:
        return self.error is None


@dataclass(slots=True)
class _CancellationState:
    timeout_requested: bool = False


class DefaultProcessorErrorMapper(ProcessorErrorMapper):
    def map_error(self, error: Exception) -> Exception:
        if not isinstance(error, Exception):
            _invalid("error")
        if isinstance(error, NsRuntimeError):
            return error
        return NsRuntimeProcessorFailedError()


class InterfaceOnlyRateLimitEntry(RateLimitEntry):
    async def enter(self, context: ProcessorContext) -> None:
        _context(context)


class InterfaceOnlyIdempotencyPrecheck(IdempotencyPrecheck):
    async def precheck(self, context: ProcessorContext) -> None:
        _context(context)


class InterfaceOnlyRoutingPreparation(RoutingPreparation):
    async def prepare(self, context: ProcessorContext) -> None:
        _context(context)


class PassthroughResponseFinalizer(ResponseFinalizer):
    async def finalize(self, context: ProcessorContext, response: object) -> object:
        _context(context)
        return response


class SecurityValidationProcessor(PipelineProcessor):
    @property
    def name(self) -> str:
        return "security.validation"

    async def process(self, context: ProcessorContext, value: object) -> object:
        _context(context)
        envelope = context.envelope
        session = context.session
        source = envelope.source
        auth = envelope.auth_context
        if source is None or auth is None:
            _security_reject("runtime_authority_missing")
        if (
            source.connection_id != session.connection_id
            or source.tenant_id != session.tenant_id
            or source.component_type != session.component_type
        ):
            _security_reject("runtime_source_mismatch")
        if (
            auth.permission_snapshot_ref != session.permission_snapshot_ref
            or auth.permission_digest != session.permission_digest
            or auth.iam_mode != session.iam_mode
        ):
            _security_reject("runtime_auth_context_mismatch")
        if context.protocol_version != session.protocol_version:
            _security_reject("session_protocol_mismatch")
        return value


class AuthorizationProcessor(PipelineProcessor):
    @property
    def name(self) -> str:
        return "authorization"

    async def process(self, context: ProcessorContext, value: object) -> object:
        await context.dependencies.authorization.authorize(context)
        return value


class RateLimitEntryProcessor(PipelineProcessor):
    @property
    def name(self) -> str:
        return "rate_limit.entry"

    async def process(self, context: ProcessorContext, value: object) -> object:
        await context.dependencies.rate_limit.enter(context)
        return value


class IdempotencyPrecheckProcessor(PipelineProcessor):
    @property
    def name(self) -> str:
        return "idempotency.precheck"

    async def process(self, context: ProcessorContext, value: object) -> object:
        await context.dependencies.idempotency.precheck(context)
        return value


class AuditMarkerProcessor(PipelineProcessor):
    @property
    def name(self) -> str:
        return "audit.marker"

    async def process(self, context: ProcessorContext, value: object) -> object:
        _context(context)
        return value


class RoutingPreparationProcessor(PipelineProcessor):
    @property
    def name(self) -> str:
        return "routing.preparation"

    async def process(self, context: ProcessorContext, value: object) -> object:
        await context.dependencies.routing.prepare(context)
        return value


class MessageProcessorStageProcessor(
    PipelineProcessor,
    MessageProcessorExecutionBoundary,
):
    """Fixed MESSAGE_PROCESSOR stage around one registry-selected binding."""

    def __init__(self, *, binding: MessageProcessor) -> None:
        if not isinstance(binding, MessageProcessor):
            _invalid("message_processor.binding")
        self._binding = binding

    @property
    def name(self) -> str:
        return self._binding.name

    async def process(self, context: ProcessorContext, value: object) -> object:
        _context(context)
        return await self._binding.process(context, value)


class ResponseFinalizeProcessor(PipelineProcessor):
    @property
    def name(self) -> str:
        return "response.finalize"

    async def process(self, context: ProcessorContext, value: object) -> object:
        return await context.dependencies.response_finalizer.finalize(context, value)


def build_standard_stage_processors(
    *,
    message_processor: MessageProcessor,
) -> Mapping[ProcessorStage, PipelineProcessor]:
    if not isinstance(message_processor, MessageProcessor):
        _invalid("message_processor")
    return MappingProxyType({
        ProcessorStage.SECURITY_VALIDATION: SecurityValidationProcessor(),
        ProcessorStage.AUTHORIZATION: AuthorizationProcessor(),
        ProcessorStage.RATE_LIMIT_ENTRY: RateLimitEntryProcessor(),
        ProcessorStage.IDEMPOTENCY_PRECHECK: IdempotencyPrecheckProcessor(),
        ProcessorStage.AUDIT_MARKER: AuditMarkerProcessor(),
        ProcessorStage.ROUTING_PREPARATION: RoutingPreparationProcessor(),
        ProcessorStage.MESSAGE_PROCESSOR: MessageProcessorStageProcessor(
            binding=message_processor,
        ),
        ProcessorStage.RESPONSE_FINALIZE: ResponseFinalizeProcessor(),
    })


class ProcessorPipeline:
    def __init__(self, *, registry: ProcessorRegistry, policy: ProcessorExecutionPolicy) -> None:
        if not isinstance(registry, ProcessorRegistry):
            _invalid("registry")
        if not registry.frozen:
            _invalid("registry.frozen")
        if not isinstance(policy, ProcessorExecutionPolicy):
            _invalid("policy")
        self._registry = registry
        self._policy = policy

    async def execute(
        self,
        context: ProcessorContext,
        *,
        feature_flags: Mapping[str, bool],
        audit_consistency: AuditConsistency,
        execution_id: str,
    ) -> ProcessorExecutionResult:
        _context(context)
        flags = freeze_feature_flags(feature_flags)
        if not isinstance(audit_consistency, AuditConsistency):
            _invalid("audit_consistency")
        if not isinstance(execution_id, str) or re.fullmatch(r"[0-9]+", execution_id) is None:
            _invalid("execution_id")
        state = _CancellationState()
        task = context.dependencies.task_supervisor.create_task(
            self._run(
                context,
                feature_flags=flags,
                audit_consistency=audit_consistency,
                cancellation=state,
            ),
            name=f"processor-execution-{execution_id}",
            cancel_order=24,
        )
        try:
            done, _ = await asyncio.wait({task}, timeout=self._policy.timeout_seconds)
            if done:
                return task.result()
            state.timeout_requested = True
            task.cancel()
            return await task
        except asyncio.CancelledError:
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
            raise

    async def _run(
        self,
        context: ProcessorContext,
        *,
        feature_flags: Mapping[str, bool],
        audit_consistency: AuditConsistency,
        cancellation: _CancellationState,
    ) -> ProcessorExecutionResult:
        response: object | None = None
        error: Exception | None = None
        completed: list[ProcessorStage] = []
        processor_name = "pipeline.unresolved"
        action = AuditAction.SUCCEEDED
        cancelled = False
        try:
            for stage in PROCESSOR_STAGE_ORDER:
                processor_name = f"{stage.value}.unresolved"
                processor = self._registry.resolve(
                    message_type=context.envelope.message.type,
                    stage=stage,
                    protocol_version=context.protocol_version,
                    feature_flags=feature_flags,
                )
                processor_name = processor.name
                response = await processor.process(context, response)
                completed.append(stage)
        except asyncio.CancelledError:
            response = None
            if cancellation.timeout_requested:
                error = NsRuntimeProcessorTimeoutError()
                action = AuditAction.TIMED_OUT
            else:
                cancelled = True
                action = AuditAction.CANCELLED
        except Exception as caught:
            response = None
            error = context.dependencies.error_mapper.map_error(caught)
            action = (
                AuditAction.REJECTED
                if isinstance(error, NsRuntimeError)
                and not isinstance(error, NsRuntimeProcessorFailedError)
                else AuditAction.FAILED
            )
        error_code = getattr(type(error), "code", None) if error is not None else None
        record = ProcessorAuditRecord(
            safe_summary=ProcessorSafeSummary.from_envelope(context.envelope),
            processor=processor_name,
            action=action,
            error=error_code,
            trace=context.trace,
            config_version=context.config_version,
            policy_version=context.policy_version,
            required_consistency=audit_consistency,
            occurred_at=context.clock.utc_now(),
        )
        audit = await ProcessorAuditBoundary(
            sink=context.dependencies.audit_sink,
        ).write_final(record)
        if (
            not audit.succeeded
            and audit.required_consistency is AuditConsistency.STRONG_REQUIRED
            and error is None
            and not cancelled
        ):
            error = NsRuntimeProcessorFailedError()
            response = None
        if cancelled:
            raise asyncio.CancelledError
        return ProcessorExecutionResult(
            response=response,
            error=error,
            audit=audit,
            completed_stages=tuple(completed),
        )


def _context(value: object) -> None:
    if not isinstance(value, ProcessorContext):
        _invalid("context")


def _security_reject(reason: str) -> None:
    from ns_common.exceptions import NsRuntimeProtocolViolationError

    raise NsRuntimeProtocolViolationError(
        details={
            "component": "processor_security",
            "operation": "validate",
            "reason": reason,
        },
    )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Processor pipeline value is invalid.",
        details={"component": "processor_pipeline", "field": field_name},
    )


__all__ = (
    "AuditMarkerProcessor",
    "AuthorizationProcessor",
    "DefaultProcessorErrorMapper",
    "IdempotencyPrecheckProcessor",
    "InterfaceOnlyIdempotencyPrecheck",
    "InterfaceOnlyRateLimitEntry",
    "InterfaceOnlyRoutingPreparation",
    "MessageProcessorStageProcessor",
    "PassthroughResponseFinalizer",
    "ProcessorExecutionResult",
    "ProcessorPipeline",
    "RateLimitEntryProcessor",
    "ResponseFinalizeProcessor",
    "RoutingPreparationProcessor",
    "build_standard_stage_processors",
    "SecurityValidationProcessor",
)
