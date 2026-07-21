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
from .state import (
    LogicalConnectionCloseReason,
    LogicalConnectionState,
    LogicalConnectionStateMachine,
    LogicalConnectionStateSnapshot,
)


__all__ = (
    "AuthenticatedHello",
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
    "HelloClaimParser",
    "HelloResumeRequest",
    "LogicalConnectionCloseReason",
    "LogicalConnectionState",
    "LogicalConnectionStateMachine",
    "LogicalConnectionStateSnapshot",
    "ParsedHello",
    "PendingHelloClaims",
    "TestIamAction",
    "TestIamOutcome",
)
