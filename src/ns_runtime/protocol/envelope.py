# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import (
    Any,
    Mapping,
)
from uuid import uuid4

from ns_common.exceptions import (
    NsEvermoreError,
    NsRuntimeAuthContextForgedError,
    NsRuntimeEnvelopeSchemaError,
    NsRuntimeProtocolVersionError,
    NsRuntimeSourceForgedError,
)
from ns_runtime._compat import UTC
from ns_runtime.processor.registry import (
    ProcessorRegistration,
    ProcessorRegistry,
)
from ns_runtime.protocol.constants import (
    ENVELOPE_CORE_GROUPS,
    ENVELOPE_GROUP_FIELDS,
    RUNTIME_PROTOCOL_MAJOR,
    RUNTIME_PROTOCOL_MINOR,
    RUNTIME_PROTOCOL_PATCH,
)


@dataclass(frozen=True, slots=True)
class RuntimeProtocolVersion:
    major: int
    minor: int
    patch: int = 0

    @classmethod
    def current(cls) -> "RuntimeProtocolVersion":
        return cls(
            major=RUNTIME_PROTOCOL_MAJOR,
            minor=RUNTIME_PROTOCOL_MINOR,
            patch=RUNTIME_PROTOCOL_PATCH,
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "RuntimeProtocolVersion":
        if "version" in value and isinstance(value["version"], str):
            parts = value["version"].split(".")

            if len(parts) not in {
                2,
                3,
            }:
                raise NsRuntimeProtocolVersionError(
                    details={
                        "version": value["version"],
                    },
                )

            numbers: list[int] = [
                int(part)
                for part in parts
            ]

            if len(numbers) == 2:
                numbers.append(0)

            return cls(
                major=numbers[0],
                minor=numbers[1],
                patch=numbers[2],
            )

        return cls(
            major=int(value.get("major", 0)),
            minor=int(value.get("minor", 0)),
            patch=int(value.get("patch", 0)),
        )

    def as_dict(self) -> dict[str, int]:
        return {
            "major": self.major,
            "minor": self.minor,
            "patch": self.patch,
        }


@dataclass(frozen=True, slots=True)
class ProtocolCompatibilityResult:
    accepted: bool
    negotiated_version: RuntimeProtocolVersion
    reason: str = ""


class ProtocolCompatibilityPolicy:
    def __init__(self, runtime_version: RuntimeProtocolVersion | None = None) -> None:
        self.runtime_version: RuntimeProtocolVersion = runtime_version or RuntimeProtocolVersion.current()

    def negotiate(self, client_version: RuntimeProtocolVersion) -> ProtocolCompatibilityResult:
        if client_version.major != self.runtime_version.major:
            return ProtocolCompatibilityResult(
                accepted=False,
                negotiated_version=self.runtime_version,
                reason="major_version_mismatch",
            )

        negotiated_minor = min(
            client_version.minor,
            self.runtime_version.minor,
        )

        return ProtocolCompatibilityResult(
            accepted=True,
            negotiated_version=RuntimeProtocolVersion(
                major=self.runtime_version.major,
                minor=negotiated_minor,
                patch=0,
            ),
        )


@dataclass(frozen=True, slots=True)
class RuntimeEnvelope:
    raw: dict[str, Any]
    message_type: str
    message_id: str
    registration: ProcessorRegistration
    protocol_version: RuntimeProtocolVersion


class EnvelopeProtocol:
    def __init__(self, registry: ProcessorRegistry, compatibility_policy: ProtocolCompatibilityPolicy | None = None) -> None:
        self.registry: ProcessorRegistry = registry
        self.compatibility_policy: ProtocolCompatibilityPolicy = compatibility_policy or ProtocolCompatibilityPolicy()

    def decode_inbound_text_frame(self, frame_text: str) -> RuntimeEnvelope:
        try:
            raw = json.loads(frame_text)
        except json.JSONDecodeError as error:
            raise NsRuntimeEnvelopeSchemaError(
                "Inbound WebSocket text frame is not valid JSON.",
                details={
                    "line": error.lineno,
                    "column": error.colno,
                },
            ) from error

        if not isinstance(raw, dict):
            raise NsRuntimeEnvelopeSchemaError(
                "Inbound envelope root must be a JSON object.",
                details={
                    "actual_type": type(raw).__name__,
                },
            )

        return self.validate_inbound(raw)

    def validate_inbound(self, raw: Mapping[str, Any]) -> RuntimeEnvelope:
        normalized: dict[str, Any] = dict(raw)

        self._validate_top_level_groups(normalized)
        self._validate_inbound_forbidden_groups(normalized)

        protocol_version = self._resolve_protocol_version(normalized)
        compatibility = self.compatibility_policy.negotiate(protocol_version)

        if not compatibility.accepted:
            raise NsRuntimeProtocolVersionError(
                details={
                    "reason": compatibility.reason,
                    "client_version": protocol_version.as_dict(),
                    "runtime_version": self.compatibility_policy.runtime_version.as_dict(),
                },
            )

        message = self._require_group(normalized, "message")
        message_type = self._require_string(message, "type")
        message_id = self._require_string(message, "message_id")
        registration = self.registry.get(message_type)

        self._validate_message_type_schema(normalized, registration)

        return RuntimeEnvelope(
            raw=normalized,
            message_type=message_type,
            message_id=message_id,
            registration=registration,
            protocol_version=compatibility.negotiated_version,
        )

    def build_error_envelope(self, error: NsEvermoreError, *, request_id: str | None = None, trace: Mapping[str, Any] | None = None) -> dict[str, Any]:
        envelope: dict[str, Any] = {
            "protocol": self.compatibility_policy.runtime_version.as_dict(),
            "message": {
                "message_id": f"err-{uuid4().hex}",
                "type": "runtime.error",
                "category": "error",
                "priority": 0,
                "created_at": datetime.now(UTC).isoformat(),
                "reliability": "best_effort",
            },
            "payload": {
                "mode": "inline",
                "inline": error.to_dict(),
            },
        }

        if request_id:
            envelope["trace"] = {
                "request_id": request_id,
            }

        if trace:
            envelope["trace"] = {
                **dict(trace),
                **dict(envelope.get("trace", {})),
            }

        return envelope

    def _validate_top_level_groups(self, raw: Mapping[str, Any]) -> None:
        for group_name, value in raw.items():
            if group_name not in ENVELOPE_CORE_GROUPS:
                raise NsRuntimeEnvelopeSchemaError(
                    "Envelope contains unknown top-level group.",
                    details={
                        "group": group_name,
                    },
                )

            if value is None:
                raise NsRuntimeEnvelopeSchemaError(
                    "Envelope group must be omitted instead of null.",
                    details={
                        "group": group_name,
                    },
                )

            if not isinstance(value, dict):
                raise NsRuntimeEnvelopeSchemaError(
                    "Envelope group must be a JSON object.",
                    details={
                        "group": group_name,
                        "actual_type": type(value).__name__,
                    },
                )

            if not value:
                raise NsRuntimeEnvelopeSchemaError(
                    "Envelope group must be omitted instead of empty object.",
                    details={
                        "group": group_name,
                    },
                )

            allowed_fields = ENVELOPE_GROUP_FIELDS[group_name]

            if group_name == "extensions":
                continue

            unknown_fields = sorted(set(value) - allowed_fields)

            if unknown_fields:
                raise NsRuntimeEnvelopeSchemaError(
                    "Envelope group contains unknown fields.",
                    details={
                        "group": group_name,
                        "unknown_fields": unknown_fields,
                    },
                )

    @staticmethod
    def _validate_inbound_forbidden_groups(raw: Mapping[str, Any]) -> None:
        if "source" in raw:
            raise NsRuntimeSourceForgedError()

        if "auth_context" in raw:
            raise NsRuntimeAuthContextForgedError()

    def _resolve_protocol_version(self, raw: Mapping[str, Any]) -> RuntimeProtocolVersion:
        protocol = self._require_group(raw, "protocol")

        try:
            return RuntimeProtocolVersion.from_mapping(protocol)
        except (TypeError, ValueError) as error:
            raise NsRuntimeProtocolVersionError(
                details={
                    "protocol": dict(protocol),
                },
            ) from error

    def _validate_message_type_schema(self, raw: Mapping[str, Any], registration: ProcessorRegistration) -> None:
        schema = registration.schema

        missing_groups = sorted(
            group
            for group in schema.required_groups
            if group not in raw
        )

        if missing_groups:
            raise NsRuntimeEnvelopeSchemaError(
                "Envelope misses required groups for message type.",
                details={
                    "message_type": registration.message_type,
                    "missing_groups": missing_groups,
                },
            )

        unknown_for_type = sorted(set(raw) - set(schema.allowed_groups))

        if unknown_for_type:
            raise NsRuntimeEnvelopeSchemaError(
                "Envelope contains groups not allowed by message type schema.",
                details={
                    "message_type": registration.message_type,
                    "groups": unknown_for_type,
                },
            )

        message = self._require_group(raw, "message")
        missing_message_fields = sorted(
            field
            for field in schema.required_message_fields
            if field not in message
        )

        if missing_message_fields:
            raise NsRuntimeEnvelopeSchemaError(
                "Message group misses required fields.",
                details={
                    "message_type": registration.message_type,
                    "missing_fields": missing_message_fields,
                },
            )

        for group_name, required_fields in schema.required_group_fields.items():
            group = self._require_group(raw, group_name)
            missing_fields = sorted(
                field
                for field in required_fields
                if field not in group
            )

            if missing_fields:
                raise NsRuntimeEnvelopeSchemaError(
                    "Envelope group misses required fields.",
                    details={
                        "message_type": registration.message_type,
                        "group": group_name,
                        "missing_fields": missing_fields,
                    },
                )

    @staticmethod
    def _require_group(raw: Mapping[str, Any], group_name: str) -> Mapping[str, Any]:
        value = raw.get(group_name)

        if not isinstance(value, Mapping):
            raise NsRuntimeEnvelopeSchemaError(
                "Envelope misses required group.",
                details={
                    "group": group_name,
                },
            )

        return value

    @staticmethod
    def _require_string(raw: Mapping[str, Any], field_name: str) -> str:
        value = raw.get(field_name)

        if not isinstance(value, str) or not value.strip():
            raise NsRuntimeEnvelopeSchemaError(
                "Envelope field must be a non-empty string.",
                details={
                    "field": field_name,
                    "actual_type": type(value).__name__,
                },
            )

        return value.strip()
