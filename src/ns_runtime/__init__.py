# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_runtime.auth import (
    LocalTokenRuntimeAuthenticator,
    RuntimeAuthResult,
    RuntimeAuthenticator
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
from ns_runtime.processors import (
    BaseRuntimeProcessor,
    ProcessorPipeline,
    ProcessorRegistry,
    build_default_processor_pipeline,
    build_default_processor_registry,
)
from ns_runtime.protocol import EnvelopeCodec
from ns_runtime.service import RuntimeService
from ns_runtime.session import (
    RuntimeConnectionRecord,
    RuntimeSessionRegistry,
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
]

__version__ = "0.2.0"
