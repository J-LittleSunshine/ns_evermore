# -*- coding: utf-8 -*-
"""Central protocol compatibility and schema selection policy."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Iterable, Mapping

from ns_common.exceptions import NsRuntimeProtocolVersionError

from .models import ProtocolGroup


_VERSION_PATTERN = re.compile(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:\.(0|[1-9][0-9]*))?")


def _version_error(reason: str) -> NsRuntimeProtocolVersionError:
    return NsRuntimeProtocolVersionError(
        details={"component": "protocol", "reason": reason},
    )


@dataclass(frozen=True, slots=True, order=True)
class ProtocolVersion:
    major: int
    minor: int
    patch: int = 0

    def __post_init__(self) -> None:
        for name in ("major", "minor", "patch"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")

    @classmethod
    def parse(cls, value: object) -> "ProtocolVersion":
        if not isinstance(value, str):
            raise _version_error("invalid_version_format")
        match = _VERSION_PATTERN.fullmatch(value)
        if match is None:
            raise _version_error("invalid_version_format")
        major, minor, patch = match.groups()
        if any(len(component) > 9 for component in (major, minor, patch or "0")):
            raise _version_error("invalid_version_format")
        return cls(int(major), int(minor), int(patch or 0))

    @classmethod
    def from_group(cls, group: ProtocolGroup) -> "ProtocolVersion":
        if not isinstance(group, ProtocolGroup):
            raise _version_error("protocol_group_required")
        return cls(group.major, group.minor, group.patch)

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"


@dataclass(frozen=True, slots=True)
class ProtocolVersionSupport:
    version: ProtocolVersion
    schema_key: str

    def __post_init__(self) -> None:
        if not isinstance(self.version, ProtocolVersion):
            raise TypeError("version must be ProtocolVersion")
        if not isinstance(self.schema_key, str) or not self.schema_key:
            raise ValueError("schema_key must be a non-empty string")


@dataclass(frozen=True, slots=True)
class NegotiatedProtocol:
    requested: ProtocolVersion
    minimum: ProtocolVersion
    selected: ProtocolVersion
    schema_key: str
    downgraded: bool


@dataclass(frozen=True, slots=True, init=False)
class ProtocolCompatibilityMatrix:
    _supported: tuple[ProtocolVersionSupport, ...] = field(repr=False)
    _by_version: Mapping[ProtocolVersion, ProtocolVersionSupport] = field(repr=False)

    def __init__(self, supported: Iterable[ProtocolVersionSupport]) -> None:
        values = tuple(supported)
        if not values:
            raise ValueError("supported protocol versions must not be empty")
        if any(not isinstance(item, ProtocolVersionSupport) for item in values):
            raise TypeError("supported entries must be ProtocolVersionSupport")
        ordered = tuple(sorted(values, key=lambda item: item.version))
        by_version = {item.version: item for item in ordered}
        if len(by_version) != len(ordered):
            raise ValueError("supported protocol versions must be unique")
        object.__setattr__(self, "_supported", ordered)
        object.__setattr__(self, "_by_version", MappingProxyType(by_version))

    @property
    def supported(self) -> tuple[ProtocolVersionSupport, ...]:
        return self._supported

    def negotiate(
        self,
        requested: ProtocolVersion,
        *,
        minimum: ProtocolVersion | None = None,
    ) -> NegotiatedProtocol:
        if not isinstance(requested, ProtocolVersion):
            raise _version_error("requested_version_required")
        effective_minimum = minimum or ProtocolVersion(requested.major, 0, 0)
        if not isinstance(effective_minimum, ProtocolVersion):
            raise _version_error("minimum_version_required")
        if effective_minimum.major != requested.major:
            raise _version_error("minimum_major_mismatch")
        if effective_minimum > requested:
            raise _version_error("minimum_exceeds_requested")

        same_major = tuple(
            support
            for support in self._supported
            if support.version.major == requested.major
        )
        if not same_major:
            raise _version_error("major_not_supported")
        candidates = tuple(
            support
            for support in same_major
            if effective_minimum <= support.version <= requested
        )
        if not candidates:
            raise _version_error("compatible_version_not_found")
        selected = candidates[-1]
        return NegotiatedProtocol(
            requested=requested,
            minimum=effective_minimum,
            selected=selected.version,
            schema_key=selected.schema_key,
            downgraded=selected.version != requested,
        )

    def negotiate_group(self, group: ProtocolGroup) -> NegotiatedProtocol:
        requested = ProtocolVersion.from_group(group)
        minimum = (
            ProtocolVersion.parse(group.min_version)
            if group.min_version is not None
            else None
        )
        return self.negotiate(requested, minimum=minimum)


JSON_V1_PROTOCOL_MATRIX = ProtocolCompatibilityMatrix((
    ProtocolVersionSupport(ProtocolVersion(1, 0, 0), "json.v1/protocol-1.0"),
))


__all__ = (
    "JSON_V1_PROTOCOL_MATRIX",
    "NegotiatedProtocol",
    "ProtocolCompatibilityMatrix",
    "ProtocolVersion",
    "ProtocolVersionSupport",
)
