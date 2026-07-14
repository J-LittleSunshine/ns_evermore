# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from typing import (
    Any,
    TYPE_CHECKING
)

from ns_common.logger import get_ns_logger
from ns_runtime.admission import (
    LocalRuntimeAdmissionController,
    RuntimeAdmissionController,
    RuntimeAdmissionPolicy,
)
from ns_runtime.auth import (
    LocalTokenRuntimeAuthenticator,
    RuntimeAuthenticator
)
from ns_runtime.cluster import (
    LocalRuntimeClusterCoordinator,
    RuntimeClusterCoordinator,
)
from ns_runtime.delivery import (
    RuntimeAckTimeoutScanResult,
    RuntimeDeadLetterScanResult,
    RuntimeDeliveryRegistry,
    RuntimeMessageDeliverySummary,
)
from ns_runtime.handshake import (
    RuntimeHandshakeOutcome,
    RuntimeHandshakeService
)
from ns_runtime.models import (
    ProcessorResponse,
    RuntimeRole,
    RuntimeSessionContext,
)
from ns_runtime.outbound import (
    RuntimeConnectionWriterRegistry,
    RuntimeLocalEnvelopeForwarder,
    RuntimeLocalRetryScanResult,
)
from ns_runtime.payload_reference import (
    PayloadReferenceValidator,
    UnavailablePayloadReferenceValidator,
)
from ns_runtime.processors import (
    ProcessorPipeline,
    ProcessorRegistry,
    build_default_processor_pipeline,
    build_default_processor_registry,
)
from ns_runtime.protocol import EnvelopeCodec
from ns_runtime.routing import RuntimeTargetResolver
from ns_runtime.session import (
    RuntimeConnectionRecord,
    RuntimeSessionRegistry
)
from ns_runtime.transport import (
    RuntimeWebSocketTransport,
    RuntimeWebSocketTransportConfig
)

if TYPE_CHECKING:
    pass


class RuntimeService:
    def __init__(
            self,
            *,
            runtime_id: str,
            codec: EnvelopeCodec,
            registry: ProcessorRegistry,
            pipeline: ProcessorPipeline,
            session_registry: RuntimeSessionRegistry,
            writer_registry: RuntimeConnectionWriterRegistry,
            delivery_registry: RuntimeDeliveryRegistry,
            admission_controller: RuntimeAdmissionController,
            cluster_coordinator: RuntimeClusterCoordinator,
            local_forwarder: RuntimeLocalEnvelopeForwarder,
            handshake_service: RuntimeHandshakeService,
            target_resolver: RuntimeTargetResolver,
            config_version: str = "local:1",
            policy_version: str = "local:1",
    ) -> None:
        self._runtime_id = runtime_id
        self._codec = codec
        self._registry = registry
        self._pipeline = pipeline
        self._session_registry = session_registry
        self._writer_registry = writer_registry
        self._delivery_registry = delivery_registry
        self._admission_controller = admission_controller
        self._cluster_coordinator = cluster_coordinator
        self._local_forwarder = local_forwarder
        self._handshake_service = handshake_service
        self._target_resolver = target_resolver
        self._config_version = config_version
        self._policy_version = policy_version
        self._logger = get_ns_logger("ns_runtime", True)

    @classmethod
    def build_default(
            cls,
            *,
            runtime_id: str,
            authenticator: RuntimeAuthenticator | None = None,
            payload_reference_validator: (
                    PayloadReferenceValidator | None
            ) = None,
            admission_policy: (
                    RuntimeAdmissionPolicy | None
            ) = None,
            admission_controller: (
                    RuntimeAdmissionController | None
            ) = None,
            runtime_role: RuntimeRole = "singleton",
            cluster_coordinator: (
                    RuntimeClusterCoordinator | None
            ) = None,
    ) -> "RuntimeService":
        codec = EnvelopeCodec(
            runtime_id=runtime_id
        )
        session_registry = RuntimeSessionRegistry(
            runtime_id=runtime_id
        )
        writer_registry = (
            RuntimeConnectionWriterRegistry()
        )
        delivery_registry = RuntimeDeliveryRegistry()

        if (
                admission_policy is not None
                and admission_controller is not None
        ):
            raise ValueError(
                "admission_policy and admission_controller "
                "cannot be provided together."
            )

        resolved_admission_controller = (
                admission_controller
                or LocalRuntimeAdmissionController(
            delivery_registry=delivery_registry,
            policy=admission_policy,
        )
        )

        if (
                cluster_coordinator is not None
                and runtime_role != "singleton"
        ):
            raise ValueError(
                "runtime_role and cluster_coordinator "
                "cannot be provided together."
            )

        resolved_cluster_coordinator = (
                cluster_coordinator
                or LocalRuntimeClusterCoordinator(
                    runtime_id=runtime_id,
                    initial_role=runtime_role,
                )
        )

        if (
                resolved_cluster_coordinator.runtime_id
                != runtime_id
        ):
            raise ValueError(
                "cluster_coordinator runtime_id "
                "must match RuntimeService runtime_id."
            )

        local_forwarder = (
            RuntimeLocalEnvelopeForwarder(
                writer_registry=writer_registry,
                delivery_registry=delivery_registry,
            )
        )
        target_resolver = RuntimeTargetResolver(
            runtime_id=runtime_id,
            session_registry=session_registry,
        )

        resolved_payload_reference_validator = (
                payload_reference_validator
                or UnavailablePayloadReferenceValidator()
        )

        def build_health_snapshot() -> dict[str, object]:
            return {
                "cluster": (
                    resolved_cluster_coordinator
                    .build_snapshot()
                    .to_dict()
                ),
                "connections": (
                    session_registry
                    .build_health_snapshot()
                ),
            }

        registry = build_default_processor_registry(
            codec,
            health_snapshot_provider=build_health_snapshot,
            runtime_role_provider=lambda: (
                resolved_cluster_coordinator.role
            ),
            target_resolver=target_resolver,
            local_forwarder=local_forwarder,
            delivery_registry=delivery_registry,
            payload_reference_validator=resolved_payload_reference_validator,
            admission_controller=resolved_admission_controller
        )
        pipeline = build_default_processor_pipeline(
            codec,
            registry,
            target_resolver=target_resolver,
        )

        resolved_authenticator = (
                authenticator
                or LocalTokenRuntimeAuthenticator(
            expected_token="local-dev-token"
        )
        )
        handshake_service = RuntimeHandshakeService(
            runtime_id=runtime_id,
            codec=codec,
            authenticator=resolved_authenticator,
            session_registry=session_registry,
            runtime_role_provider=lambda: (
                resolved_cluster_coordinator.role
            ),
        )

        return cls(
            runtime_id=runtime_id,
            codec=codec,
            registry=registry,
            pipeline=pipeline,
            session_registry=session_registry,
            writer_registry=writer_registry,
            delivery_registry=delivery_registry,
            local_forwarder=local_forwarder,
            handshake_service=handshake_service,
            target_resolver=target_resolver,
            admission_controller=(
                resolved_admission_controller
            ),
            cluster_coordinator=(
                resolved_cluster_coordinator
            ),
        )

    @property
    def runtime_id(self) -> str:
        return self._runtime_id

    @property
    def session_registry(self) -> RuntimeSessionRegistry:
        return self._session_registry

    @property
    def target_resolver(self) -> RuntimeTargetResolver:
        return self._target_resolver

    @property
    def writer_registry(self) -> RuntimeConnectionWriterRegistry:
        return self._writer_registry

    @property
    def delivery_registry(self) -> RuntimeDeliveryRegistry:
        return self._delivery_registry

    @property
    def admission_controller(self) -> RuntimeAdmissionController:
        return self._admission_controller

    @property
    def cluster_coordinator(
            self,
    ) -> RuntimeClusterCoordinator:
        return self._cluster_coordinator

    def build_runtime_snapshot(
            self,
    ) -> dict[str, object]:
        return {
            "cluster": (
                self._cluster_coordinator
                .build_snapshot()
                .to_dict()
            ),
            "connections": (
                self._session_registry
                .build_health_snapshot()
            ),
        }

    def get_message_summary(self, message_id: str, *, tenant_id: str | None = None) -> RuntimeMessageDeliverySummary | None:
        return self._delivery_registry.get_message_summary(
            message_id,
            tenant_id=tenant_id,
        )

    def list_message_summaries(self) -> tuple[RuntimeMessageDeliverySummary, ...]:
        return self._delivery_registry.list_message_summaries()

    def scan_ack_timeouts(self) -> RuntimeAckTimeoutScanResult:
        return self._delivery_registry.scan_ack_timeouts()

    async def scan_retry_scheduled(self) -> RuntimeLocalRetryScanResult:
        return await self._local_forwarder.scan_retry_scheduled()

    def scan_dead_letters(self) -> RuntimeDeadLetterScanResult:
        return self._delivery_registry.scan_dead_letters()

    @property
    def local_forwarder(self) -> RuntimeLocalEnvelopeForwarder:
        return self._local_forwarder

    def resolve_target(self, frame_text: str, session: RuntimeSessionContext) -> dict[str, Any] | None:
        envelope = self._codec.parse_inbound(frame_text, session)
        decision = self._target_resolver.resolve(envelope, session)
        if decision is None:
            return None

        return decision.to_dict()

    def list_message_type_specs(self) -> tuple[dict[str, Any], ...]:
        return tuple(
            {
                "message_type": spec.message_type,
                "category": spec.category,
                "required_groups": list(spec.required_groups),
                "required_capabilities": list(spec.required_capabilities),
                "reliability": spec.reliability,
                "implemented": spec.implemented,
            }
            for spec in self._registry.list_specs()
        )

    def build_transport(self, transport_config: RuntimeWebSocketTransportConfig) -> RuntimeWebSocketTransport:
        return RuntimeWebSocketTransport(
            service=self,
            handshake_service=self._handshake_service,
            session_registry=self._session_registry,
            writer_registry=self._writer_registry,
            config=transport_config,
        )

    async def accept_connection_hello(self, frame_text: str, record: RuntimeConnectionRecord, *, remote_address: str) -> RuntimeHandshakeOutcome:
        return await self._handshake_service.accept(
            frame_text=frame_text,
            record=record,
            remote_address=remote_address,
        )

    async def process_frame(self, frame_text: str, session: RuntimeSessionContext) -> ProcessorResponse:
        try:
            envelope = self._codec.parse_inbound(frame_text, session)
            return await self._pipeline.process(
                envelope,
                session,
                config_version=self._config_version,
                policy_version=self._policy_version,
            )
        except Exception as exc:  # noqa
            self._logger.warning(
                "runtime frame rejected",
                exc_info=True,
                extra={
                    "runtime_id": self._runtime_id,
                    "connection_id": session.connection_id,
                    "tenant_id": session.tenant_id,
                    "exception_class": exc.__class__.__name__,
                },
            )
            return ProcessorResponse.reject(self._codec.build_error_envelope(exc, session=session), should_close=True)

    def build_protocol_error_response(self, exc: Exception, session: RuntimeSessionContext) -> ProcessorResponse:
        return ProcessorResponse.reject(
            self._codec.build_error_envelope(exc, session=session),
            should_close=True,
        )

    def process_frame_sync(self, frame_text: str, session: RuntimeSessionContext) -> ProcessorResponse:
        return asyncio.run(self.process_frame(frame_text, session))

    async def start(self) -> None:
        self._logger.info(
            "runtime service initialized",
            extra={
                "runtime_id": self._runtime_id,
                "runtime_role": (
                    self._cluster_coordinator.role
                ),
                "message_type_count": len(self._registry.list_specs()),
                "config_version": self._config_version,
                "policy_version": self._policy_version,
            },
        )

    async def serve_forever(self, transport_config: RuntimeWebSocketTransportConfig) -> None:
        await self.start()
        transport = self.build_transport(transport_config)
        await transport.serve_forever()
