# -*- coding: utf-8 -*-
"""Transport-independent logical connection lifecycle contracts."""

from __future__ import annotations

from .authentication import (
    AuthenticatedHello,
    ConnectionHandshakeAuthenticator,
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
from .iam import (
    DeterministicTestIamAdapter,
    FailClosedHandshakeIamAdapter,
    HandshakeIamAdapter,
    HandshakeIamAuthority,
    HandshakeIamRequest,
    TestIamAction,
    TestIamOutcome,
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
    "AuthenticatedHello",
    "CapabilityPolicy",
    "CapabilityRule",
    "ConnectionHelloReceiver",
    "ConnectionHandshakeAuthenticator",
    "DeterministicTestIamAdapter",
    "FailClosedHandshakeIamAdapter",
    "HELLO_EXTENSION_REGISTRY",
    "HELLO_RESUME_NAMESPACE",
    "HandshakeCredential",
    "HandshakeIamAdapter",
    "HandshakeIamAuthority",
    "HandshakeIamRequest",
    "HandshakeSessionNegotiator",
    "HelloClaimParser",
    "HelloResumeRequest",
    "LogicalConnectionCloseReason",
    "LogicalConnectionState",
    "LogicalConnectionStateMachine",
    "LogicalConnectionStateSnapshot",
    "LogicalSessionIdentity",
    "NegotiatedSession",
    "P05_CAPABILITY_POLICY",
    "ParsedHello",
    "PendingHelloClaims",
    "SessionContext",
    "TestIamAction",
    "TestIamOutcome",
)
