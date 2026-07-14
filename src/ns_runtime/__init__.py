# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_runtime.admission import (
    LocalRuntimeAdmissionController,
    RuntimeAdmissionController,
    RuntimeAdmissionDecision,
    RuntimeAdmissionPolicy,
    RuntimeAdmissionReason,
    RuntimeAdmissionScope,
    RuntimeAdmissionSnapshot,
)
from ns_runtime.audit import (
    InMemoryRuntimeAuditSink,
    RuntimeAuditEvent,
    RuntimeAuditOutcome,
    RuntimeAuditResultAction,
    RuntimeAuditSink,
)
from ns_runtime.auth import (
    LocalTokenRuntimeAuthenticator,
    RuntimeAuthResult,
    RuntimeAuthenticator
)
from ns_runtime.cluster import (
    LocalRuntimeClusterCoordinator,
    RuntimeClusterCoordinator,
    RuntimeClusterSnapshot,
    RuntimeClusterState,
    RuntimeLeaderLease,
)
from ns_runtime.cluster_store import (
    InMemoryRuntimeLeaderLeaseStore,
    RuntimeLeaderLeaseStore,
    RuntimeLeaderLeaseStoreSnapshot,
    StateStoreRuntimeLeaderLeaseStore,
)
from ns_runtime.delivery import (
    RuntimeAckRecord,
    RuntimeAckResult,
    RuntimeAckTimeoutRecord,
    RuntimeAckTimeoutScanResult,
    RuntimeDeadLetterRecord,
    RuntimeDeadLetterReplayability,
    RuntimeDeadLetterScanResult,
    RuntimeDeferRecord,
    RuntimeDeferResult,
    RuntimeDeliveryAttempt,
    RuntimeDeliveryAttemptWriteStatus,
    RuntimeDeliveryDuplicateStatus,
    RuntimeDeliveryRecord,
    RuntimeDeliveryRegistrationResult,
    RuntimeDeliveryRegistry,
    RuntimeDeliveryState,
    RuntimeMessageDeliverySummary,
    RuntimeMessageDeliverySummaryState,
    RuntimeNackRecord,
    RuntimeNackResult
)
from ns_runtime.handshake import (
    ConnectionHello,
    RuntimeHandshakeOutcome,
    RuntimeHandshakeService,
)
from ns_runtime.models import (
    Envelope,
    MessageTypeSpec,
    ProcessorRequest,
    ProcessorResponse,
    RuntimeAuthContext,
    RuntimeSessionContext,
    RuntimeSourceContext,
)
from ns_runtime.outbound import (
    RuntimeConnectionWriter,
    RuntimeConnectionWriterRegistry,
    RuntimeLocalEnvelopeForwarder,
    RuntimeLocalRetryResult,
    RuntimeLocalRetryScanResult,
    RuntimeLocalWriteResult
)
from ns_runtime.payload_reference import (
    PayloadReferenceRejectionReason,
    PayloadReferenceUnavailableReason,
    PayloadReferenceValidationReason,
    PayloadReferenceValidationRequest,
    PayloadReferenceValidationResult,
    PayloadReferenceValidationStatus,
    PayloadReferenceValidator,
    RuntimePayloadReference,
    UnavailablePayloadReferenceValidator,
)
from ns_runtime.processors import (
    BaseRuntimeProcessor,
    ProcessorPipeline,
    ProcessorRegistry,
    build_default_processor_pipeline,
    build_default_processor_registry,
)
from ns_runtime.protocol import EnvelopeCodec
from ns_runtime.routing import (
    RuntimeRouteDecision,
    RuntimeRouteTarget,
    RuntimeTargetResolver,
)
from ns_runtime.service import RuntimeService
from ns_runtime.session import (
    RuntimeConnectionRecord,
    RuntimeSessionRegistry,
)
from ns_runtime.state_store import (
    InMemoryRuntimeStateStore,
    RuntimeStateEntry,
    RuntimeStateStore,
    RuntimeStateStoreCapabilities,
    RuntimeStateWriteResult,
    RuntimeStateWriteStatus,
)
from ns_runtime.transport import (
    RuntimeWebSocketTransport,
    RuntimeWebSocketTransportConfig,
)

if TYPE_CHECKING:
    pass

__all__ = [
    "Envelope",
    "EnvelopeCodec",
    "MessageTypeSpec",
    "ProcessorRequest",
    "ProcessorResponse",
    "RuntimeAuthContext",
    "RuntimeSessionContext",
    "RuntimeSourceContext",
    "RuntimeAuthResult",
    "RuntimeAuthenticator",
    "RuntimeMessageDeliverySummary",
    "RuntimeMessageDeliverySummaryState",
    "LocalTokenRuntimeAuthenticator",
    "ConnectionHello",
    "RuntimeHandshakeOutcome",
    "RuntimeHandshakeService",
    "RuntimeConnectionRecord",
    "RuntimeSessionRegistry",
    "RuntimeWebSocketTransport",
    "RuntimeWebSocketTransportConfig",
    "BaseRuntimeProcessor",
    "ProcessorPipeline",
    "ProcessorRegistry",
    "build_default_processor_pipeline",
    "build_default_processor_registry",
    "RuntimeService",
    "RuntimeRouteDecision",
    "RuntimeRouteTarget",
    "RuntimeTargetResolver",
    "RuntimeConnectionWriter",
    "RuntimeConnectionWriterRegistry",
    "RuntimeLocalEnvelopeForwarder",
    "RuntimeLocalWriteResult",
    "RuntimeDeliveryAttempt",
    "RuntimeDeliveryAttemptWriteStatus",
    "RuntimeDeliveryRecord",
    "RuntimeDeliveryRegistry",
    "RuntimeDeliveryState",
    "RuntimeAckRecord",
    "RuntimeAckResult",
    "RuntimeNackRecord",
    "RuntimeNackResult",
    "RuntimeDeferRecord",
    "RuntimeDeferResult",
    "RuntimeAckTimeoutRecord",
    "RuntimeAckTimeoutScanResult",
    "RuntimeDeadLetterRecord",
    "RuntimeDeadLetterReplayability",
    "RuntimeDeadLetterScanResult",
    "RuntimeLocalRetryResult",
    "RuntimeLocalRetryScanResult",
    "RuntimeDeliveryDuplicateStatus",
    "RuntimeDeliveryRegistrationResult",
    "RuntimePayloadReference",
    "PayloadReferenceValidationStatus",
    "PayloadReferenceValidationReason",
    "PayloadReferenceRejectionReason",
    "PayloadReferenceUnavailableReason",
    "PayloadReferenceValidationRequest",
    "PayloadReferenceValidationResult",
    "PayloadReferenceValidator",
    "UnavailablePayloadReferenceValidator",
    "RuntimeAdmissionScope",
    "RuntimeAdmissionReason",
    "RuntimeAdmissionPolicy",
    "RuntimeAdmissionSnapshot",
    "RuntimeAdmissionDecision",
    "RuntimeAdmissionController",
    "LocalRuntimeAdmissionController",
    "RuntimeClusterState",
    "RuntimeLeaderLease",
    "RuntimeClusterSnapshot",
    "RuntimeClusterCoordinator",
    "LocalRuntimeClusterCoordinator",
    "RuntimeLeaderLeaseStoreSnapshot",
    "RuntimeLeaderLeaseStore",
    "StateStoreRuntimeLeaderLeaseStore",
    "InMemoryRuntimeLeaderLeaseStore",
    "RuntimeStateWriteStatus",
    "RuntimeStateStoreCapabilities",
    "RuntimeStateEntry",
    "RuntimeStateWriteResult",
    "RuntimeStateStore",
    "InMemoryRuntimeStateStore",
    "RuntimeAuditOutcome",
    "RuntimeAuditResultAction",
    "RuntimeAuditEvent",
    "RuntimeAuditSink",
    "InMemoryRuntimeAuditSink",
]

__version__ = "0.2.0"
