# -*- coding: utf-8 -*-
from __future__ import annotations

import uuid
from dataclasses import dataclass
from typing import (
    Any,
    Mapping,
    TYPE_CHECKING
)

from ns_common.exceptions import (
    NsEvermoreError,
    NsRuntimeEnvelopeSchemaError
)
from ns_runtime.auth import (
    RuntimeAuthenticator
)
from ns_runtime.models import (
    RuntimeComponentType,
    RuntimeSessionContext,
    utc_now_iso
)
from ns_runtime.protocol import EnvelopeCodec
from ns_runtime.session import (
    RuntimeConnectionRecord,
    RuntimeSessionRegistry
)

if TYPE_CHECKING:
    pass

_COMPONENT_TYPES: frozenset[str] = frozenset(
    {
        "frontend",
        "client",
        "node",
        "backend",
        "runtime",
        "sub_node",
        "management",
    }
)


@dataclass(slots=True, kw_only=True)
class ConnectionHello:
    token: str
    component_type: RuntimeComponentType
    requested_capabilities: tuple[str, ...]
    raw: Mapping[str, Any]


@dataclass(slots=True, kw_only=True)
class RuntimeHandshakeOutcome:
    accepted: bool
    envelope: dict[str, Any]
    session: RuntimeSessionContext | None = None
    close_code: int = 1008
    close_reason: str = ""


class RuntimeHandshakeService:
    def __init__(self, *, runtime_id: str, codec: EnvelopeCodec, authenticator: RuntimeAuthenticator, session_registry: RuntimeSessionRegistry) -> None:
        self._runtime_id = runtime_id
        self._codec = codec
        self._authenticator = authenticator
        self._session_registry = session_registry

    async def accept(self, *, frame_text: str, record: RuntimeConnectionRecord, remote_address: str) -> RuntimeHandshakeOutcome:
        try:
            hello = self.parse_connection_hello(frame_text)
            auth_result = await self._authenticator.authenticate_connection_hello(
                hello,
                connection_id=record.connection_id,
                remote_address=remote_address,
            )

            if not auth_result.accepted:
                self._session_registry.reject(record, state="auth_failed", reason=auth_result.reject_reason)
                return RuntimeHandshakeOutcome(
                    accepted=False,
                    envelope=self.build_rejected_envelope(
                        record,
                        code=auth_result.reject_code,
                        reason=auth_result.reject_reason,
                    ),
                    close_code=1008,
                    close_reason=auth_result.reject_reason,
                )

            session = self._session_registry.activate(record, auth_result)
            return RuntimeHandshakeOutcome(
                accepted=True,
                envelope=self.build_accepted_envelope(record, session),
                session=session,
                close_code=1000,
                close_reason="accepted",
            )
        except Exception as exc:  # noqa
            code, reason = self._normalize_reject_reason(exc)
            self._session_registry.reject(record, state="protocol_failed", reason=reason)
            return RuntimeHandshakeOutcome(
                accepted=False,
                envelope=self.build_rejected_envelope(record, code=code, reason=reason),
                close_code=1002,
                close_reason=reason,
            )

    def parse_connection_hello(self, frame_text: str) -> ConnectionHello:
        raw = self._codec.parse_connection_hello(frame_text)

        payload = raw.get("payload")
        if not isinstance(payload, dict):
            raise NsRuntimeEnvelopeSchemaError("connection.hello must contain payload group.")

        mode = payload.get("mode")
        if mode != "inline":
            raise NsRuntimeEnvelopeSchemaError(
                "connection.hello payload must use inline mode.",
                details={
                    "mode": mode,
                },
            )

        inline = payload.get("inline")
        if not isinstance(inline, dict):
            raise NsRuntimeEnvelopeSchemaError("connection.hello payload.inline must be an object.")

        token = self._require_non_empty_str(inline, "token", "payload.inline")
        component_type_raw = self._require_non_empty_str(inline, "component_type", "payload.inline")
        requested_capabilities = self._read_string_tuple(inline.get("requested_capabilities", ()), "payload.inline.requested_capabilities")

        if component_type_raw not in _COMPONENT_TYPES:
            raise NsRuntimeEnvelopeSchemaError(
                "connection.hello component_type is invalid.",
                details={
                    "component_type": component_type_raw,
                    "allowed_values": sorted(_COMPONENT_TYPES),
                },
            )

        return ConnectionHello(
            token=token,
            component_type=component_type_raw,  # type: ignore[arg-type]
            requested_capabilities=requested_capabilities,
            raw=raw,
        )

    def build_accepted_envelope(self, record: RuntimeConnectionRecord, session: RuntimeSessionContext) -> dict[str, Any]:
        return {
            "protocol": {
                "version": self._codec.protocol_version_text,
            },
            "message": {
                "message_id": str(uuid.uuid4()),
                "type": "connection.accepted",
                "category": "connection",
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "best_effort",
            },
            "source": {
                "runtime_id": self._runtime_id,
                "connection_id": "runtime",
                "session_id": "runtime",
                "identity": self._runtime_id,
                "tenant_id": "system",
                "component_type": "runtime",
                "capabilities_summary": [
                    "connection.accepted",
                ],
                "connection_epoch": 0,
            },
            "target": {
                "kind": "connection",
                "connection_id": record.connection_id,
            },
            "payload": {
                "mode": "inline",
                "inline": {
                    "connection_id": record.connection_id,
                    "session_id": record.session_id,
                    "connection_epoch": record.connection_epoch,
                    "negotiated_protocol_version": self._codec.protocol_version_text,
                    "heartbeat_interval_seconds": 20,
                    "session_expires_at": session.auth_expires_at,
                    "server_time": utc_now_iso(),
                    "runtime_id": self._runtime_id,
                    "role": session.role,
                },
            },
            "trace": {
                "trace_id": str(uuid.uuid4()),
                "request_id": record.connection_id,
            },
        }

    def build_rejected_envelope(self, record: RuntimeConnectionRecord, *, code: str, reason: str) -> dict[str, Any]:
        return {
            "protocol": {
                "version": self._codec.protocol_version_text,
            },
            "message": {
                "message_id": str(uuid.uuid4()),
                "type": "connection.rejected",
                "category": "connection",
                "priority": 100,
                "created_at": utc_now_iso(),
                "reliability": "best_effort",
            },
            "source": {
                "runtime_id": self._runtime_id,
                "connection_id": "runtime",
                "session_id": "runtime",
                "identity": self._runtime_id,
                "tenant_id": "system",
                "component_type": "runtime",
                "capabilities_summary": [
                    "connection.rejected",
                ],
                "connection_epoch": 0,
            },
            "target": {
                "kind": "connection",
                "connection_id": record.connection_id,
            },
            "payload": {
                "mode": "inline",
                "inline": {
                    "code": code,
                    "reason": reason,
                    "connection_id": record.connection_id,
                    "server_time": utc_now_iso(),
                },
            },
            "trace": {
                "trace_id": str(uuid.uuid4()),
                "request_id": record.connection_id,
            },
        }

    @staticmethod
    def _normalize_reject_reason(exc: Exception) -> tuple[str, str]:
        if isinstance(exc, NsEvermoreError):
            return exc.code, exc.message

        return "RUNTIME_HANDSHAKE_REJECTED", str(exc) or exc.__class__.__name__

    @staticmethod
    def _require_non_empty_str(data: Mapping[str, Any], field_name: str, group_name: str) -> str:
        value = data.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise NsRuntimeEnvelopeSchemaError(
                "connection.hello field must be a non-empty string.",
                details={
                    "group": group_name,
                    "field": field_name,
                },
            )

        return value.strip()

    @staticmethod
    def _read_string_tuple(value: Any, field_name: str) -> tuple[str, ...]:
        if value is None:
            return ()

        if not isinstance(value, list):
            raise NsRuntimeEnvelopeSchemaError(
                "connection.hello requested capabilities must be a string list.",
                details={
                    "field": field_name,
                    "actual_type": type(value).__name__,
                },
            )

        result: list[str] = []
        for item in value:
            if not isinstance(item, str) or not item.strip():
                raise NsRuntimeEnvelopeSchemaError(
                    "connection.hello requested capabilities must only contain non-empty strings.",
                    details={
                        "field": field_name,
                    },
                )
            result.append(item.strip())

        return tuple(sorted(set(result)))
