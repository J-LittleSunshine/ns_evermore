# -*- coding: utf-8 -*-
"""Typed P05-only IAM boundary and deterministic test adapter."""

from __future__ import annotations

import asyncio
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from types import MappingProxyType
from typing import Iterable, Mapping

from ns_common.exceptions import (
    NsRuntimeIamDeniedError,
    NsRuntimeIamTimeoutError,
    NsValidationError,
)
from ns_common.time import Clock
from ns_common.iam import IamPrincipalType

from .hello import HandshakeCredential, PendingHelloClaims


_AUTHORITY_VALUE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:@/-]{0,255}")
_CAPABILITY_PATTERN = re.compile(
    r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+"
)


@dataclass(frozen=True, slots=True, kw_only=True)
class HandshakeIamAuthority:
    identity: str = field(repr=False)
    tenant_id: str = field(repr=False)
    component_type: str
    principal_type: IamPrincipalType
    capabilities: frozenset[str] = field(repr=False)
    permissions: Mapping[str, bool] = field(repr=False)
    permission_snapshot_ref: str = field(repr=False)
    permission_digest: str = field(repr=False)
    permission_version: str = field(repr=False)
    issued_at: datetime
    expires_at: datetime
    resume_eligible: bool
    iam_mode: str = "test"

    def __post_init__(self) -> None:
        for name in (
            "identity", "tenant_id", "component_type", "permission_snapshot_ref",
            "permission_digest", "permission_version", "iam_mode",
        ):
            value = getattr(self, name)
            if (
                not isinstance(value, str)
                or _AUTHORITY_VALUE_PATTERN.fullmatch(value) is None
            ):
                _invalid(name)
        if not isinstance(self.capabilities, frozenset) or any(
            not isinstance(item, str)
            or _CAPABILITY_PATTERN.fullmatch(item) is None
            for item in self.capabilities
        ):
            _invalid("capabilities")
        if not isinstance(self.principal_type, IamPrincipalType):
            _invalid("principal_type")
        if not isinstance(self.permissions, Mapping):
            _invalid("permissions")
        frozen_permissions: dict[str, bool] = {}
        for key, value in self.permissions.items():
            if (
                not isinstance(key, str)
                or _CAPABILITY_PATTERN.fullmatch(key) is None
                or not isinstance(value, bool)
            ):
                _invalid("permissions")
            frozen_permissions[key] = value
        object.__setattr__(
            self,
            "permissions",
            MappingProxyType(frozen_permissions),
        )
        object.__setattr__(
            self,
            "issued_at",
            _utc(self.issued_at, "issued_at"),
        )
        object.__setattr__(
            self,
            "expires_at",
            _utc(self.expires_at, "expires_at"),
        )
        if self.expires_at <= self.issued_at:
            _invalid("expires_at")
        if not isinstance(self.resume_eligible, bool):
            _invalid("resume_eligible")

    def detached_copy(self) -> "HandshakeIamAuthority":
        return HandshakeIamAuthority(
            identity=self.identity,
            tenant_id=self.tenant_id,
            component_type=self.component_type,
            principal_type=self.principal_type,
            capabilities=frozenset(self.capabilities),
            permissions=dict(self.permissions),
            permission_snapshot_ref=self.permission_snapshot_ref,
            permission_digest=self.permission_digest,
            permission_version=self.permission_version,
            issued_at=self.issued_at,
            expires_at=self.expires_at,
            resume_eligible=self.resume_eligible,
            iam_mode=self.iam_mode,
        )


@dataclass(frozen=True, slots=True, kw_only=True, repr=False)
class HandshakeIamRequest:
    claims: PendingHelloClaims
    credential: HandshakeCredential

    def __post_init__(self) -> None:
        if not isinstance(self.claims, PendingHelloClaims):
            _invalid("claims")
        if not isinstance(self.credential, HandshakeCredential):
            _invalid("credential")

    def __repr__(self) -> str:
        return "HandshakeIamRequest(redacted=True)"


class HandshakeIamAdapter(ABC):
    @abstractmethod
    async def authenticate(
        self,
        request: HandshakeIamRequest,
    ) -> HandshakeIamAuthority:
        raise NotImplementedError


class FailClosedHandshakeIamAdapter(HandshakeIamAdapter):
    """Production-safe P05 default until the P06 backend exists."""

    async def authenticate(
        self,
        request: HandshakeIamRequest,
    ) -> HandshakeIamAuthority:
        if not isinstance(request, HandshakeIamRequest):
            _invalid("request")
        credential = request.credential.take()
        del credential
        raise NsRuntimeIamDeniedError(
            details={
                "component": "logical_connection",
                "operation": "handshake_authentication",
                "reason": "production_iam_unavailable",
            },
        )


class TestIamAction(str, Enum):
    ALLOW = "allow"
    DENY = "deny"
    TIMEOUT = "timeout"
    CANCEL = "cancel"
    EXPIRED = "expired"
    INCONSISTENT = "inconsistent"


@dataclass(frozen=True, slots=True, kw_only=True)
class TestIamOutcome:
    action: TestIamAction
    authority: HandshakeIamAuthority | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.action, TestIamAction):
            _invalid("action")
        if self.action in {
            TestIamAction.ALLOW,
            TestIamAction.EXPIRED,
            TestIamAction.INCONSISTENT,
        }:
            if not isinstance(self.authority, HandshakeIamAuthority):
                _invalid("authority")
        elif self.authority is not None:
            _invalid("authority")


class DeterministicTestIamAdapter(HandshakeIamAdapter):
    """Explicit, offline, call-ordered adapter for P05 lifecycle tests."""

    def __init__(
        self,
        outcomes: Iterable[TestIamOutcome],
        *,
        clock: Clock,
        timeout_delay_seconds: float = 3_600.0,
    ) -> None:
        values = tuple(outcomes)
        if not values or any(not isinstance(item, TestIamOutcome) for item in values):
            _invalid("outcomes")
        if not isinstance(clock, Clock):
            _invalid("clock")
        if (
            isinstance(timeout_delay_seconds, bool)
            or not isinstance(timeout_delay_seconds, (int, float))
            or not 0 < float(timeout_delay_seconds) < float("inf")
        ):
            _invalid("timeout_delay_seconds")
        self._outcomes = values
        self._clock = clock
        self._timeout_delay_seconds = float(timeout_delay_seconds)
        self._next_outcome = 0
        self._lock = asyncio.Lock()
        self._call_count = 0
        self._consumed_credential_count = 0

    @property
    def call_count(self) -> int:
        return self._call_count

    @property
    def consumed_credential_count(self) -> int:
        return self._consumed_credential_count

    async def authenticate(
        self,
        request: HandshakeIamRequest,
    ) -> HandshakeIamAuthority:
        if not isinstance(request, HandshakeIamRequest):
            _invalid("request")
        credential = request.credential.take()
        del credential
        self._consumed_credential_count += 1
        async with self._lock:
            if self._next_outcome >= len(self._outcomes):
                raise NsRuntimeIamDeniedError(
                    details={
                        "component": "test_iam_adapter",
                        "reason": "outcome_exhausted",
                    },
                )
            outcome = self._outcomes[self._next_outcome]
            self._next_outcome += 1
            self._call_count += 1

        if outcome.action is TestIamAction.DENY:
            raise NsRuntimeIamDeniedError(
                details={
                    "component": "test_iam_adapter",
                    "reason": "configured_denial",
                },
            )
        if outcome.action is TestIamAction.TIMEOUT:
            await self._clock.sleep(self._timeout_delay_seconds)
            raise NsRuntimeIamTimeoutError(
                details={
                    "component": "test_iam_adapter",
                    "reason": "configured_timeout",
                },
            )
        if outcome.action is TestIamAction.CANCEL:
            raise asyncio.CancelledError
        if outcome.authority is None:
            raise NsRuntimeIamDeniedError(
                details={
                    "component": "test_iam_adapter",
                    "reason": "authority_missing",
                },
            )
        return outcome.authority


def _utc(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        _invalid(field_name)
    try:
        offset = value.utcoffset()
        normalized = value.astimezone(timezone.utc)
    except Exception:
        offset = None
    if offset is None:
        _invalid(field_name)
    return normalized


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Handshake IAM value is invalid.",
        details={
            "component": "logical_connection",
            "field": field_name,
        },
    )


__all__ = (
    "DeterministicTestIamAdapter",
    "FailClosedHandshakeIamAdapter",
    "HandshakeIamAdapter",
    "HandshakeIamAuthority",
    "HandshakeIamRequest",
    "TestIamAction",
    "TestIamOutcome",
)
