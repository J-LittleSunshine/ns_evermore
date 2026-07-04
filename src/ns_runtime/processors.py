# -*- coding: utf-8 -*-
from __future__ import annotations

from abc import (
    ABC,
    abstractmethod
)
from typing import (
    Any,
    Iterable,
    Mapping,
    TYPE_CHECKING
)

from ns_common.exceptions import (
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeUnauthorizedMessageTypeError,
    NsRuntimeUnsupportedMessageTypeError,
)
from ns_runtime.models import (
    Envelope,
    MessageTypeSpec,
    ProcessorRequest,
    ProcessorResponse,
    RuntimeSessionContext,
    utc_now_iso,
)
from ns_runtime.protocol import EnvelopeCodec

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

        return ProcessorResponse.continue_next()


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
    def __init__(self, *, codec: EnvelopeCodec) -> None:
        self._codec = codec

    async def process(self, request: ProcessorRequest) -> ProcessorResponse:
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
                    "inline": {
                        "status": "ok",
                        "runtime_id": request.session.runtime_id,
                        "role": request.session.role,
                        "server_time": utc_now_iso(),
                    },
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


def build_default_processor_registry(codec: EnvelopeCodec) -> ProcessorRegistry:
    registry = ProcessorRegistry()
    registered_only = RegisteredOnlyProcessor(codec=codec)

    for spec in _build_builtin_message_type_specs():
        processor: BaseRuntimeProcessor = registered_only

        if spec.message_type == "connection.heartbeat":
            processor = HeartbeatProcessor(codec=codec)
        elif spec.message_type == "runtime.control.health":
            processor = RuntimeHealthProcessor(codec=codec)

        registry.register(spec, processor)

    return registry


def build_default_processor_pipeline(codec: EnvelopeCodec, registry: ProcessorRegistry) -> ProcessorPipeline:
    return ProcessorPipeline(
        codec=codec,
        registry=registry,
        generic_processors=(
            MessageTypeAuthProcessor(registry=registry, codec=codec),
            AuditMarkProcessor(),
        ),
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
        {"message_type": "task.dispatch", "category": "task", "required_groups": ("target",), "required_capabilities": ("task.dispatch",), "reliability": "critical", "implemented": False},
        {"message_type": "task.result", "category": "task", "required_groups": ("target",), "reliability": "reliable", "implemented": False},
        {"message_type": "delivery.ack", "category": "delivery", "required_groups": ("delivery",), "reliability": "critical", "implemented": False},
        {"message_type": "delivery.nack", "category": "delivery", "required_groups": ("delivery",), "reliability": "critical", "implemented": False},
        {"message_type": "delivery.defer", "category": "delivery", "required_groups": ("delivery",), "reliability": "critical", "implemented": False},
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
