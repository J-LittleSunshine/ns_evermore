# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import uuid
from dataclasses import (
    dataclass,
    field
)
from typing import (
    Any,
    Mapping,
    TYPE_CHECKING
)

from ns_common.exceptions import (
    NsEvermoreError,
    NsRuntimeAuthContextForgedError,
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeProtocolVersionError,
    NsRuntimeSourceForgedError,
)
from ns_runtime.models import (
    Envelope,
    MessageReliability,
    RuntimeSessionContext,
    utc_now_iso,
)

if TYPE_CHECKING:
    pass

_ALLOWED_TOP_LEVEL_GROUPS: frozenset[str] = frozenset(
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

_ALLOWED_GROUP_FIELDS: dict[str, frozenset[str]] = {
    "protocol": frozenset({"version", "min_version", "supported_versions"}),
    "message": frozenset({"message_id", "type", "category", "priority", "created_at", "expires_at", "reliability"}),
    "target": frozenset({"kind", "connection_id", "identity", "tenant_id", "capabilities", "component_type", "runtime_id", "strategy", "filters"}),
    "route": frozenset({"root_runtime_id", "current_runtime_id", "previous_runtime_id", "next_runtime_id", "segment", "routing_plan_id", "hop", "max_hops"}),
    "delivery": frozenset({"delivery_id", "summary_id", "root_delivery_id", "parent_delivery_id", "attempt", "ack_timeout_ms", "replay_epoch"}),
    "stream": frozenset({"stream_id", "sequence", "ack_sequence", "ack_ranges", "missing_sequences", "received_sequences", "end_reason"}),
    "payload": frozenset({"mode", "inline", "payload_ref", "checksum", "content_type", "size_bytes"}),
    "callback": frozenset({"mode", "target", "payload_ref", "url", "message_type"}),
    "trace": frozenset({"trace_id", "span_id", "parent_span_id", "correlation_id", "request_id"}),
    "extensions": frozenset(),
}

_REQUIRED_MESSAGE_FIELDS: frozenset[str] = frozenset(
    {
        "message_id",
        "type",
        "category",
        "priority",
        "created_at",
        "reliability",
    }
)

_RELIABILITY_VALUES: frozenset[str] = frozenset(
    {
        "best_effort",
        "reliable",
        "critical",
    }
)


@dataclass(slots=True, kw_only=True)
class ProtocolCompatibilityPolicy:
    supported_major: int = 1
    supported_minor: int = 0
    supported_patch: int = 0
    max_frame_bytes: int = 1024 * 1024
    allow_minor_downgrade: bool = True
    allowed_extension_namespaces: tuple[str, ...] = field(default_factory=tuple)


class EnvelopeCodec:
    def __init__(self, *, runtime_id: str, policy: ProtocolCompatibilityPolicy | None = None) -> None:
        self._runtime_id = runtime_id
        self._policy = policy or ProtocolCompatibilityPolicy()

    def parse_inbound(self, frame_text: str, session: RuntimeSessionContext) -> Envelope:
        self._validate_frame_text(frame_text)

        try:
            raw = json.loads(frame_text)
        except json.JSONDecodeError as exc:
            raise NsRuntimeEnvelopeSchemaError("Inbound frame must be a valid JSON object.", details={"reason": str(exc)}) from exc

        if not isinstance(raw, dict):
            raise NsRuntimeEnvelopeSchemaError("Inbound envelope must be a JSON object.", details={"actual_type": type(raw).__name__})

        self._validate_top_level_groups(raw)
        self._reject_forged_context(raw)
        self._validate_group_fields(raw)
        version = self._validate_protocol(raw)
        message_id, message_type, category, reliability = self._validate_message(raw)
        self._validate_target(raw)
        self._validate_delivery(raw)
        self._validate_extensions(raw)
        normalized_raw = self.inject_runtime_context(raw, session)

        return Envelope(
            raw=normalized_raw,
            protocol_version=version,
            message_id=message_id,
            message_type=message_type,
            category=category,
            reliability=reliability,
        )

    def parse_connection_hello(self, frame_text: str) -> dict[str, Any]:
        self._validate_frame_text(frame_text)

        try:
            raw = json.loads(frame_text)
        except json.JSONDecodeError as exc:
            raise NsRuntimeEnvelopeSchemaError("connection.hello frame must be a valid JSON object.", details={"reason": str(exc)}) from exc

        if not isinstance(raw, dict):
            raise NsRuntimeEnvelopeSchemaError("connection.hello envelope must be a JSON object.", details={"actual_type": type(raw).__name__})

        self._validate_top_level_groups(raw)
        self._reject_forged_context(raw)
        self._validate_group_fields(raw)
        self._validate_protocol(raw)
        _message_id, message_type, category, _reliability = self._validate_message(raw)
        self._validate_extensions(raw)

        if message_type != "connection.hello":
            raise NsRuntimeEnvelopeSchemaError(
                "First WebSocket runtime envelope must be connection.hello.",
                details={
                    "actual_message_type": message_type,
                },
            )

        if category != "connection":
            raise NsRuntimeEnvelopeSchemaError(
                "connection.hello must use message.category=connection.",
                details={
                    "actual_category": category,
                },
            )

        forbidden_groups = sorted(set(raw.keys()) & {"target", "route", "delivery", "stream", "callback"})
        if forbidden_groups:
            raise NsRuntimeEnvelopeSchemaError(
                "connection.hello contains groups that are not allowed during handshake.",
                details={
                    "forbidden_groups": forbidden_groups,
                },
            )

        return dict(raw)

    def inject_runtime_context(self, raw: Mapping[str, Any], session: RuntimeSessionContext) -> dict[str, Any]:
        normalized = dict(raw)
        normalized["source"] = session.build_source_context().to_group()
        normalized["auth_context"] = session.build_auth_context().to_group()
        return normalized

    def build_error_envelope(self, exc: Exception, *, session: RuntimeSessionContext | None = None, request: Envelope | None = None, close_reason: str | None = None) -> dict[str, Any]:
        error = self._normalize_error(exc)
        message_id = str(uuid.uuid4())
        target: dict[str, Any] | None = None

        if session is not None:
            target = {
                "kind": "connection",
                "connection_id": session.connection_id,
            }

        envelope: dict[str, Any] = {
            "protocol": {
                "version": self.protocol_version_text,
            },
            "message": {
                "message_id": message_id,
                "type": "runtime.error",
                "category": "control",
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "best_effort",
            },
            "source": {
                "runtime_id": self._runtime_id,
                "connection_id": "runtime",
                "session_id": "runtime",
                "identity": self._runtime_id,
                "tenant_id": session.tenant_id if session else "system",
                "component_type": "runtime",
                "capabilities_summary": [
                    "runtime.error"
                ],
                "connection_epoch": 0,
            },
            "payload": {
                "mode": "inline",
                "inline": {
                    "error": error,
                    "request_message_id": request.message_id if request else None,
                    "request_message_type": request.message_type if request else None,
                    "close_reason": close_reason,
                },
            },
            "trace": {
                "trace_id": str(uuid.uuid4()),
                "request_id": request.message_id if request else message_id,
            },
        }

        if target is not None:
            envelope["target"] = target

        return envelope

    @property
    def protocol_version_text(self) -> str:
        return f"{self._policy.supported_major}.{self._policy.supported_minor}.{self._policy.supported_patch}"

    def _validate_frame_text(self, frame_text: str) -> None:
        if not isinstance(frame_text, str):
            raise NsRuntimeEnvelopeSchemaError("WebSocket runtime protocol only accepts JSON text frames.")

        if len(frame_text.encode("utf-8")) > self._policy.max_frame_bytes:
            raise NsRuntimeEnvelopeSchemaError(
                "Inbound envelope frame is too large.",
                details={
                    "max_frame_bytes": self._policy.max_frame_bytes,
                },
            )

    def _validate_top_level_groups(self, raw: Mapping[str, Any]) -> None:
        unknown_groups = sorted(set(raw.keys()) - _ALLOWED_TOP_LEVEL_GROUPS)
        if unknown_groups:
            raise NsRuntimeEnvelopeSchemaError("Inbound envelope contains unknown top-level group.", details={"unknown_groups": unknown_groups})

        if "protocol" not in raw or "message" not in raw:
            raise NsRuntimeEnvelopeSchemaError("Inbound envelope must contain protocol and message groups.")

        for group_name, value in raw.items():
            if value is None:
                raise NsRuntimeEnvelopeSchemaError("Envelope group must be omitted instead of null.", details={"group": group_name})
            if isinstance(value, dict) and not value:
                raise NsRuntimeEnvelopeSchemaError("Envelope group must be omitted instead of empty object.", details={"group": group_name})

    def _reject_forged_context(self, raw: Mapping[str, Any]) -> None:
        if "source" in raw:
            raise NsRuntimeSourceForgedError()

        if "auth_context" in raw:
            raise NsRuntimeAuthContextForgedError()

    def _validate_group_fields(self, raw: Mapping[str, Any]) -> None:
        for group_name, value in raw.items():
            if group_name in {"source", "auth_context"}:
                continue

            if not isinstance(value, dict):
                raise NsRuntimeEnvelopeSchemaError("Envelope group must be an object.", details={"group": group_name, "actual_type": type(value).__name__})

            allowed_fields = _ALLOWED_GROUP_FIELDS.get(group_name)
            if allowed_fields is None:
                continue

            if group_name == "extensions":
                continue

            unknown_fields = sorted(set(value.keys()) - allowed_fields)
            if unknown_fields:
                raise NsRuntimeEnvelopeSchemaError("Envelope group contains unknown field.", details={"group": group_name, "unknown_fields": unknown_fields})

    def _validate_protocol(self, raw: Mapping[str, Any]) -> tuple[int, int, int]:
        protocol = raw["protocol"]
        version = protocol.get("version")
        parsed = self._parse_version(version)

        if parsed[0] != self._policy.supported_major:
            raise NsRuntimeProtocolVersionError(
                "Runtime protocol major version is incompatible.",
                details={
                    "client_version": version,
                    "runtime_version": self.protocol_version_text,
                },
            )

        if not self._policy.allow_minor_downgrade and parsed[1:] != (self._policy.supported_minor, self._policy.supported_patch):
            raise NsRuntimeProtocolVersionError(
                "Runtime protocol minor or patch version is incompatible.",
                details={
                    "client_version": version,
                    "runtime_version": self.protocol_version_text,
                },
            )

        return parsed

    def _validate_message(self, raw: Mapping[str, Any]) -> tuple[str, str, str, MessageReliability]:
        message = raw["message"]
        missing_fields = sorted(_REQUIRED_MESSAGE_FIELDS - set(message.keys()))
        if missing_fields:
            raise NsRuntimeEnvelopeSchemaError("Envelope message group misses required fields.", details={"missing_fields": missing_fields})

        message_id = self._require_non_empty_str(message, "message_id", "message")
        message_type = self._require_non_empty_str(message, "type", "message")
        category = self._require_non_empty_str(message, "category", "message")
        reliability_raw = self._require_non_empty_str(message, "reliability", "message")

        if "." not in message_type:
            raise NsRuntimeEnvelopeSchemaError("message.type must use dotted naming style.", details={"message_type": message_type})

        if reliability_raw not in _RELIABILITY_VALUES:
            raise NsRuntimeEnvelopeSchemaError("message.reliability is invalid.", details={"value": reliability_raw, "allowed_values": sorted(_RELIABILITY_VALUES)})

        return message_id, message_type, category, reliability_raw  # type: ignore[return-value]

    def _validate_target(self, raw: Mapping[str, Any]) -> None:
        target = raw.get("target")
        if target is None:
            return

        kind = self._require_non_empty_str(target, "kind", "target")

        required_by_kind: dict[str, str] = {
            "connection": "connection_id",
            "identity": "identity",
            "capability": "capabilities",
            "component_type": "component_type",
            "runtime": "runtime_id",
            "tenant": "tenant_id",
            "broadcast": "tenant_id",
        }

        required_field = required_by_kind.get(kind)
        if required_field is None:
            raise NsRuntimeEnvelopeSchemaError("target.kind is invalid.", details={"kind": kind})

        if required_field not in target:
            raise NsRuntimeEnvelopeSchemaError("target misses required field for kind.", details={"kind": kind, "required_field": required_field})

    def _validate_delivery(self, raw: Mapping[str, Any]) -> None:
        delivery = raw.get("delivery")
        if delivery is None:
            return

        if "message_id" in delivery:
            raise NsRuntimeEnvelopeSchemaError("delivery.message_id is forbidden; use message.message_id only.")

    def _validate_extensions(self, raw: Mapping[str, Any]) -> None:
        extensions = raw.get("extensions")
        if extensions is None:
            return

        if not isinstance(extensions, dict):
            raise NsRuntimeEnvelopeSchemaError("extensions group must be an object.")

        allowed_namespaces = set(self._policy.allowed_extension_namespaces)
        for namespace in extensions.keys():
            if not isinstance(namespace, str) or not namespace.strip():
                raise NsRuntimeEnvelopeSchemaError("extension namespace must be a non-empty string.")
            if namespace not in allowed_namespaces:
                raise NsRuntimeEnvelopeSchemaError(
                    "Extension namespace is not registered or allowed by current runtime policy.",
                    details={
                        "namespace": namespace,
                        "allowed_namespaces": sorted(allowed_namespaces),
                    },
                )

    @staticmethod
    def _parse_version(value: Any) -> tuple[int, int, int]:
        if isinstance(value, str):
            parts = value.split(".")
            if len(parts) != 3:
                raise NsRuntimeProtocolVersionError("protocol.version must use major.minor.patch format.")
            try:
                return int(parts[0]), int(parts[1]), int(parts[2])
            except ValueError as exc:
                raise NsRuntimeProtocolVersionError("protocol.version contains non-integer segment.") from exc

        if isinstance(value, dict):
            try:
                return int(value["major"]), int(value["minor"]), int(value["patch"])
            except (KeyError, TypeError, ValueError) as exc:
                raise NsRuntimeProtocolVersionError("protocol.version object must contain integer major/minor/patch.") from exc

        raise NsRuntimeProtocolVersionError("protocol.version is required.")

    @staticmethod
    def _require_non_empty_str(group: Mapping[str, Any], field_name: str, group_name: str) -> str:
        value = group.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise NsRuntimeEnvelopeSchemaError(
                "Envelope field must be a non-empty string.",
                details={
                    "group": group_name,
                    "field": field_name,
                    "actual_type": type(value).__name__,
                },
            )
        return value.strip()

    @staticmethod
    def _normalize_error(exc: Exception) -> dict[str, Any]:
        if isinstance(exc, NsEvermoreError):
            return exc.to_dict()

        return {
            "code": "RUNTIME_INTERNAL_ERROR",
            "numeric_code": 200500,
            "message": str(exc) or exc.__class__.__name__,
            "details": {
                "exception_class": exc.__class__.__name__,
            },
        }
