# -*- coding: utf-8 -*-
from __future__ import annotations

from abc import (
    ABC,
    abstractmethod
)
from typing import (
    Any,
    Callable,
    Iterable,
    Mapping,
    TYPE_CHECKING
)

from ns_common.exceptions import (
    NsEvermoreError,
    NsRuntimeDeliveryStateError,
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeTargetUnavailableError,
    NsRuntimeTenantMismatchError,
    NsRuntimeUnauthorizedMessageTypeError,
    NsRuntimeUnsupportedMessageTypeError
)
from ns_runtime.delivery import (
    RuntimeDeliveryRegistry,
    RuntimeMessageDeliverySummary,
)
from ns_runtime.models import (
    Envelope,
    MessageTypeSpec,
    ProcessorRequest,
    ProcessorResponse,
    RuntimeSessionContext,
    utc_now_iso,
)
from ns_runtime.outbound import RuntimeLocalEnvelopeForwarder
from ns_runtime.protocol import EnvelopeCodec
from ns_runtime.routing import RuntimeTargetResolver

if TYPE_CHECKING:
    pass


class BaseRuntimeProcessor(ABC):
    @abstractmethod
    async def process(self, request: ProcessorRequest) -> ProcessorResponse:
        raise NotImplementedError


class MessageTypeAuthProcessor(BaseRuntimeProcessor):
    def __init__(self, *, registry: "ProcessorRegistry", codec: EnvelopeCodec) -> None:
        self._registry = registry
        self._codec = codec

    async def process(self, request: ProcessorRequest) -> ProcessorResponse:
        spec = self._registry.get_spec(request.envelope.message_type)

        if spec is None:
            error = NsRuntimeUnsupportedMessageTypeError(details={"message_type": request.envelope.message_type})
            return ProcessorResponse.reject(self._codec.build_error_envelope(error, session=request.session, request=request.envelope))

        missing_capabilities = sorted(set(spec.required_capabilities) - set(request.session.capabilities))
        if missing_capabilities:
            error = NsRuntimeUnauthorizedMessageTypeError(
                details={
                    "message_type": request.envelope.message_type,
                    "missing_capabilities": missing_capabilities,
                }
            )
            return ProcessorResponse.reject(self._codec.build_error_envelope(error, session=request.session, request=request.envelope))

        schema_error = self._validate_message_type_schema(request.envelope, spec)
        if schema_error is not None:
            return ProcessorResponse.reject(self._codec.build_error_envelope(schema_error, session=request.session, request=request.envelope))

        return ProcessorResponse.continue_next()

    @staticmethod
    def _validate_message_type_schema(envelope: Envelope, spec: MessageTypeSpec) -> NsRuntimeEnvelopeSchemaError | None:
        raw_groups = set(envelope.raw.keys())
        missing_groups = sorted(set(spec.required_groups) - raw_groups)

        if missing_groups:
            return NsRuntimeEnvelopeSchemaError(
                "Envelope misses required groups for message.type.",
                details={
                    "message_type": spec.message_type,
                    "missing_groups": missing_groups,
                },
            )

        if envelope.category != spec.category:
            return NsRuntimeEnvelopeSchemaError(
                "Envelope message.category does not match registered message.type category.",
                details={
                    "message_type": spec.message_type,
                    "actual_category": envelope.category,
                    "expected_category": spec.category,
                },
            )

        return None


class TargetLookupProcessor(BaseRuntimeProcessor):
    def __init__(self,*,codec: EnvelopeCodec,target_resolver: RuntimeTargetResolver) -> None:
        self._codec = codec
        self._target_resolver = target_resolver

    async def process(self,request: ProcessorRequest) -> ProcessorResponse:
        if request.envelope.message_type == "task.dispatch":
            return ProcessorResponse.continue_next()

        if "target" not in request.envelope.raw:
            return ProcessorResponse.continue_next()

        try:
            self._target_resolver.resolve(
                request.envelope,
                request.session,
            )
            return ProcessorResponse.continue_next()
        except NsEvermoreError as exc:
            return ProcessorResponse.reject(
                self._codec.build_error_envelope(
                    exc,
                    session=request.session,
                    request=request.envelope,
                )
            )

class AuditMarkProcessor(BaseRuntimeProcessor):
    async def process(self, request: ProcessorRequest) -> ProcessorResponse:
        return ProcessorResponse(
            action="continue",
            audit_event={
                "audit_action": "runtime.processor.accepted",
                "message_id": request.envelope.message_id,
                "message_type": request.envelope.message_type,
                "tenant_id": request.session.tenant_id,
                "received_at": request.received_at,
                "config_version": request.config_version,
                "policy_version": request.policy_version,
            },
        )


class LocalTaskDispatchProcessor(BaseRuntimeProcessor):
    def __init__(self, *, codec: EnvelopeCodec, target_resolver: RuntimeTargetResolver, local_forwarder: RuntimeLocalEnvelopeForwarder, delivery_registry: RuntimeDeliveryRegistry) -> None:
        self._codec = codec
        self._target_resolver = target_resolver
        self._local_forwarder = local_forwarder
        self._delivery_registry = delivery_registry

    async def process(self,request: ProcessorRequest ) -> ProcessorResponse:
        decision = None

        try:
            decision = self._target_resolver.resolve(
                request.envelope,
                request.session,
            )
            if decision is None:
                raise NsRuntimeEnvelopeSchemaError(
                    "task.dispatch must contain target group.",
                    details={
                        "message_id": request.envelope.message_id,
                    },
                )

            await self._local_forwarder.forward(
                decision=decision,
                envelope=request.envelope,
            )

            summary = self._delivery_registry.get_message_summary(
                request.envelope.message_id
            )
            if summary is None:
                raise NsRuntimeDeliveryStateError(
                    "Accepted task dispatch is missing MessageDeliverySummary.",
                    details={
                        "message_id": request.envelope.message_id,
                        "message_type": request.envelope.message_type,
                    },
                )

            return ProcessorResponse.respond(
                self._build_delivery_accepted(
                    request=request,
                    summary=summary,
                )
            )

        except (
                NsRuntimeTargetUnavailableError,
                NsRuntimeTenantMismatchError,
        ) as exc:
            summary = self._delivery_registry.register_rejected_summary(
                envelope=request.envelope,
                source_connection_id=request.session.connection_id,
                source_tenant_id=request.session.tenant_id,
                target_count=(
                    decision.target_count
                    if decision is not None
                    else 1
                ),
                rejected_count=1,
                reason_code=exc.code,
                reason_message=exc.message,
            )

            return ProcessorResponse.reject(
                self._build_delivery_rejected(
                    request=request,
                    summary=summary,
                    exc=exc,
                )
            )

        except NsEvermoreError as exc:
            return ProcessorResponse.reject(
                self._codec.build_error_envelope(
                    exc,
                    session=request.session,
                    request=request.envelope,
                )
            )

    def _build_delivery_accepted(self, *, request: ProcessorRequest, summary: RuntimeMessageDeliverySummary) -> dict[str, Any]:
        accepted_at = utc_now_iso()

        return {
            "protocol": {
                "version": self._codec.protocol_version_text,
            },
            "message": {
                "message_id": f"{request.envelope.message_id}.accepted",
                "type": "delivery.accepted",
                "category": "delivery",
                "priority": 100,
                "created_at": accepted_at,
                "reliability": "best_effort",
            },
            "source": {
                "runtime_id": request.session.runtime_id,
                "connection_id": "runtime",
                "session_id": "runtime",
                "identity": request.session.runtime_id,
                "tenant_id": request.session.tenant_id,
                "component_type": "runtime",
                "capabilities_summary": [
                    "delivery.accepted",
                ],
                "connection_epoch": 0,
            },
            "target": {
                "kind": "connection",
                "connection_id": request.session.connection_id,
            },
            "payload": {
                "mode": "inline",
                "inline": {
                    "message_id": request.envelope.message_id,
                    "summary_id": summary.summary_id,
                    "accepted_at": accepted_at,
                    "status_query_hint": "delivery.status_query",
                },
            },
            "trace": {
                "trace_id": request.envelope.raw.get(
                    "trace",
                    {},
                ).get(
                    "trace_id",
                    request.envelope.message_id,
                ),
                "request_id": request.envelope.message_id,
            },
        }

    def _build_delivery_rejected(self,*,request: ProcessorRequest,summary: RuntimeMessageDeliverySummary, exc: NsEvermoreError) -> dict[str, Any]:
        rejected_at = summary.last_rejected_at or utc_now_iso()
        retryable = isinstance(
            exc,
            NsRuntimeTargetUnavailableError,
        )

        return {
            "protocol": {
                "version": self._codec.protocol_version_text,
            },
            "message": {
                "message_id": f"{request.envelope.message_id}.rejected",
                "type": "delivery.rejected",
                "category": "delivery",
                "priority": 100,
                "created_at": rejected_at,
                "reliability": "best_effort",
            },
            "source": {
                "runtime_id": request.session.runtime_id,
                "connection_id": "runtime",
                "session_id": "runtime",
                "identity": request.session.runtime_id,
                "tenant_id": request.session.tenant_id,
                "component_type": "runtime",
                "capabilities_summary": [
                    "delivery.rejected",
                ],
                "connection_epoch": 0,
            },
            "target": {
                "kind": "connection",
                "connection_id": request.session.connection_id,
            },
            "payload": {
                "mode": "inline",
                "inline": {
                    "message_id": request.envelope.message_id,
                    "summary_id": summary.summary_id,
                    "rejected_at": rejected_at,
                    "reason_code": exc.code,
                    "reason_message": exc.message,
                    "retryable": retryable,
                    "status_query_hint": "delivery.status_query",
                },
            },
            "trace": {
                "trace_id": request.envelope.raw.get(
                    "trace",
                    {},
                ).get(
                    "trace_id",
                    request.envelope.message_id,
                ),
                "request_id": request.envelope.message_id,
            },
        }


class DeliveryAckProcessor(BaseRuntimeProcessor):
    def __init__(self, *, codec: EnvelopeCodec, delivery_registry: RuntimeDeliveryRegistry) -> None:
        self._codec = codec
        self._delivery_registry = delivery_registry

    async def process(self, request: ProcessorRequest) -> ProcessorResponse:
        try:
            ack_result = self._delivery_registry.mark_acked(
                envelope=request.envelope,
                session_connection_id=request.session.connection_id,
                session_connection_epoch=request.session.connection_epoch,
                session_tenant_id=request.session.tenant_id,
            )

            return ProcessorResponse.respond(
                self._build_ack_result(
                    request=request,
                    ack_result=ack_result,
                )
            )
        except NsEvermoreError as exc:
            return ProcessorResponse.reject(
                self._codec.build_error_envelope(
                    exc,
                    session=request.session,
                    request=request.envelope,
                )
            )

    def _build_ack_result(self, *, request: ProcessorRequest, ack_result) -> dict[str, Any]:
        return {
            "protocol": {
                "version": self._codec.protocol_version_text,
            },
            "message": {
                "message_id": f"{request.envelope.message_id}.result",
                "type": "delivery.ack_result",
                "category": "delivery",
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "best_effort",
            },
            "source": {
                "runtime_id": request.session.runtime_id,
                "connection_id": "runtime",
                "session_id": "runtime",
                "identity": request.session.runtime_id,
                "tenant_id": request.session.tenant_id,
                "component_type": "runtime",
                "capabilities_summary": [
                    "delivery.ack_result",
                ],
                "connection_epoch": 0,
            },
            "target": {
                "kind": "connection",
                "connection_id": request.session.connection_id,
            },
            "delivery": {
                "delivery_id": ack_result.delivery_record.delivery_id,
                "summary_id": ack_result.delivery_record.summary_id,
                "root_delivery_id": ack_result.delivery_record.root_delivery_id,
                "attempt": ack_result.delivery_record.attempt_count,
                "ack_timeout_ms": ack_result.delivery_record.ack_timeout_ms,
                "replay_epoch": 0,
            },
            "payload": {
                "mode": "inline",
                "inline": {
                    "status": ack_result.status,
                    "duplicate": ack_result.duplicate,
                    "delivery_id": ack_result.delivery_record.delivery_id,
                    "delivery_state": ack_result.delivery_record.state,
                    "ack_id": ack_result.ack_record.ack_id,
                    "ack_connection_id": ack_result.ack_record.ack_connection_id,
                    "ack_connection_epoch": ack_result.ack_record.ack_connection_epoch,
                    "duplicate_count": ack_result.ack_record.duplicate_count,
                },
            },
            "trace": {
                "trace_id": request.envelope.raw.get("trace", {}).get("trace_id", request.envelope.message_id),
                "request_id": request.envelope.message_id,
            },
        }


class DeliveryNackProcessor(BaseRuntimeProcessor):
    def __init__(self, *, codec: EnvelopeCodec, delivery_registry: RuntimeDeliveryRegistry) -> None:
        self._codec = codec
        self._delivery_registry = delivery_registry

    async def process(self, request: ProcessorRequest) -> ProcessorResponse:
        try:
            nack_result = self._delivery_registry.mark_nacked(
                envelope=request.envelope,
                session_connection_id=request.session.connection_id,
                session_connection_epoch=request.session.connection_epoch,
                session_tenant_id=request.session.tenant_id,
            )

            return ProcessorResponse.respond(
                self._build_nack_result(
                    request=request,
                    nack_result=nack_result,
                )
            )
        except NsEvermoreError as exc:
            return ProcessorResponse.reject(
                self._codec.build_error_envelope(
                    exc,
                    session=request.session,
                    request=request.envelope,
                )
            )

    def _build_nack_result(self, *, request: ProcessorRequest, nack_result) -> dict[str, Any]:
        return {
            "protocol": {
                "version": self._codec.protocol_version_text,
            },
            "message": {
                "message_id": f"{request.envelope.message_id}.result",
                "type": "delivery.nack_result",
                "category": "delivery",
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "best_effort",
            },
            "source": {
                "runtime_id": request.session.runtime_id,
                "connection_id": "runtime",
                "session_id": "runtime",
                "identity": request.session.runtime_id,
                "tenant_id": request.session.tenant_id,
                "component_type": "runtime",
                "capabilities_summary": [
                    "delivery.nack_result",
                ],
                "connection_epoch": 0,
            },
            "target": {
                "kind": "connection",
                "connection_id": request.session.connection_id,
            },
            "delivery": {
                "delivery_id": nack_result.delivery_record.delivery_id,
                "summary_id": nack_result.delivery_record.summary_id,
                "root_delivery_id": nack_result.delivery_record.root_delivery_id,
                "attempt": nack_result.delivery_record.attempt_count,
                "ack_timeout_ms": nack_result.delivery_record.ack_timeout_ms,
                "replay_epoch": 0,
            },
            "payload": {
                "mode": "inline",
                "inline": {
                    "status": nack_result.status,
                    "duplicate": nack_result.duplicate,
                    "delivery_id": nack_result.delivery_record.delivery_id,
                    "delivery_state": nack_result.delivery_record.state,
                    "nack_id": nack_result.nack_record.nack_id,
                    "nack_connection_id": nack_result.nack_record.nack_connection_id,
                    "nack_connection_epoch": nack_result.nack_record.nack_connection_epoch,
                    "reason": nack_result.nack_record.reason,
                    "reason_error_code": nack_result.nack_record.reason_error_code,
                    "retryable": nack_result.nack_record.retryable,
                    "duplicate_count": nack_result.nack_record.duplicate_count,
                },
            },
            "trace": {
                "trace_id": request.envelope.raw.get("trace", {}).get("trace_id", request.envelope.message_id),
                "request_id": request.envelope.message_id,
            },
        }


class DeliveryDeferProcessor(BaseRuntimeProcessor):
    def __init__(self, *, codec: EnvelopeCodec, delivery_registry: RuntimeDeliveryRegistry) -> None:
        self._codec = codec
        self._delivery_registry = delivery_registry

    async def process(self, request: ProcessorRequest) -> ProcessorResponse:
        try:
            defer_result = self._delivery_registry.mark_deferred(
                envelope=request.envelope,
                session_connection_id=request.session.connection_id,
                session_connection_epoch=request.session.connection_epoch,
                session_tenant_id=request.session.tenant_id,
            )

            return ProcessorResponse.respond(
                self._build_defer_result(
                    request=request,
                    defer_result=defer_result,
                )
            )
        except NsEvermoreError as exc:
            return ProcessorResponse.reject(
                self._codec.build_error_envelope(
                    exc,
                    session=request.session,
                    request=request.envelope,
                )
            )

    def _build_defer_result(self, *, request: ProcessorRequest, defer_result) -> dict[str, Any]:
        return {
            "protocol": {
                "version": self._codec.protocol_version_text,
            },
            "message": {
                "message_id": f"{request.envelope.message_id}.result",
                "type": "delivery.defer_result",
                "category": "delivery",
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "best_effort",
            },
            "source": {
                "runtime_id": request.session.runtime_id,
                "connection_id": "runtime",
                "session_id": "runtime",
                "identity": request.session.runtime_id,
                "tenant_id": request.session.tenant_id,
                "component_type": "runtime",
                "capabilities_summary": [
                    "delivery.defer_result",
                ],
                "connection_epoch": 0,
            },
            "target": {
                "kind": "connection",
                "connection_id": request.session.connection_id,
            },
            "delivery": {
                "delivery_id": defer_result.delivery_record.delivery_id,
                "summary_id": defer_result.delivery_record.summary_id,
                "root_delivery_id": defer_result.delivery_record.root_delivery_id,
                "attempt": defer_result.delivery_record.attempt_count,
                "ack_timeout_ms": defer_result.delivery_record.ack_timeout_ms,
                "replay_epoch": 0,
            },
            "payload": {
                "mode": "inline",
                "inline": {
                    "status": defer_result.status,
                    "delivery_id": defer_result.delivery_record.delivery_id,
                    "delivery_state": defer_result.delivery_record.state,
                    "defer_id": defer_result.defer_record.defer_id,
                    "defer_connection_id": defer_result.defer_record.defer_connection_id,
                    "defer_connection_epoch": defer_result.defer_record.defer_connection_epoch,
                    "defer_ms": defer_result.defer_record.defer_ms,
                    "defer_sequence": defer_result.defer_record.defer_sequence,
                    "previous_ack_deadline_at": defer_result.defer_record.previous_ack_deadline_at,
                    "new_ack_deadline_at": defer_result.defer_record.new_ack_deadline_at,
                    "total_defer_ms": defer_result.total_defer_ms,
                    "defer_count": defer_result.defer_count,
                },
            },
            "trace": {
                "trace_id": request.envelope.raw.get("trace", {}).get("trace_id", request.envelope.message_id),
                "request_id": request.envelope.message_id,
            },
        }


class RegisteredOnlyProcessor(BaseRuntimeProcessor):
    def __init__(self, *, codec: EnvelopeCodec) -> None:
        self._codec = codec

    async def process(self, request: ProcessorRequest) -> ProcessorResponse:
        error = NsRuntimeEnvelopeSchemaError(
            "Runtime message type is registered but not implemented in this sub-stage.",
            details={
                "message_type": request.envelope.message_type,
                "stage": "runtime-1.1-protocol-and-processor-foundation",
            },
        )
        return ProcessorResponse.respond(self._codec.build_error_envelope(error, session=request.session, request=request.envelope))


class HeartbeatProcessor(BaseRuntimeProcessor):
    def __init__(self, *, codec: EnvelopeCodec) -> None:
        self._codec = codec

    async def process(self, request: ProcessorRequest) -> ProcessorResponse:
        return ProcessorResponse.respond(
            {
                "protocol": {
                    "version": self._codec.protocol_version_text,
                },
                "message": {
                    "message_id": f"{request.envelope.message_id}.ack",
                    "type": "connection.heartbeat_ack",
                    "category": "control",
                    "priority": 100,
                    "created_at": utc_now_iso(),
                    "reliability": "best_effort",
                },
                "source": {
                    "runtime_id": request.session.runtime_id,
                    "connection_id": "runtime",
                    "session_id": "runtime",
                    "identity": request.session.runtime_id,
                    "tenant_id": request.session.tenant_id,
                    "component_type": "runtime",
                    "capabilities_summary": [
                        "connection.heartbeat_ack"
                    ],
                    "connection_epoch": 0,
                },
                "target": {
                    "kind": "connection",
                    "connection_id": request.session.connection_id,
                },
                "payload": {
                    "mode": "inline",
                    "inline": {
                        "server_time": utc_now_iso(),
                        "runtime_id": request.session.runtime_id,
                        "role": request.session.role,
                    },
                },
                "trace": {
                    "trace_id": request.envelope.raw.get("trace", {}).get("trace_id", request.envelope.message_id),
                    "request_id": request.envelope.message_id,
                },
            }
        )


class RuntimeHealthProcessor(BaseRuntimeProcessor):
    def __init__(self, *, codec: EnvelopeCodec, health_snapshot_provider: Callable[[], Mapping[str, Any]] | None = None) -> None:
        self._codec = codec
        self._health_snapshot_provider = health_snapshot_provider

    async def process(self, request: ProcessorRequest) -> ProcessorResponse:
        inline_payload: dict[str, Any] = {
            "status": "ok",
            "runtime_id": request.session.runtime_id,
            "role": request.session.role,
            "server_time": utc_now_iso(),
        }

        if self._health_snapshot_provider is not None:
            inline_payload["runtime"] = dict(self._health_snapshot_provider())

        return ProcessorResponse.respond(
            {
                "protocol": {
                    "version": self._codec.protocol_version_text,
                },
                "message": {
                    "message_id": f"{request.envelope.message_id}.result",
                    "type": "runtime.control.health_result",
                    "category": "control",
                    "priority": 100,
                    "created_at": utc_now_iso(),
                    "reliability": "best_effort",
                },
                "source": {
                    "runtime_id": request.session.runtime_id,
                    "connection_id": "runtime",
                    "session_id": "runtime",
                    "identity": request.session.runtime_id,
                    "tenant_id": request.session.tenant_id,
                    "component_type": "runtime",
                    "capabilities_summary": [
                        "runtime.control.health_result"
                    ],
                    "connection_epoch": 0,
                },
                "target": {
                    "kind": "connection",
                    "connection_id": request.session.connection_id,
                },
                "payload": {
                    "mode": "inline",
                    "inline": inline_payload,
                },
                "trace": {
                    "trace_id": request.envelope.raw.get("trace", {}).get("trace_id", request.envelope.message_id),
                    "request_id": request.envelope.message_id,
                },
            }
        )


class ProcessorRegistry:
    def __init__(self) -> None:
        self._specs: dict[str, MessageTypeSpec] = {}
        self._processors: dict[str, BaseRuntimeProcessor] = {}

    def register(self, spec: MessageTypeSpec, processor: BaseRuntimeProcessor) -> None:
        if spec.message_type in self._specs:
            raise NsRuntimeEnvelopeSchemaError("Runtime message type is registered repeatedly.", details={"message_type": spec.message_type})

        self._specs[spec.message_type] = spec
        self._processors[spec.message_type] = processor

    def get_spec(self, message_type: str) -> MessageTypeSpec | None:
        return self._specs.get(message_type)

    def get_processor(self, message_type: str) -> BaseRuntimeProcessor:
        processor = self._processors.get(message_type)
        if processor is None:
            raise NsRuntimeUnsupportedMessageTypeError(details={"message_type": message_type})
        return processor

    def list_specs(self) -> tuple[MessageTypeSpec, ...]:
        return tuple(self._specs[key] for key in sorted(self._specs.keys()))


class ProcessorPipeline:
    def __init__(self, *, codec: EnvelopeCodec, registry: ProcessorRegistry, generic_processors: Iterable[BaseRuntimeProcessor]) -> None:
        self._codec = codec
        self._registry = registry
        self._generic_processors = tuple(generic_processors)

    async def process(self, envelope: Envelope, session: RuntimeSessionContext, *, config_version: str, policy_version: str) -> ProcessorResponse:
        request = ProcessorRequest(
            envelope=envelope,
            session=session,
            received_at=utc_now_iso(),
            config_version=config_version,
            policy_version=policy_version,
        )

        for processor in self._generic_processors:
            response = await processor.process(request)
            if response.action in {"respond", "reject"}:
                return response

        message_processor = self._registry.get_processor(envelope.message_type)
        return await message_processor.process(request)


def build_default_processor_registry(
        codec: EnvelopeCodec,
        *,
        health_snapshot_provider: Callable[[], Mapping[str, Any]] | None = None,
        target_resolver: RuntimeTargetResolver | None = None,
        local_forwarder: RuntimeLocalEnvelopeForwarder | None = None,
        delivery_registry: RuntimeDeliveryRegistry | None = None,
) -> ProcessorRegistry:
    registry = ProcessorRegistry()
    registered_only = RegisteredOnlyProcessor(codec=codec)

    for spec in _build_builtin_message_type_specs():
        processor: BaseRuntimeProcessor = registered_only

        if spec.message_type == "connection.heartbeat":
            processor = HeartbeatProcessor(codec=codec)
        elif spec.message_type == "runtime.control.health":
            processor = RuntimeHealthProcessor(
                codec=codec,
                health_snapshot_provider=health_snapshot_provider,
            )
        elif spec.message_type == "task.dispatch" and target_resolver is not None and local_forwarder is not None and delivery_registry is not None:
            processor = LocalTaskDispatchProcessor(
                codec=codec,
                target_resolver=target_resolver,
                local_forwarder=local_forwarder,
                delivery_registry=delivery_registry,
            )
        elif spec.message_type == "delivery.ack" and delivery_registry is not None:
            processor = DeliveryAckProcessor(
                codec=codec,
                delivery_registry=delivery_registry,
            )
        elif spec.message_type == "delivery.nack" and delivery_registry is not None:
            processor = DeliveryNackProcessor(
                codec=codec,
                delivery_registry=delivery_registry,
            )
        elif spec.message_type == "delivery.defer" and delivery_registry is not None:
            processor = DeliveryDeferProcessor(
                codec=codec,
                delivery_registry=delivery_registry,
            )

        registry.register(spec, processor)

    return registry


def build_default_processor_pipeline(codec: EnvelopeCodec, registry: ProcessorRegistry, *, target_resolver: RuntimeTargetResolver | None = None) -> ProcessorPipeline:
    generic_processors: list[BaseRuntimeProcessor] = [
        MessageTypeAuthProcessor(registry=registry, codec=codec),
    ]

    if target_resolver is not None:
        generic_processors.append(
            TargetLookupProcessor(
                codec=codec,
                target_resolver=target_resolver,
            )
        )

    generic_processors.append(AuditMarkProcessor())

    return ProcessorPipeline(
        codec=codec,
        registry=registry,
        generic_processors=tuple(generic_processors),
    )


def _build_builtin_message_type_specs() -> tuple[MessageTypeSpec, ...]:
    raw_specs: tuple[Mapping[str, Any], ...] = (
        {"message_type": "connection.hello", "category": "connection", "reliability": "best_effort", "implemented": False},
        {"message_type": "connection.accepted", "category": "connection", "reliability": "best_effort", "implemented": False},
        {"message_type": "connection.rejected", "category": "connection", "reliability": "best_effort", "implemented": False},
        {"message_type": "connection.reauth", "category": "connection", "reliability": "best_effort", "implemented": False},
        {"message_type": "connection.reauth_accepted", "category": "connection", "reliability": "best_effort", "implemented": False},
        {"message_type": "connection.reauth_rejected", "category": "connection", "reliability": "best_effort", "implemented": False},
        {"message_type": "connection.heartbeat", "category": "control", "reliability": "best_effort", "implemented": True},
        {"message_type": "connection.heartbeat_ack", "category": "control", "reliability": "best_effort", "implemented": False},
        {"message_type": "connection.drain", "category": "control", "reliability": "reliable", "implemented": False},
        {"message_type": "task.dispatch", "category": "task", "required_groups": ("target",), "required_capabilities": ("task.dispatch",), "reliability": "critical", "implemented": True},
        {"message_type": "task.result", "category": "task", "required_groups": ("target",), "reliability": "reliable", "implemented": False},
        {"message_type": "delivery.accepted", "category": "delivery", "reliability": "best_effort", "implemented": False},
        {"message_type": "delivery.rejected", "category": "delivery", "reliability": "best_effort", "implemented": False},
        {"message_type": "delivery.ack", "category": "delivery", "required_groups": ("delivery",), "reliability": "critical", "implemented": True},
        {"message_type": "delivery.ack_result", "category": "delivery", "required_groups": ("delivery",), "reliability": "best_effort", "implemented": False},
        {"message_type": "delivery.nack", "category": "delivery", "required_groups": ("delivery", "payload"), "reliability": "critical", "implemented": True},
        {"message_type": "delivery.nack_result", "category": "delivery", "required_groups": ("delivery",), "reliability": "best_effort", "implemented": False},
        {"message_type": "delivery.defer", "category": "delivery", "required_groups": ("delivery", "payload"), "reliability": "critical", "implemented": True},
        {"message_type": "delivery.defer_result", "category": "delivery", "required_groups": ("delivery",), "reliability": "best_effort", "implemented": False},
        {"message_type": "delivery.dead_letter", "category": "delivery", "required_groups": ("delivery",), "reliability": "critical", "implemented": False},
        {"message_type": "delivery.replay", "category": "delivery", "required_groups": ("delivery",), "required_capabilities": ("delivery.replay",), "reliability": "critical", "implemented": False},
        {"message_type": "delivery.cancel", "category": "delivery", "required_groups": ("delivery",), "required_capabilities": ("delivery.cancel",), "reliability": "critical", "implemented": False},
        {"message_type": "delivery.hold", "category": "delivery", "required_groups": ("delivery",), "required_capabilities": ("delivery.hold",), "reliability": "critical", "implemented": False},
        {"message_type": "delivery.status_query", "category": "delivery", "required_capabilities": ("delivery.status_query",), "reliability": "best_effort", "implemented": False},
        {"message_type": "stream.start", "category": "stream", "required_groups": ("target", "stream"), "reliability": "critical", "implemented": False},
        {"message_type": "stream.chunk", "category": "stream", "required_groups": ("target", "stream", "delivery"), "reliability": "critical", "implemented": False},
        {"message_type": "stream.end", "category": "stream", "required_groups": ("target", "stream", "delivery"), "reliability": "critical", "implemented": False},
        {"message_type": "stream.ack", "category": "stream", "required_groups": ("stream", "delivery"), "reliability": "critical", "implemented": False},
        {"message_type": "stream.status_query", "category": "stream", "required_capabilities": ("stream.status_query",), "reliability": "best_effort", "implemented": False},
        {"message_type": "runtime.control.health", "category": "control", "reliability": "best_effort", "implemented": True},
        {"message_type": "runtime.control.health_result", "category": "control", "reliability": "best_effort", "implemented": False},
        {"message_type": "runtime.control.node_status", "category": "control", "required_capabilities": ("runtime.management",), "reliability": "best_effort", "implemented": False},
        {"message_type": "runtime.control.connection_status", "category": "control", "required_capabilities": ("runtime.management",), "reliability": "best_effort", "implemented": False},
        {"message_type": "runtime.control.kick_connection", "category": "control", "required_capabilities": ("runtime.management",), "reliability": "critical", "implemented": False},
        {"message_type": "runtime.control.replay_delivery", "category": "control", "required_capabilities": ("runtime.management",), "reliability": "critical", "implemented": False},
        {"message_type": "runtime.control.cleanup_delivery", "category": "control", "required_capabilities": ("runtime.management",), "reliability": "critical", "implemented": False},
        {"message_type": "runtime.control.isolate_node", "category": "control", "required_capabilities": ("runtime.management",), "reliability": "critical", "implemented": False},
        {"message_type": "runtime.control.recover_node", "category": "control", "required_capabilities": ("runtime.management",), "reliability": "critical", "implemented": False},
        {"message_type": "runtime.control.switch_master", "category": "control", "required_capabilities": ("runtime.management",), "reliability": "critical", "implemented": False},
        {"message_type": "runtime.control.adjust_rate_limit", "category": "control", "required_capabilities": ("runtime.management",), "reliability": "critical", "implemented": False},
        {"message_type": "runtime.control.config_update", "category": "control", "required_capabilities": ("runtime.management",), "reliability": "critical", "implemented": False},
        {"message_type": "runtime.control.state_snapshot", "category": "control", "required_capabilities": ("runtime.management",), "reliability": "best_effort", "implemented": False},
        {"message_type": "cluster.event.node_joined", "category": "cluster", "required_capabilities": ("runtime.node",), "reliability": "reliable", "implemented": False},
        {"message_type": "cluster.event.node_left", "category": "cluster", "required_capabilities": ("runtime.node",), "reliability": "reliable", "implemented": False},
        {"message_type": "cluster.event.master_elected", "category": "cluster", "required_capabilities": ("runtime.node",), "reliability": "critical", "implemented": False},
        {"message_type": "cluster.event.heartbeat", "category": "cluster", "required_capabilities": ("runtime.node",), "reliability": "best_effort", "implemented": False},
        {"message_type": "cluster.event.config_drift", "category": "cluster", "required_capabilities": ("runtime.node",), "reliability": "critical", "implemented": False},
        {"message_type": "cluster.event.delivery_transferred", "category": "cluster", "required_capabilities": ("runtime.node",), "reliability": "critical", "implemented": False},
        {"message_type": "runtime.error", "category": "control", "reliability": "best_effort", "implemented": False},
    )

    specs: list[MessageTypeSpec] = []
    for raw in raw_specs:
        specs.append(
            MessageTypeSpec(
                message_type=str(raw["message_type"]),
                category=str(raw["category"]),
                required_groups=tuple(raw.get("required_groups", ())),
                allowed_groups=tuple(raw.get("allowed_groups", ())),
                required_capabilities=tuple(raw.get("required_capabilities", ())),
                reliability=raw.get("reliability", "best_effort"),  # type: ignore[arg-type]
                audit_action=f"runtime.message.{raw['message_type']}",
                implemented=bool(raw.get("implemented", False)),
            )
        )

    return tuple(specs)
