# -*- coding: utf-8 -*-
"""Resource-bounded UTF-8 ``json.v1`` decoding."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any

from ns_common.exceptions import (
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeProtocolParseError,
)

from .inbound import InboundEnvelope, inbound_envelope_from_mapping


WIRE_CODEC_JSON_V1 = "json.v1"


def _limit_error(reason: str) -> NsRuntimeEnvelopeSchemaError:
    return NsRuntimeEnvelopeSchemaError(
        "Runtime JSON resource limit exceeded.",
        details={
            "group": "envelope",
            "field": "$document",
            "reason": reason,
        },
    )


def _parse_error(reason: str) -> NsRuntimeProtocolParseError:
    return NsRuntimeProtocolParseError(
        details={"codec": WIRE_CODEC_JSON_V1, "reason": reason},
    )


@dataclass(frozen=True, slots=True)
class JsonResourceLimits:
    max_document_bytes: int = 1_048_576
    max_depth: int = 32
    max_string_chars: int = 65_536
    max_array_items: int = 4_096
    max_object_items: int = 4_096
    max_nodes: int = 100_000
    max_integer_abs: int = 9_223_372_036_854_775_807
    max_float_abs: float = 1.0e308

    def __post_init__(self) -> None:
        for name in (
            "max_document_bytes", "max_depth", "max_string_chars",
            "max_array_items", "max_object_items", "max_nodes",
            "max_integer_abs",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if (
            isinstance(self.max_float_abs, bool)
            or not isinstance(self.max_float_abs, (int, float))
            or not math.isfinite(float(self.max_float_abs))
            or self.max_float_abs <= 0
        ):
            raise ValueError("max_float_abs must be a positive finite number")


DEFAULT_JSON_LIMITS = JsonResourceLimits()


class JsonV1Codec:
    """Decode exactly one JSON document under fixed structural budgets."""

    name = WIRE_CODEC_JSON_V1

    def __init__(self, *, limits: JsonResourceLimits = DEFAULT_JSON_LIMITS) -> None:
        if not isinstance(limits, JsonResourceLimits):
            raise TypeError("limits must be JsonResourceLimits")
        self._limits = limits

    @property
    def limits(self) -> JsonResourceLimits:
        return self._limits

    def decode_document(self, raw: str | bytes) -> Any:
        text = self._decode_text(raw)
        _scan_depth(text, self._limits.max_depth)
        try:
            value = json.loads(
                text,
                object_pairs_hook=_strict_object_pairs,
                parse_int=lambda raw_number: _parse_integer(
                    raw_number,
                    self._limits.max_integer_abs,
                ),
                parse_float=lambda raw_number: _parse_float(
                    raw_number,
                    self._limits.max_float_abs,
                ),
                parse_constant=lambda _value: (_ for _ in ()).throw(
                    _parse_error("non_finite_number")
                ),
            )
        except NsRuntimeProtocolParseError:
            raise
        except _DuplicateKeyError:
            raise _parse_error("duplicate_object_key") from None
        except (json.JSONDecodeError, RecursionError, ValueError, TypeError):
            raise _parse_error("invalid_json_document") from None
        _validate_resources(value, limits=self._limits)
        return value

    def decode_inbound(self, raw: str | bytes) -> InboundEnvelope:
        return inbound_envelope_from_mapping(self.decode_document(raw))

    def _decode_text(self, raw: str | bytes) -> str:
        if isinstance(raw, bytes):
            if len(raw) > self._limits.max_document_bytes:
                raise _limit_error("max_document_bytes_exceeded")
            try:
                text = raw.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                raise _parse_error("invalid_utf8") from None
        elif isinstance(raw, str):
            if len(raw) > self._limits.max_document_bytes:
                raise _limit_error("max_document_bytes_exceeded")
            try:
                encoded_length = len(raw.encode("utf-8", errors="strict"))
            except UnicodeEncodeError:
                raise _parse_error("invalid_unicode") from None
            if encoded_length > self._limits.max_document_bytes:
                raise _limit_error("max_document_bytes_exceeded")
            text = raw
        else:
            raise _parse_error("text_or_bytes_required")
        return text


class _DuplicateKeyError(ValueError):
    pass


def _strict_object_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError
        result[key] = value
    return result


def _parse_integer(raw_number: str, maximum: int) -> int:
    unsigned = raw_number.removeprefix("-")
    maximum_digits = len(str(maximum))
    if len(unsigned) > maximum_digits:
        raise _limit_error("integer_range_exceeded")
    value = int(raw_number)
    if abs(value) > maximum:
        raise _limit_error("integer_range_exceeded")
    return value


def _parse_float(raw_number: str, maximum: float) -> float:
    value = float(raw_number)
    if not math.isfinite(value) or abs(value) > maximum:
        raise _limit_error("float_range_exceeded")
    return value


def _scan_depth(text: str, max_depth: int) -> None:
    depth = 0
    in_string = False
    escaped = False
    for character in text:
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            continue
        if character == '"':
            in_string = True
        elif character in "[{":
            depth += 1
            if depth > max_depth:
                raise _limit_error("max_depth_exceeded")
        elif character in "]}":
            depth -= 1


def _validate_resources(value: Any, *, limits: JsonResourceLimits) -> None:
    nodes = 0
    stack: list[tuple[Any, int]] = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        nodes += 1
        if nodes > limits.max_nodes:
            raise _limit_error("max_nodes_exceeded")
        if isinstance(current, str):
            if len(current) > limits.max_string_chars:
                raise _limit_error("max_string_chars_exceeded")
        elif current is None or isinstance(current, bool):
            continue
        elif isinstance(current, int):
            if abs(current) > limits.max_integer_abs:
                raise _limit_error("integer_range_exceeded")
        elif isinstance(current, float):
            if not math.isfinite(current) or abs(current) > limits.max_float_abs:
                raise _limit_error("float_range_exceeded")
        elif isinstance(current, list):
            container_depth = depth + 1
            if container_depth > limits.max_depth:
                raise _limit_error("max_depth_exceeded")
            if len(current) > limits.max_array_items:
                raise _limit_error("max_array_items_exceeded")
            stack.extend((item, container_depth) for item in current)
        elif isinstance(current, dict):
            container_depth = depth + 1
            if container_depth > limits.max_depth:
                raise _limit_error("max_depth_exceeded")
            if len(current) > limits.max_object_items:
                raise _limit_error("max_object_items_exceeded")
            for key, item in current.items():
                if len(key) > limits.max_string_chars:
                    raise _limit_error("max_string_chars_exceeded")
                stack.append((item, container_depth))
        else:
            raise _parse_error("unsupported_json_value")


def validate_json_resources(
    value: Any,
    *,
    limits: JsonResourceLimits = DEFAULT_JSON_LIMITS,
) -> None:
    """Apply the same structural limits to an already-normalized JSON value."""

    if not isinstance(limits, JsonResourceLimits):
        raise TypeError("limits must be JsonResourceLimits")
    _validate_resources(value, limits=limits)


__all__ = (
    "DEFAULT_JSON_LIMITS",
    "JsonResourceLimits",
    "JsonV1Codec",
    "WIRE_CODEC_JSON_V1",
    "validate_json_resources",
)
