# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from ns_common.exceptions import NsRuntimeProtocolError
from ns_runtime.protocol.constants import (
    RUNTIME_PROTOCOL_VERSION,
    SUPPORTED_BACKPRESSURE_POLICIES,
    SUPPORTED_CLIENT_TYPES,
    SUPPORTED_DELIVERY_MODES,
    SUPPORTED_MESSAGE_TYPES,
    SUPPORTED_REPLY_MODES,
    SUPPORTED_TARGET_TYPES,
)
from ns_runtime.protocol.envelope import (
    RuntimeAttachment,
    RuntimeEnvelope,
    RuntimeRouteContext,
)


def validate_envelope(envelope: RuntimeEnvelope, *, max_message_size_bytes: int | None = None) -> None:
    if not isinstance(envelope, RuntimeEnvelope):
        raise NsRuntimeProtocolError(
            "runtime envelope must be RuntimeEnvelope.",
            details={
                "actual_type": type(envelope).__name__,
            },
        )

    _validate_non_empty_string("protocol_version", envelope.protocol_version)
    if envelope.protocol_version != RUNTIME_PROTOCOL_VERSION:
        raise NsRuntimeProtocolError(
            "Unsupported runtime protocol_version.",
            details={
                "field": "protocol_version",
                "value": envelope.protocol_version,
                "supported": RUNTIME_PROTOCOL_VERSION,
            },
        )

    _validate_non_empty_string("message_id", envelope.message_id)

    if envelope.correlation_id is not None:
        _validate_non_empty_string("correlation_id", envelope.correlation_id)

    _validate_choice("message_type", envelope.message_type, SUPPORTED_MESSAGE_TYPES)
    _validate_choice("client_type", envelope.client_type, SUPPORTED_CLIENT_TYPES)
    _validate_choice("target_type", envelope.target_type, SUPPORTED_TARGET_TYPES)
    _validate_choice("reply_mode", envelope.reply_mode, SUPPORTED_REPLY_MODES)
    _validate_choice("delivery_mode", envelope.delivery_mode, SUPPORTED_DELIVERY_MODES)
    _validate_choice("backpressure_policy", envelope.backpressure_policy, SUPPORTED_BACKPRESSURE_POLICIES)

    if envelope.action is not None:
        _validate_non_empty_string("action", envelope.action)

    _validate_positive_int("priority", envelope.priority)
    _validate_positive_int("timeout_ms", envelope.timeout_ms)

    if envelope.queue_timeout_ms is not None:
        _validate_positive_int("queue_timeout_ms", envelope.queue_timeout_ms)

    _validate_non_empty_string("codec", envelope.codec)

    if not isinstance(envelope.metadata, dict):
        raise NsRuntimeProtocolError(
            "metadata must be a dict.",
            details={
                "field": "metadata",
                "actual_type": type(envelope.metadata).__name__,
            },
        )

    _validate_route_context(envelope.route_context)
    _validate_attachments(envelope.attachments)

    if max_message_size_bytes is not None:
        _validate_positive_int("max_message_size_bytes", max_message_size_bytes)


def _validate_route_context(route_context: RuntimeRouteContext) -> None:
    if not isinstance(route_context, RuntimeRouteContext):
        raise NsRuntimeProtocolError(
            "route_context must be RuntimeRouteContext.",
            details={
                "field": "route_context",
                "actual_type": type(route_context).__name__,
            },
        )

    _validate_non_negative_int("route_context.hop_count", route_context.hop_count)
    _validate_positive_int("route_context.max_hops", route_context.max_hops)

    if route_context.hop_count > route_context.max_hops:
        raise NsRuntimeProtocolError(
            "runtime routing loop detected.",
            code="RUNTIME_ROUTING_LOOP_DETECTED",
            numeric_code=203010,
            details={
                "hop_count": route_context.hop_count,
                "max_hops": route_context.max_hops,
                "route_trace": route_context.route_trace,
            },
        )

    if not isinstance(route_context.route_trace, list):
        raise NsRuntimeProtocolError(
            "route_context.route_trace must be a list.",
            details={
                "field": "route_context.route_trace",
                "actual_type": type(route_context.route_trace).__name__,
            },
        )


def _validate_attachments(attachments: list[RuntimeAttachment]) -> None:
    if not isinstance(attachments, list):
        raise NsRuntimeProtocolError(
            "attachments must be a list.",
            details={
                "field": "attachments",
                "actual_type": type(attachments).__name__,
            },
        )

    for index, attachment in enumerate(attachments):
        if not isinstance(attachment, RuntimeAttachment):
            raise NsRuntimeProtocolError(
                "attachment item must be RuntimeAttachment.",
                details={
                    "field": f"attachments[{index}]",
                    "actual_type": type(attachment).__name__,
                },
            )

        _validate_non_empty_string(f"attachments[{index}].type", attachment.type)

        if attachment.size_bytes is not None:
            _validate_non_negative_int(f"attachments[{index}].size_bytes", attachment.size_bytes)

        if not isinstance(attachment.metadata, dict):
            raise NsRuntimeProtocolError(
                "attachment.metadata must be a dict.",
                details={
                    "field": f"attachments[{index}].metadata",
                    "actual_type": type(attachment.metadata).__name__,
                },
            )


def _validate_choice(field_name: str, value: Any, allowed_values: set[str]) -> None:
    if value not in allowed_values:
        raise NsRuntimeProtocolError(
            f"{field_name} is invalid.",
            details={
                "field": field_name,
                "value": value,
                "allowed_values": sorted(allowed_values),
            },
        )


def _validate_non_empty_string(field_name: str, value: Any) -> None:
    if not isinstance(value, str) or not value.strip():
        raise NsRuntimeProtocolError(
            f"{field_name} must be a non-empty string.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )


def _validate_positive_int(field_name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise NsRuntimeProtocolError(
            f"{field_name} must be a positive integer.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )


def _validate_non_negative_int(field_name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise NsRuntimeProtocolError(
            f"{field_name} must be a non-negative integer.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )
