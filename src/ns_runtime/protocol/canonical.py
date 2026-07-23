# -*- coding: utf-8 -*-
"""Deterministic UTF-8 serialization for normalized runtime Envelopes."""

from __future__ import annotations

import hashlib
import json

from ns_common.exceptions import NsRuntimeEnvelopeSchemaError

from .codec import DEFAULT_JSON_LIMITS, JsonResourceLimits, validate_json_resources
from .models import Envelope


CANONICAL_SERIALIZATION = "json.v1.canonical"
CANONICAL_CHECKSUM_ALGORITHM = "sha256"


def canonical_serialize(
    envelope: Envelope,
    *,
    limits: JsonResourceLimits = DEFAULT_JSON_LIMITS,
) -> bytes:
    """Return strict, compact JSON bytes with recursively sorted object keys."""

    if not isinstance(envelope, Envelope):
        raise TypeError("envelope must be Envelope")
    value = envelope.to_dict()
    validate_json_resources(value, limits=limits)
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8", errors="strict")
    except (TypeError, ValueError, UnicodeEncodeError):
        raise NsRuntimeEnvelopeSchemaError(
            "Runtime Envelope cannot be canonically serialized.",
            details={
                "group": "envelope",
                "field": "$document",
                "reason": "canonical_serialization_failed",
            },
        ) from None
    if len(encoded) > limits.max_document_bytes:
        raise NsRuntimeEnvelopeSchemaError(
            "Runtime canonical Envelope exceeds its resource limit.",
            details={
                "group": "envelope",
                "field": "$document",
                "reason": "max_document_bytes_exceeded",
            },
        )
    return encoded


def canonical_checksum(
    envelope: Envelope,
    *,
    limits: JsonResourceLimits = DEFAULT_JSON_LIMITS,
) -> str:
    """Return the stable full-envelope checksum without exposing its bytes."""

    digest = hashlib.sha256(canonical_serialize(envelope, limits=limits)).hexdigest()
    return f"{CANONICAL_CHECKSUM_ALGORITHM}:{digest}"


__all__ = (
    "CANONICAL_CHECKSUM_ALGORITHM",
    "CANONICAL_SERIALIZATION",
    "canonical_checksum",
    "canonical_serialize",
)
