# -*- coding: utf-8 -*-
"""Runtime Envelope protocol contracts."""

from .codec import (
    DEFAULT_JSON_LIMITS,
    JsonResourceLimits,
    JsonV1Codec,
    WIRE_CODEC_JSON_V1,
)

from .inbound import (
    InboundEnvelope,
    RuntimeAuthority,
    inbound_envelope_from_mapping,
    normalize_inbound,
)

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
from .versioning import (
    JSON_V1_PROTOCOL_MATRIX,
    NegotiatedProtocol,
    ProtocolCompatibilityMatrix,
    ProtocolVersion,
    ProtocolVersionSupport,
)

__all__ = (
    "AuthContextGroup", "CallbackGroup", "DEFAULT_JSON_LIMITS", "DeliveryGroup", "ENVELOPE_GROUP_NAMES",
    "Envelope", "EnvelopeSchemaValidator", "ExtensionsGroup", "InboundEnvelope",
    "InlinePayloadSchema", "MessageGroup", "MessageTypeSchema", "PayloadGroup", "ProtocolGroup",
    "RouteGroup", "SourceGroup", "StreamGroup", "TargetGroup", "TraceGroup",
    "JSON_V1_PROTOCOL_MATRIX", "JsonResourceLimits", "JsonV1Codec", "NegotiatedProtocol",
    "ProtocolCompatibilityMatrix", "ProtocolVersion", "ProtocolVersionSupport",
    "RuntimeAuthority", "WIRE_CODEC_JSON_V1",
    "envelope_from_mapping", "inbound_envelope_from_mapping",
    "normalize_inbound",
)
