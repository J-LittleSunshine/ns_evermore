# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

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
    "BaseRuntimeProcessor",
    "ProcessorPipeline",
    "ProcessorRegistry",
    "build_default_processor_pipeline",
    "build_default_processor_registry",
    "RuntimeService",
]

__version__ = "0.1.0"