# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Final

RUNTIME_PROTOCOL_MAJOR: Final[int] = 1
RUNTIME_PROTOCOL_MINOR: Final[int] = 0
RUNTIME_PROTOCOL_PATCH: Final[int] = 0

ENVELOPE_CORE_GROUPS: Final[frozenset[str]] = frozenset(
    {
        "protocol",
        "message",
        "source",
        "target",
        "route",
        "delivery",
        "stream",
        "auth_context",
        "payload",
        "callback",
        "trace",
        "extensions",
    }
)

INBOUND_FORBIDDEN_GROUPS: Final[frozenset[str]] = frozenset(
    {
        "source",
        "auth_context",
    }
)

PROTOCOL_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "major",
        "minor",
        "patch",
        "version",
        "min_version",
        "supported_versions",
    }
)

MESSAGE_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "message_id",
        "type",
        "category",
        "priority",
        "created_at",
        "expires_at",
        "reliability",
    }
)

SOURCE_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "runtime_id",
        "connection_id",
        "identity",
        "identity_digest",
        "tenant_id",
        "component_type",
        "capabilities_digest",
    }
)

TARGET_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "kind",
        "connection_id",
        "identity",
        "tenant_id",
        "capabilities",
        "component_type",
        "runtime_id",
        "broadcast_scope",
        "filters",
        "strategy",
    }
)

ROUTE_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "root_runtime_id",
        "current_runtime_id",
        "previous_runtime_id",
        "next_runtime_id",
        "segment_id",
        "routing_plan_id",
        "hop",
        "max_hops",
        "segments",
    }
)

DELIVERY_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "delivery_id",
        "summary_id",
        "root_delivery_id",
        "parent_delivery_id",
        "attempt",
        "ack_timeout_ms",
        "replay_epoch",
    }
)

STREAM_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "stream_id",
        "sequence",
        "ack_sequence",
        "ack_ranges",
        "missing_sequences",
        "received_sequences",
        "end_reason",
    }
)

AUTH_CONTEXT_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "snapshot_ref",
        "capabilities_digest",
        "iam_mode",
        "issued_at",
        "expires_at",
        "permission_version",
    }
)

PAYLOAD_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "mode",
        "inline",
        "payload_ref",
        "size",
        "checksum",
        "content_type",
        "version",
        "summary",
    }
)

CALLBACK_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "mode",
        "target",
        "payload",
        "payload_ref",
        "timeout_ms",
        "retry_policy",
    }
)

TRACE_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "trace_id",
        "span_id",
        "parent_span_id",
        "correlation_id",
        "request_id",
    }
)

EXTENSIONS_FIELDS: Final[frozenset[str]] = frozenset()

ENVELOPE_GROUP_FIELDS: Final[dict[str, frozenset[str]]] = {
    "protocol": PROTOCOL_FIELDS,
    "message": MESSAGE_FIELDS,
    "source": SOURCE_FIELDS,
    "target": TARGET_FIELDS,
    "route": ROUTE_FIELDS,
    "delivery": DELIVERY_FIELDS,
    "stream": STREAM_FIELDS,
    "auth_context": AUTH_CONTEXT_FIELDS,
    "payload": PAYLOAD_FIELDS,
    "callback": CALLBACK_FIELDS,
    "trace": TRACE_FIELDS,
    "extensions": EXTENSIONS_FIELDS,
}
