# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import re
import time
import uuid
from dataclasses import (
    asdict,
    dataclass,
    field,
)
from typing import (
    Any,
    Mapping,
)

from ns_common.exceptions import (
    NsRuntimeCodecError,
    NsRuntimeProtocolError,
)

RUNTIME_PROTOCOL_NAME = "ns_runtime"
RUNTIME_PROTOCOL_VERSION = 1

_MESSAGE_TYPE_PATTERN = re.compile(r"^[a-zA-Z][a-zA-Z0-9_.:-]*$")
_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_.:@/-]+$")


class NsRuntimeClientType:
    FRONTEND_USER = "frontend_user"
    SUB_NODE = "sub_node"
    NS_NODE = "ns_node"
    NS_CLIENT = "ns_client"
    ADMIN = "admin"


class NsRuntimeMessageType:
    CONNECTION_HELLO = "connection.hello"
    CONNECTION_ACCEPTED = "connection.accepted"
    CONNECTION_REJECTED = "connection.rejected"

    HEARTBEAT_PING = "heartbeat.ping"
    HEARTBEAT_PONG = "heartbeat.pong"

    PROCESSOR_REQUEST = "processor.request"
    PROCESSOR_RESPONSE = "processor.response"
    PROCESSOR_ERROR = "processor.error"

    NODE_REGISTER = "node.register"
    NODE_UNREGISTER = "node.unregister"
    NODE_STATUS = "node.status"

    ROUTING_FORWARD = "routing.forward"
    ACK = "ack"

    ADMIN_COMMAND = "admin.command"
    ADMIN_RESPONSE = "admin.response"
    ADMIN_ERROR = "admin.error"


def new_runtime_message_id() -> str:
    return uuid.uuid4().hex


def current_epoch_ms() -> int:
    return int(time.time() * 1000)


def _ensure_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if value is None:
        return {}

    if not isinstance(value, Mapping):
        raise NsRuntimeProtocolError(
            f"{field_name} must be a JSON object.",
            details={
                "field": field_name,
                "actual_type": type(value).__name__,
            },
        )

    return dict(value)


def _ensure_required_text(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise NsRuntimeProtocolError(
            f"{field_name} must be a non-empty string.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )

    return value.strip()


def _ensure_optional_text(value: Any, field_name: str) -> str | None:
    if value is None:
        return None

    if not isinstance(value, str):
        raise NsRuntimeProtocolError(
            f"{field_name} must be a string.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )

    text = value.strip()
    return text or None


def _ensure_required_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise NsRuntimeProtocolError(
            f"{field_name} must be an integer.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )

    return value


def _ensure_optional_positive_int(value: Any, field_name: str) -> int | None:
    if value is None:
        return None

    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise NsRuntimeProtocolError(
            f"{field_name} must be a positive integer.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )

    return value


def _ensure_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise NsRuntimeProtocolError(
            f"{field_name} must be a boolean.",
            details={
                "field": field_name,
                "value": value,
                "actual_type": type(value).__name__,
            },
        )

    return value


def _validate_id_text(value: str, field_name: str) -> None:
    if _ID_PATTERN.fullmatch(value) is None:
        raise NsRuntimeProtocolError(
            f"{field_name} contains invalid characters.",
            details={
                "field": field_name,
                "value": value,
                "allowed_pattern": _ID_PATTERN.pattern,
            },
        )


def _validate_message_type(value: str) -> None:
    if _MESSAGE_TYPE_PATTERN.fullmatch(value) is None:
        raise NsRuntimeProtocolError(
            "message_type contains invalid characters.",
            details={
                "field": "message_type",
                "value": value,
                "allowed_pattern": _MESSAGE_TYPE_PATTERN.pattern,
            },
        )


def _validate_json_value(value: Any, field_name: str) -> None:
    try:
        json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise NsRuntimeCodecError(
            f"{field_name} must be JSON serializable.",
            details={
                "field": field_name,
                "actual_type": type(value).__name__,
                "error": str(exc),
            },
        ) from exc


def _drop_none(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _drop_none(item)
            for key, item in value.items()
            if item is not None
        }

    if isinstance(value, list):
        return [
            _drop_none(item)
            for item in value
        ]

    return value


@dataclass(slots=True, kw_only=True)
class NsRuntimePeer:
    client_type: str
    client_id: str | None = None
    runtime_id: str | None = None
    node_id: str | None = None
    node_group: str | None = None
    principal_id: str | None = None
    principal_type: str | None = None

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any] | None, *, field_name: str) -> "NsRuntimePeer | None":
        if value is None:
            return None

        data = _ensure_mapping(value, field_name)

        peer = cls(
            client_type=_ensure_required_text(data.get("client_type"), f"{field_name}.client_type"),
            client_id=_ensure_optional_text(data.get("client_id"), f"{field_name}.client_id"),
            runtime_id=_ensure_optional_text(data.get("runtime_id"), f"{field_name}.runtime_id"),
            node_id=_ensure_optional_text(data.get("node_id"), f"{field_name}.node_id"),
            node_group=_ensure_optional_text(data.get("node_group"), f"{field_name}.node_group"),
            principal_id=_ensure_optional_text(data.get("principal_id"), f"{field_name}.principal_id"),
            principal_type=_ensure_optional_text(data.get("principal_type"), f"{field_name}.principal_type"),
        )
        peer.validate(field_name)
        return peer

    def validate(self, field_name: str = "peer") -> None:
        self.client_type = _ensure_required_text(self.client_type, f"{field_name}.client_type")

        for item_field in (
                "client_id",
                "runtime_id",
                "node_id",
                "node_group",
                "principal_id",
                "principal_type",
        ):
            item_value = getattr(self, item_field)
            if item_value is None:
                continue

            normalized = _ensure_required_text(item_value, f"{field_name}.{item_field}")
            _validate_id_text(normalized, f"{field_name}.{item_field}")
            setattr(self, item_field, normalized)

    def to_mapping(self) -> dict[str, Any]:
        self.validate()
        return _drop_none(asdict(self))


@dataclass(slots=True, kw_only=True)
class NsRuntimeEnvelope:
    message_type: str
    payload: dict[str, Any] = field(default_factory=dict)

    protocol: str = RUNTIME_PROTOCOL_NAME
    version: int = RUNTIME_PROTOCOL_VERSION
    message_id: str = field(default_factory=new_runtime_message_id)
    timestamp_epoch_ms: int = field(default_factory=current_epoch_ms)

    source: NsRuntimePeer | None = None
    target: NsRuntimePeer | None = None

    trace_id: str | None = None
    correlation_id: str | None = None
    reply_to_message_id: str | None = None

    ttl_ms: int | None = None
    priority: int = 0
    requires_ack: bool = False

    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def new(
            cls,
            *,
            message_type: str,
            payload: Mapping[str, Any] | None = None,
            source: NsRuntimePeer | None = None,
            target: NsRuntimePeer | None = None,
            trace_id: str | None = None,
            correlation_id: str | None = None,
            reply_to_message_id: str | None = None,
            ttl_ms: int | None = None,
            priority: int = 0,
            requires_ack: bool = False,
            metadata: Mapping[str, Any] | None = None,
    ) -> "NsRuntimeEnvelope":
        envelope = cls(
            message_type=message_type,
            payload=dict(payload or {}),
            source=source,
            target=target,
            trace_id=trace_id,
            correlation_id=correlation_id,
            reply_to_message_id=reply_to_message_id,
            ttl_ms=ttl_ms,
            priority=priority,
            requires_ack=requires_ack,
            metadata=dict(metadata or {}),
        )
        envelope.validate()
        return envelope

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "NsRuntimeEnvelope":
        data = _ensure_mapping(value, "envelope")

        envelope = cls(
            protocol=_ensure_required_text(data.get("protocol", RUNTIME_PROTOCOL_NAME), "protocol"),
            version=_ensure_required_int(data.get("version", RUNTIME_PROTOCOL_VERSION), "version"),
            message_id=_ensure_required_text(data.get("message_id"), "message_id"),
            message_type=_ensure_required_text(data.get("message_type"), "message_type"),
            timestamp_epoch_ms=_ensure_required_int(data.get("timestamp_epoch_ms"), "timestamp_epoch_ms"),
            source=NsRuntimePeer.from_mapping(data.get("source"), field_name="source"),
            target=NsRuntimePeer.from_mapping(data.get("target"), field_name="target"),
            trace_id=_ensure_optional_text(data.get("trace_id"), "trace_id"),
            correlation_id=_ensure_optional_text(data.get("correlation_id"), "correlation_id"),
            reply_to_message_id=_ensure_optional_text(data.get("reply_to_message_id"), "reply_to_message_id"),
            ttl_ms=_ensure_optional_positive_int(data.get("ttl_ms"), "ttl_ms"),
            priority=_ensure_required_int(data.get("priority", 0), "priority"),
            requires_ack=_ensure_bool(data.get("requires_ack", False), "requires_ack"),
            payload=_ensure_mapping(data.get("payload"), "payload"),
            metadata=_ensure_mapping(data.get("metadata"), "metadata"),
        )
        envelope.validate()
        return envelope

    def validate(self) -> None:
        self.protocol = _ensure_required_text(self.protocol, "protocol")
        if self.protocol != RUNTIME_PROTOCOL_NAME:
            raise NsRuntimeProtocolError(
                "protocol is unsupported.",
                details={
                    "field": "protocol",
                    "value": self.protocol,
                    "expected": RUNTIME_PROTOCOL_NAME,
                },
            )

        self.version = _ensure_required_int(self.version, "version")
        if self.version != RUNTIME_PROTOCOL_VERSION:
            raise NsRuntimeProtocolError(
                "protocol version is unsupported.",
                details={
                    "field": "version",
                    "value": self.version,
                    "expected": RUNTIME_PROTOCOL_VERSION,
                },
            )

        self.message_id = _ensure_required_text(self.message_id, "message_id")
        _validate_id_text(self.message_id, "message_id")

        self.message_type = _ensure_required_text(self.message_type, "message_type")
        _validate_message_type(self.message_type)

        self.timestamp_epoch_ms = _ensure_required_int(self.timestamp_epoch_ms, "timestamp_epoch_ms")
        if self.timestamp_epoch_ms <= 0:
            raise NsRuntimeProtocolError(
                "timestamp_epoch_ms must be a positive integer.",
                details={
                    "field": "timestamp_epoch_ms",
                    "value": self.timestamp_epoch_ms,
                },
            )

        if self.source is not None:
            self.source.validate("source")

        if self.target is not None:
            self.target.validate("target")

        for item_field in (
                "trace_id",
                "correlation_id",
                "reply_to_message_id",
        ):
            item_value = getattr(self, item_field)
            if item_value is None:
                continue

            normalized = _ensure_required_text(item_value, item_field)
            _validate_id_text(normalized, item_field)
            setattr(self, item_field, normalized)

        self.ttl_ms = _ensure_optional_positive_int(self.ttl_ms, "ttl_ms")
        self.priority = _ensure_required_int(self.priority, "priority")
        self.requires_ack = _ensure_bool(self.requires_ack, "requires_ack")

        if not isinstance(self.payload, dict):
            raise NsRuntimeProtocolError(
                "payload must be a JSON object.",
                details={
                    "field": "payload",
                    "actual_type": type(self.payload).__name__,
                },
            )

        if not isinstance(self.metadata, dict):
            raise NsRuntimeProtocolError(
                "metadata must be a JSON object.",
                details={
                    "field": "metadata",
                    "actual_type": type(self.metadata).__name__,
                },
            )

        _validate_json_value(self.payload, "payload")
        _validate_json_value(self.metadata, "metadata")

    def to_mapping(self) -> dict[str, Any]:
        self.validate()

        data = asdict(self)

        if self.source is not None:
            data["source"] = self.source.to_mapping()

        if self.target is not None:
            data["target"] = self.target.to_mapping()

        return _drop_none(data)

    def is_expired(self, *, now_epoch_ms: int | None = None) -> bool:
        if self.ttl_ms is None:
            return False

        now_value = now_epoch_ms if now_epoch_ms is not None else current_epoch_ms()
        return now_value > self.timestamp_epoch_ms + self.ttl_ms

    def build_ack(self, *, source: NsRuntimePeer | None = None, metadata: Mapping[str, Any] | None = None) -> "NsRuntimeEnvelope":
        return NsRuntimeEnvelope.new(
            message_type=NsRuntimeMessageType.ACK,
            payload={
                "ack_message_id": self.message_id,
                "ack_message_type": self.message_type,
            },
            source=source,
            target=self.source,
            trace_id=self.trace_id,
            correlation_id=self.correlation_id or self.message_id,
            reply_to_message_id=self.message_id,
            metadata=dict(metadata or {}),
        )

    def build_error_response(
            self,
            *,
            code: str,
            message: str,
            numeric_code: int | None = None,
            details: Mapping[str, Any] | None = None,
            source: NsRuntimePeer | None = None,
            metadata: Mapping[str, Any] | None = None,
    ) -> "NsRuntimeEnvelope":
        payload: dict[str, Any] = {
            "code": code,
            "message": message,
            "details": dict(details or {}),
        }

        if numeric_code is not None:
            payload["numeric_code"] = numeric_code

        return NsRuntimeEnvelope.new(
            message_type=NsRuntimeMessageType.PROCESSOR_ERROR,
            payload=payload,
            source=source,
            target=self.source,
            trace_id=self.trace_id,
            correlation_id=self.correlation_id or self.message_id,
            reply_to_message_id=self.message_id,
            metadata=dict(metadata or {}),
        )


class NsRuntimeJsonCodec:
    @staticmethod
    def encode(envelope: NsRuntimeEnvelope) -> str:
        if not isinstance(envelope, NsRuntimeEnvelope):
            raise NsRuntimeCodecError(
                "Runtime JSON codec can only encode NsRuntimeEnvelope.",
                details={
                    "actual_type": type(envelope).__name__,
                },
            )

        try:
            return json.dumps(
                envelope.to_mapping(),
                ensure_ascii=False,
                separators=(",", ":"),
            )
        except (TypeError, ValueError) as exc:
            raise NsRuntimeCodecError(
                "Failed to encode runtime envelope.",
                details={
                    "message_id": getattr(envelope, "message_id", None),
                    "message_type": getattr(envelope, "message_type", None),
                    "error": str(exc),
                },
            ) from exc

    @staticmethod
    def decode(raw_message: str | bytes | bytearray | memoryview) -> NsRuntimeEnvelope:
        try:
            if isinstance(raw_message, str):
                text = raw_message
            elif isinstance(raw_message, (bytes, bytearray, memoryview)):
                text = bytes(raw_message).decode("utf-8")
            else:
                raise NsRuntimeCodecError(
                    "Runtime JSON codec input must be str or bytes.",
                    details={
                        "actual_type": type(raw_message).__name__,
                    },
                )

            data = json.loads(text)
        except UnicodeDecodeError as exc:
            raise NsRuntimeCodecError(
                "Runtime message is not valid UTF-8.",
                details={
                    "error": str(exc),
                },
            ) from exc
        except json.JSONDecodeError as exc:
            raise NsRuntimeCodecError(
                "Runtime message is not valid JSON.",
                details={
                    "line": exc.lineno,
                    "column": exc.colno,
                    "message": exc.msg,
                },
            ) from exc

        try:
            return NsRuntimeEnvelope.from_mapping(data)
        except NsRuntimeProtocolError:
            raise
        except Exception as exc:
            raise NsRuntimeCodecError(
                "Failed to decode runtime envelope.",
                details={
                    "actual_type": type(data).__name__,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
            ) from exc

    @staticmethod
    def encode_bytes(envelope: NsRuntimeEnvelope) -> bytes:
        return NsRuntimeJsonCodec.encode(envelope).encode("utf-8")

    @staticmethod
    def decode_bytes(raw_message: bytes | bytearray | memoryview) -> NsRuntimeEnvelope:
        return NsRuntimeJsonCodec.decode(raw_message)
