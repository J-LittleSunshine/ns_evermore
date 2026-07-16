# -*- coding: utf-8 -*-
from __future__ import annotations

import re
import types
from dataclasses import dataclass
from enum import Enum
from typing import (
    Callable,
    Mapping,
)
from uuid import (
    RFC_4122,
    UUID,
    uuid4,
)

from ns_common.exceptions import (
    NsStateError,
    NsValidationError,
)


class NsIdentifierKind(str, Enum):
    RUNTIME_ID = "runtime_id"
    CONNECTION_ID = "connection_id"
    SESSION_ID = "session_id"
    MESSAGE_ID = "message_id"
    SUMMARY_ID = "summary_id"
    DELIVERY_ID = "delivery_id"
    STREAM_ID = "stream_id"
    PLAN_ID = "plan_id"
    OPERATION_ID = "operation_id"


IDENTIFIER_KINDS: tuple[str, ...] = tuple(
    kind.value
    for kind in NsIdentifierKind
)
IDENTIFIER_PREFIXES: Mapping[NsIdentifierKind, str] = types.MappingProxyType({
    NsIdentifierKind.RUNTIME_ID: "runtime",
    NsIdentifierKind.CONNECTION_ID: "connection",
    NsIdentifierKind.SESSION_ID: "session",
    NsIdentifierKind.MESSAGE_ID: "message",
    NsIdentifierKind.SUMMARY_ID: "summary",
    NsIdentifierKind.DELIVERY_ID: "delivery",
    NsIdentifierKind.STREAM_ID: "stream",
    NsIdentifierKind.PLAN_ID: "plan",
    NsIdentifierKind.OPERATION_ID: "operation",
})
IDENTIFIER_FORMAT = "{prefix}_{uuid4_hex}"

_IDENTIFIER_KIND_BY_PREFIX: Mapping[str, NsIdentifierKind] = types.MappingProxyType({
    prefix: kind
    for kind, prefix in IDENTIFIER_PREFIXES.items()
})
_UUID4_HEX_PATTERN = re.compile(r"[0-9a-f]{32}")


@dataclass(frozen=True, slots=True)
class NsIdentifier:
    kind: NsIdentifierKind
    value: str
    uuid_value: UUID

    def __post_init__(self) -> None:
        if not isinstance(self.kind, NsIdentifierKind):
            raise NsValidationError(
                "identifier kind is invalid.",
                details={
                    "field": "identifier.kind",
                    "value": self.kind,
                    "allowed_values": list(IDENTIFIER_KINDS),
                },
            )
        if not _is_rfc4122_uuid4(self.uuid_value):
            raise NsValidationError(
                "identifier UUID must be an RFC 4122 UUIDv4.",
                details={
                    "field": self.kind.value,
                    "value": str(self.uuid_value),
                },
            )

        expected_value = (
            f"{IDENTIFIER_PREFIXES[self.kind]}_{self.uuid_value.hex}"
        )
        if self.value != expected_value:
            raise NsValidationError(
                f"{self.kind.value} does not match its kind and UUID.",
                details={
                    "field": self.kind.value,
                    "value": self.value,
                    "expected_value": expected_value,
                },
            )

    @property
    def payload(self) -> str:
        return self.uuid_value.hex

    def __str__(self) -> str:
        return self.value


UuidFactory = Callable[[], UUID]


class IdentifierFactory:
    """Generate and validate typed runtime identifiers.

    The wire format is ``<kind-prefix>_<32 lowercase UUIDv4 hex chars>``.
    The factory is explicit and stateless apart from its injected UUID source,
    so runtime components do not need a global identifier service.
    """

    def __init__(self, *, uuid_factory: UuidFactory = uuid4) -> None:
        if not callable(uuid_factory):
            raise NsValidationError(
                "uuid_factory must be callable.",
                details={
                    "field": "uuid_factory",
                    "actual_type": type(uuid_factory).__name__,
                },
            )
        self._uuid_factory = uuid_factory

    def generate(self, kind: NsIdentifierKind | str) -> str:
        normalized_kind = _coerce_identifier_kind(kind)
        uuid_value = self._uuid_factory()
        if not _is_rfc4122_uuid4(uuid_value):
            raise NsStateError(
                "identifier UUID factory must return an RFC 4122 UUIDv4.",
                details={
                    "field": "uuid_factory",
                    "actual_type": type(uuid_value).__name__,
                    "value": str(uuid_value),
                },
            )

        prefix = IDENTIFIER_PREFIXES[normalized_kind]
        return f"{prefix}_{uuid_value.hex}"

    def parse(
        self,
        value: object,
        *,
        expected_kind: NsIdentifierKind | str | None = None,
    ) -> NsIdentifier:
        return parse_identifier(value, expected_kind=expected_kind)

    def validate(
        self,
        value: object,
        *,
        expected_kind: NsIdentifierKind | str | None = None,
    ) -> str:
        return self.parse(value, expected_kind=expected_kind).value

    def is_valid(
        self,
        value: object,
        *,
        expected_kind: NsIdentifierKind | str | None = None,
    ) -> bool:
        return is_valid_identifier(value, expected_kind=expected_kind)


NsIdentifierFactory = IdentifierFactory


def generate_identifier(kind: NsIdentifierKind | str) -> str:
    return IdentifierFactory().generate(kind)


def parse_identifier(
    value: object,
    *,
    expected_kind: NsIdentifierKind | str | None = None,
) -> NsIdentifier:
    normalized_expected = (
        None
        if expected_kind is None
        else _coerce_identifier_kind(expected_kind)
    )
    field_name = (
        "identifier"
        if normalized_expected is None
        else normalized_expected.value
    )

    if not isinstance(value, str) or not value or value != value.strip():
        raise _invalid_identifier_error(
            field_name=field_name,
            value=value,
            expected_kind=normalized_expected,
            reason="identifier must be a non-empty string without surrounding whitespace",
        )

    prefix, separator, payload = value.partition("_")
    actual_kind = _IDENTIFIER_KIND_BY_PREFIX.get(prefix)
    if separator != "_" or actual_kind is None:
        raise _invalid_identifier_error(
            field_name=field_name,
            value=value,
            expected_kind=normalized_expected,
            reason="identifier prefix is unknown",
        )

    if _UUID4_HEX_PATTERN.fullmatch(payload) is None:
        raise _invalid_identifier_error(
            field_name=field_name,
            value=value,
            expected_kind=normalized_expected,
            reason="identifier payload must contain 32 lowercase hexadecimal characters",
        )

    uuid_value = UUID(hex=payload)
    if not _is_rfc4122_uuid4(uuid_value):
        raise _invalid_identifier_error(
            field_name=field_name,
            value=value,
            expected_kind=normalized_expected,
            reason="identifier payload must be an RFC 4122 UUIDv4",
        )

    if normalized_expected is not None and actual_kind is not normalized_expected:
        raise NsValidationError(
            f"{field_name} has the wrong identifier kind.",
            details={
                "field": field_name,
                "value": value,
                "expected_kind": normalized_expected.value,
                "actual_kind": actual_kind.value,
                "expected_format": _expected_format(normalized_expected),
            },
        )

    return NsIdentifier(
        kind=actual_kind,
        value=value,
        uuid_value=uuid_value,
    )


def validate_identifier(
    value: object,
    *,
    expected_kind: NsIdentifierKind | str | None = None,
) -> str:
    return parse_identifier(value, expected_kind=expected_kind).value


def is_valid_identifier(
    value: object,
    *,
    expected_kind: NsIdentifierKind | str | None = None,
) -> bool:
    try:
        parse_identifier(value, expected_kind=expected_kind)
    except NsValidationError:
        return False
    return True


def generate_runtime_id() -> str:
    return generate_identifier(NsIdentifierKind.RUNTIME_ID)


def generate_connection_id() -> str:
    return generate_identifier(NsIdentifierKind.CONNECTION_ID)


def generate_session_id() -> str:
    return generate_identifier(NsIdentifierKind.SESSION_ID)


def generate_message_id() -> str:
    return generate_identifier(NsIdentifierKind.MESSAGE_ID)


def generate_summary_id() -> str:
    return generate_identifier(NsIdentifierKind.SUMMARY_ID)


def generate_delivery_id() -> str:
    return generate_identifier(NsIdentifierKind.DELIVERY_ID)


def generate_stream_id() -> str:
    return generate_identifier(NsIdentifierKind.STREAM_ID)


def generate_plan_id() -> str:
    return generate_identifier(NsIdentifierKind.PLAN_ID)


def generate_operation_id() -> str:
    return generate_identifier(NsIdentifierKind.OPERATION_ID)


def _coerce_identifier_kind(value: NsIdentifierKind | str) -> NsIdentifierKind:
    if isinstance(value, NsIdentifierKind):
        return value
    if isinstance(value, str):
        try:
            return NsIdentifierKind(value)
        except ValueError:
            pass

    raise NsValidationError(
        "identifier kind is invalid.",
        details={
            "field": "identifier.kind",
            "value": value,
            "allowed_values": list(IDENTIFIER_KINDS),
        },
    )


def _is_rfc4122_uuid4(value: object) -> bool:
    return (
        isinstance(value, UUID)
        and value.version == 4
        and value.variant == RFC_4122
    )


def _expected_format(kind: NsIdentifierKind | None) -> str:
    if kind is None:
        return "<known_prefix>_<32 lowercase UUIDv4 hex chars>"
    return f"{IDENTIFIER_PREFIXES[kind]}_<32 lowercase UUIDv4 hex chars>"


def _invalid_identifier_error(
    *,
    field_name: str,
    value: object,
    expected_kind: NsIdentifierKind | None,
    reason: str,
) -> NsValidationError:
    return NsValidationError(
        f"{field_name} is invalid.",
        details={
            "field": field_name,
            "value": value,
            "reason": reason,
            "expected_format": _expected_format(expected_kind),
            "allowed_prefixes": sorted(_IDENTIFIER_KIND_BY_PREFIX),
        },
    )


__all__ = [
    "IDENTIFIER_FORMAT",
    "IDENTIFIER_KINDS",
    "IDENTIFIER_PREFIXES",
    "IdentifierFactory",
    "NsIdentifier",
    "NsIdentifierFactory",
    "NsIdentifierKind",
    "generate_connection_id",
    "generate_delivery_id",
    "generate_identifier",
    "generate_message_id",
    "generate_operation_id",
    "generate_plan_id",
    "generate_runtime_id",
    "generate_session_id",
    "generate_stream_id",
    "generate_summary_id",
    "is_valid_identifier",
    "parse_identifier",
    "validate_identifier",
]
