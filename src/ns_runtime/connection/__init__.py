# -*- coding: utf-8 -*-
"""Transport-independent logical connection lifecycle contracts."""

from __future__ import annotations

from .accepted import (
    ACCEPTED_HEARTBEAT_FIELDS,
    ACCEPTED_PAYLOAD_FIELDS,
    AcceptedHeartbeatPolicy,
    ConnectionAcceptedEnvelopeBuilder,
    ConnectionAdmissionActivator,
)
from .authentication import (
    AuthenticatedHello,
    ConnectionHandshakeAuthenticator,
)
from .binding import (
    LogicalConnectionTransportMap,
    LogicalSessionIdentityFactory,
    LogicalTransportMappingSnapshot,
    NetworkPathBinding,
    TransportSessionBinding,
)
from .drain import (
    DRAIN_ALLOWED_MESSAGE_TYPES,
    ConnectionDrainEnvelopeHandler,
    ConnectionDrainService,
    DrainPolicy,
    DrainSnapshot,
    DrainingMessageDisposition,
    DrainingMessageGate,
)
from .handshake import ConnectionHelloReceiver
from .hello import (
    HELLO_EXTENSION_REGISTRY,
    HELLO_RESUME_NAMESPACE,
    HandshakeCredential,
    HelloClaimParser,
    HelloResumeRequest,
    ParsedHello,
    PendingHelloClaims,
)
from .heartbeat import (
    HEARTBEAT_ACK_PAYLOAD_FIELDS,
    HEARTBEAT_PAYLOAD_FIELDS,
    ConnectionHeartbeatService,
    EnvelopeHeartbeatOutcome,
    HeartbeatPolicy,
    HeartbeatSnapshot,
)
from .iam import (
    DeterministicTestIamAdapter,
    FailClosedHandshakeIamAdapter,
    HandshakeIamAdapter,
    HandshakeIamAuthority,
    HandshakeIamRequest,
    TestIamAction,
    TestIamOutcome,
)
from .index import (
    ConnectionIndexEntrySnapshot,
    LocalConnectionIndex,
    LocalConnectionIndexSnapshot,
)
from .session import (
    CapabilityPolicy,
    CapabilityRule,
    HandshakeSessionNegotiator,
    LogicalSessionIdentity,
    NegotiatedSession,
    P05_CAPABILITY_POLICY,
    SessionContext,
)
from .state import (
    LogicalConnectionCloseReason,
    LogicalConnectionState,
    LogicalConnectionStateMachine,
    LogicalConnectionStateSnapshot,
)


__all__ = (
    "ACCEPTED_HEARTBEAT_FIELDS",
    "ACCEPTED_PAYLOAD_FIELDS",
    "AcceptedHeartbeatPolicy",
    "AuthenticatedHello",
    "CapabilityPolicy",
    "CapabilityRule",
    "ConnectionHelloReceiver",
    "ConnectionHandshakeAuthenticator",
    "ConnectionHeartbeatService",
    "ConnectionAcceptedEnvelopeBuilder",
    "ConnectionAdmissionActivator",
    "ConnectionDrainService",
    "ConnectionDrainEnvelopeHandler",
    "ConnectionIndexEntrySnapshot",
    "DeterministicTestIamAdapter",
    "DRAIN_ALLOWED_MESSAGE_TYPES",
    "DrainPolicy",
    "DrainSnapshot",
    "DrainingMessageDisposition",
    "DrainingMessageGate",
    "FailClosedHandshakeIamAdapter",
    "HELLO_EXTENSION_REGISTRY",
    "HELLO_RESUME_NAMESPACE",
    "HEARTBEAT_ACK_PAYLOAD_FIELDS",
    "HEARTBEAT_PAYLOAD_FIELDS",
    "HandshakeCredential",
    "HandshakeIamAdapter",
    "HandshakeIamAuthority",
    "HandshakeIamRequest",
    "HandshakeSessionNegotiator",
    "HelloClaimParser",
    "HelloResumeRequest",
    "HeartbeatPolicy",
    "HeartbeatSnapshot",
    "LogicalConnectionCloseReason",
    "LogicalConnectionState",
    "LogicalConnectionStateMachine",
    "LogicalConnectionStateSnapshot",
    "LogicalConnectionTransportMap",
    "LogicalSessionIdentity",
    "LogicalSessionIdentityFactory",
    "LogicalTransportMappingSnapshot",
    "LocalConnectionIndex",
    "LocalConnectionIndexSnapshot",
    "NetworkPathBinding",
    "NegotiatedSession",
    "P05_CAPABILITY_POLICY",
    "ParsedHello",
    "PendingHelloClaims",
    "SessionContext",
    "EnvelopeHeartbeatOutcome",
    "TestIamAction",
    "TestIamOutcome",
    "TransportSessionBinding",
)
