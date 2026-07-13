# -*- coding: utf-8 -*-
from __future__ import annotations

from abc import (
    ABC,
    abstractmethod,
)
from dataclasses import dataclass
from typing import (
    Literal,
    TYPE_CHECKING,
)

from ns_runtime.models import (
    Envelope,
    MessageReliability,
)

if TYPE_CHECKING:
    from ns_runtime.routing import RuntimeRouteTarget

PayloadReferenceValidationStatus = Literal[
    "valid",
    "rejected",
    "unavailable",
]

PayloadReferenceRejectionReason = Literal[
    "invalid",
    "denied",
    "expired",
    "checksum_mismatch",
    "version_mismatch",
]

PayloadReferenceUnavailableReason = Literal[
    "validation_unavailable",
    "validation_timeout",
]

PayloadReferenceValidationReason = Literal[
    "valid",
    "invalid",
    "denied",
    "expired",
    "checksum_mismatch",
    "version_mismatch",
    "validation_unavailable",
    "validation_timeout",
]


@dataclass(slots=True, frozen=True, kw_only=True)
class RuntimePayloadReference:
    object_id: str
    version: str
    checksum: str
    content_type: str = ""
    size_bytes: int | None = None

    @classmethod
    def from_envelope(cls, envelope: Envelope) -> "RuntimePayloadReference | None":
        payload = envelope.raw.get("payload")

        if not isinstance(payload, dict):
            return None

        if payload.get("mode") != "reference":
            return None

        payload_ref = payload.get("payload_ref")
        if not isinstance(payload_ref, dict):
            return None

        size_bytes = payload.get("size_bytes")

        return cls(
            object_id=str(payload_ref.get("object_id", "")).strip(),
            version=str(payload_ref.get("version", "")).strip(),
            checksum=str(payload.get("checksum", "")).strip(),
            content_type=str(payload.get("content_type", "")).strip(),
            size_bytes=(size_bytes if isinstance(size_bytes, int) and not isinstance(size_bytes, bool) else None),
        )

    def to_dict(self) -> dict[str, object]:
        data: dict[str, object] = {
            "object_id": self.object_id,
            "version": self.version,
            "checksum": self.checksum,
        }

        if self.content_type:
            data["content_type"] = self.content_type

        if self.size_bytes is not None:
            data["size_bytes"] = self.size_bytes

        return data


@dataclass(slots=True, frozen=True, kw_only=True)
class PayloadReferenceValidationRequest:
    reference: RuntimePayloadReference

    message_id: str
    message_type: str
    message_reliability: MessageReliability

    source_connection_id: str
    source_identity: str
    source_tenant_id: str
    source_component_type: str
    source_capabilities: tuple[str, ...]
    auth_snapshot_id: str

    targets: tuple["RuntimeRouteTarget", ...]


@dataclass(slots=True, frozen=True, kw_only=True)
class PayloadReferenceValidationResult:
    status: PayloadReferenceValidationStatus
    reason: PayloadReferenceValidationReason

    @classmethod
    def valid(cls) -> "PayloadReferenceValidationResult":
        return cls(status="valid", reason="valid")

    @classmethod
    def rejected(cls, *, reason: PayloadReferenceRejectionReason) -> "PayloadReferenceValidationResult":
        return cls(status="rejected", reason=reason)

    @classmethod
    def unavailable(cls, *, reason: PayloadReferenceUnavailableReason = "validation_unavailable") -> "PayloadReferenceValidationResult":
        return cls(status="unavailable", reason=reason)


class PayloadReferenceValidator(ABC):
    @abstractmethod
    async def validate(self, request: PayloadReferenceValidationRequest) -> PayloadReferenceValidationResult:
        raise NotImplementedError


class UnavailablePayloadReferenceValidator(PayloadReferenceValidator):
    async def validate(self, request: PayloadReferenceValidationRequest) -> PayloadReferenceValidationResult:
        _ = request

        return PayloadReferenceValidationResult.unavailable(
            reason="validation_unavailable",
        )
