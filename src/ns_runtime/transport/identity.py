# -*- coding: utf-8 -*-
"""Transport-local identifiers and bounded address diagnostics."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable
from uuid import RFC_4122, UUID, uuid4

from ns_common.exceptions import NsStateError, NsValidationError


_IDENTIFIER_PATTERN = re.compile(
    r"transport_(connection|session|stream|path)_[0-9a-f]{32}\Z",
)
_DIGEST_PATTERN = re.compile(r"sha256:[0-9a-f]{16}\Z")


@dataclass(frozen=True, slots=True)
class TransportPathSnapshot:
    path_id: str = field(repr=False)
    path_epoch: int
    local_summary: str
    peer_summary: str
    validated_at: datetime
    migration_count: int = 0

    def __post_init__(self) -> None:
        _validate_identifier(self.path_id, expected_kind="path")
        for field_name in ("path_epoch", "migration_count"):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise NsValidationError(
                    "Transport path counter is invalid.",
                    details={"component": "transport", "field": field_name},
                )
        for field_name in ("local_summary", "peer_summary"):
            if _DIGEST_PATTERN.fullmatch(getattr(self, field_name)) is None:
                raise NsValidationError(
                    "Transport path summary is invalid.",
                    details={"component": "transport", "field": field_name},
                )
        if not isinstance(self.validated_at, datetime):
            raise NsValidationError(
                "Transport path validation time is invalid.",
                details={"component": "transport", "field": "validated_at"},
            )
        try:
            offset = self.validated_at.utcoffset()
            normalized = self.validated_at.astimezone(timezone.utc)
        except Exception:
            offset = None
        if offset is None:
            raise NsValidationError(
                "Transport path validation time must be timezone-aware.",
                details={"component": "transport", "field": "validated_at"},
            )
        object.__setattr__(self, "validated_at", normalized)


@dataclass(frozen=True, slots=True)
class TransportIdentity:
    transport_connection_id: str = field(repr=False)
    transport_session_id: str = field(repr=False)
    transport_stream_id: str = field(repr=False)
    path: TransportPathSnapshot

    def __post_init__(self) -> None:
        _validate_identifier(self.transport_connection_id, expected_kind="connection")
        _validate_identifier(self.transport_session_id, expected_kind="session")
        _validate_identifier(self.transport_stream_id, expected_kind="stream")
        if not isinstance(self.path, TransportPathSnapshot):
            raise NsValidationError(
                "Transport identity path is invalid.",
                details={"component": "transport", "field": "path"},
            )

    def diagnostic_summary(self, *, transport_type: str, tls: bool) -> "TransportDiagnosticSummary":
        if transport_type != "websocket_tcp" or not isinstance(tls, bool):
            raise NsValidationError(
                "Transport diagnostic classification is invalid.",
                details={"component": "transport", "field": "diagnostic"},
            )
        return TransportDiagnosticSummary(
            transport_type=transport_type,
            transport_connection_summary=_digest_text(self.transport_connection_id),
            transport_session_summary=_digest_text(self.transport_session_id),
            transport_stream_summary=_digest_text(self.transport_stream_id),
            path_summary=_digest_text(self.path.path_id),
            peer_summary=self.path.peer_summary,
            tls=tls,
        )


@dataclass(frozen=True, slots=True)
class TransportDiagnosticSummary:
    transport_type: str
    transport_connection_summary: str
    transport_session_summary: str
    transport_stream_summary: str
    path_summary: str
    peer_summary: str
    tls: bool

    def __post_init__(self) -> None:
        if self.transport_type != "websocket_tcp" or not isinstance(self.tls, bool):
            raise NsValidationError(
                "Transport diagnostic summary is invalid.",
                details={"component": "transport", "field": "diagnostic"},
            )
        for field_name in (
            "transport_connection_summary",
            "transport_session_summary",
            "transport_stream_summary",
            "path_summary",
            "peer_summary",
        ):
            if _DIGEST_PATTERN.fullmatch(getattr(self, field_name)) is None:
                raise NsValidationError(
                    "Transport diagnostic digest is invalid.",
                    details={"component": "transport", "field": field_name},
                )


UuidFactory = Callable[[], UUID]


class TransportIdentityFactory:
    """Explicit factory for one adapter; no logical runtime IDs are created."""

    def __init__(self, *, uuid_factory: UuidFactory = uuid4) -> None:
        if not callable(uuid_factory):
            raise NsValidationError(
                "Transport UUID factory is invalid.",
                details={"component": "transport", "field": "uuid_factory"},
            )
        self._uuid_factory = uuid_factory

    def create(
        self,
        *,
        local_address: object,
        peer_address: object,
        validated_at: datetime,
    ) -> TransportIdentity:
        return TransportIdentity(
            transport_connection_id=self._new_identifier("connection"),
            transport_session_id=self._new_identifier("session"),
            transport_stream_id=self._new_identifier("stream"),
            path=TransportPathSnapshot(
                path_id=self._new_identifier("path"),
                path_epoch=0,
                local_summary=_digest_address(local_address),
                peer_summary=_digest_address(peer_address),
                validated_at=validated_at,
                migration_count=0,
            ),
        )

    def _new_identifier(self, kind: str) -> str:
        value = self._uuid_factory()
        if (
            not isinstance(value, UUID)
            or value.variant != RFC_4122
            or value.version != 4
        ):
            raise NsStateError(
                "Transport UUID factory returned an invalid value.",
                details={"component": "transport", "field": "uuid_factory"},
            )
        return f"transport_{kind}_{value.hex}"


def _validate_identifier(value: object, *, expected_kind: str) -> None:
    if not isinstance(value, str) or _IDENTIFIER_PATTERN.fullmatch(value) is None:
        raise NsValidationError(
            "Transport identifier is invalid.",
            details={"component": "transport", "field": f"transport_{expected_kind}_id"},
        )
    if not value.startswith(f"transport_{expected_kind}_"):
        raise NsValidationError(
            "Transport identifier kind is invalid.",
            details={"component": "transport", "field": f"transport_{expected_kind}_id"},
        )


def _digest_text(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _digest_address(value: object) -> str:
    """Digest only bounded scalar address components, never arbitrary repr."""

    normalized: list[str | int] = []
    if isinstance(value, (tuple, list)) and len(value) <= 8:
        for item in value:
            if isinstance(item, bool):
                normalized.append(int(item))
            elif isinstance(item, int):
                normalized.append(item)
            elif isinstance(item, str):
                normalized.append(item[:256])
            else:
                normalized.append(type(item).__name__[:64])
    elif value is None:
        normalized.append("unavailable")
    else:
        normalized.append(type(value).__name__[:64])
    encoded = json.dumps(
        normalized,
        allow_nan=False,
        ensure_ascii=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()[:16]


__all__ = (
    "TransportDiagnosticSummary",
    "TransportIdentity",
    "TransportIdentityFactory",
    "TransportPathSnapshot",
)

