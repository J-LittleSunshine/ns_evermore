# -*- coding: utf-8 -*-
"""Runtime Envelope protocol contracts."""

from .codec import (
    DEFAULT_JSON_LIMITS,
    JsonResourceLimits,
    JsonV1Codec,
    WIRE_CODEC_JSON_V1,
    validate_json_resources,
)
from .canonical import (
    CANONICAL_CHECKSUM_ALGORITHM,
    CANONICAL_SERIALIZATION,
    canonical_checksum,
    canonical_serialize,
)

from .inbound import (
    InboundEnvelope,
    RuntimeAuthority,
    inbound_envelope_from_mapping,
    normalize_inbound,
)
from .extensions import (
    EMPTY_EXTENSION_REGISTRY,
    ExtensionNamespaceContract,
    ExtensionNamespaceRegistry,
    ExtensionObjectSchema,
    ExtensionValidationResult,
    UnknownExtensionPolicy,
)
from .error_envelope import ErrorEnvelopeBuilder, ErrorEnvelopeContext

from .models import (
    AuthContextGroup,
    CallbackGroup,
    DeliveryGroup,
    ENVELOPE_GROUP_NAMES,
    Envelope,
    ExtensionsGroup,
    MessageGroup,
    PayloadGroup,
    ProtocolGroup,
    RouteGroup,
    SourceGroup,
    StreamGroup,
    TargetGroup,
    TraceGroup,
    envelope_from_mapping,
)
from .schema import (
    EnvelopeSchemaValidator,
    InlinePayloadSchema,
    MessageTypeSchema,
)
from .registry import (
    BUILTIN_MESSAGE_CONTRACTS,
    BUILTIN_MESSAGE_FAMILIES,
    BUILTIN_MESSAGE_REGISTRY,
    CURRENT_PROTOCOL_SCHEMA_KEY,
    MessageAuditLevel,
    MessageCategory,
    MessageReliability,
    MessageTypeContract,
    MessageTypeRegistry,
)
from .versioning import (
    JSON_V1_PROTOCOL_MATRIX,
    NegotiatedProtocol,
    ProtocolCompatibilityMatrix,
    ProtocolVersion,
    ProtocolVersionSupport,
)

__all__ = (
    "AuthContextGroup", "BUILTIN_MESSAGE_CONTRACTS", "BUILTIN_MESSAGE_FAMILIES",
    "BUILTIN_MESSAGE_REGISTRY", "CURRENT_PROTOCOL_SCHEMA_KEY", "CallbackGroup",
    "CANONICAL_CHECKSUM_ALGORITHM", "CANONICAL_SERIALIZATION", "DEFAULT_JSON_LIMITS",
    "DeliveryGroup", "ENVELOPE_GROUP_NAMES",
    "EMPTY_EXTENSION_REGISTRY", "Envelope", "EnvelopeSchemaValidator",
    "ErrorEnvelopeBuilder", "ErrorEnvelopeContext",
    "ExtensionNamespaceContract", "ExtensionNamespaceRegistry", "ExtensionObjectSchema",
    "ExtensionValidationResult", "ExtensionsGroup", "InboundEnvelope",
    "InlinePayloadSchema", "MessageGroup", "MessageTypeContract", "MessageTypeRegistry",
    "MessageAuditLevel", "MessageCategory", "MessageReliability", "MessageTypeSchema",
    "PayloadGroup", "ProtocolGroup",
    "RouteGroup", "SourceGroup", "StreamGroup", "TargetGroup", "TraceGroup",
    "JSON_V1_PROTOCOL_MATRIX", "JsonResourceLimits", "JsonV1Codec", "NegotiatedProtocol",
    "ProtocolCompatibilityMatrix", "ProtocolVersion", "ProtocolVersionSupport",
    "RuntimeAuthority", "WIRE_CODEC_JSON_V1",
    "UnknownExtensionPolicy",
    "canonical_checksum", "canonical_serialize", "envelope_from_mapping",
    "inbound_envelope_from_mapping", "normalize_inbound", "validate_json_resources",
)
