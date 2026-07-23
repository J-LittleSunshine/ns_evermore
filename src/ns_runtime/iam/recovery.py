# -*- coding: utf-8 -*-
"""Backend recovery revalidation contract; no lease or fencing implementation."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from ns_common.exceptions import NsRuntimeIamDeniedError, NsStateError, NsValidationError


class BackendRecoveryState(str, Enum):
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    REVALIDATING = "revalidating"


@dataclass(frozen=True, slots=True, kw_only=True)
class RecoveryRevalidationResult:
    credential_valid: bool
    role_valid: bool
    config_valid: bool
    lease_valid: bool
    fencing_valid: bool
    session_snapshot_valid: bool

    def __post_init__(self) -> None:
        if any(not isinstance(value, bool) for value in (
            self.credential_valid,
            self.role_valid,
            self.config_valid,
            self.lease_valid,
            self.fencing_valid,
            self.session_snapshot_valid,
        )):
            _invalid("result")

    @property
    def fully_valid(self) -> bool:
        return all((
            self.credential_valid,
            self.role_valid,
            self.config_valid,
            self.lease_valid,
            self.fencing_valid,
            self.session_snapshot_valid,
        ))


class RecoveryRevalidator(Protocol):
    async def revalidate(self) -> RecoveryRevalidationResult: ...


class BackendRecoveryCoordinator:
    """Require fresh evidence after recovery; old authorization is never inherited."""

    def __init__(self, *, revalidator: RecoveryRevalidator) -> None:
        if not callable(getattr(revalidator, "revalidate", None)):
            _invalid("revalidator")
        self._revalidator = revalidator
        self._state = BackendRecoveryState.AVAILABLE
        self._generation = 0
        self._outage_generation = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> BackendRecoveryState:
        return self._state

    @property
    def authorization_generation(self) -> int:
        return self._generation

    def mark_unavailable(self) -> None:
        self._outage_generation += 1
        self._state = BackendRecoveryState.UNAVAILABLE

    async def recover(self) -> RecoveryRevalidationResult:
        async with self._lock:
            if self._state is not BackendRecoveryState.UNAVAILABLE:
                raise NsStateError(
                    "Backend recovery requires an unavailable state.",
                    details={
                        "component": "runtime_backend_recovery",
                        "operation": "recover",
                        "state": self._state.value,
                    },
                )
            recovery_generation = self._outage_generation
            self._state = BackendRecoveryState.REVALIDATING
            try:
                result = await self._revalidator.revalidate()
            except BaseException:
                self._state = BackendRecoveryState.UNAVAILABLE
                raise
            if not isinstance(result, RecoveryRevalidationResult):
                self._state = BackendRecoveryState.UNAVAILABLE
                _invalid("revalidation_result")
            if recovery_generation != self._outage_generation:
                self._state = BackendRecoveryState.UNAVAILABLE
                raise NsRuntimeIamDeniedError(
                    details={
                        "component": "runtime_backend_recovery",
                        "operation": "recover",
                        "reason": "backend_became_unavailable",
                    },
                )
            if not result.fully_valid:
                self._state = BackendRecoveryState.UNAVAILABLE
                raise NsRuntimeIamDeniedError(
                    details={
                        "component": "runtime_backend_recovery",
                        "operation": "recover",
                        "reason": "revalidation_failed",
                    },
                )
            self._generation += 1
            self._state = BackendRecoveryState.AVAILABLE
            return result


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Runtime backend recovery value is invalid.",
        details={"component": "runtime_backend_recovery", "field": field_name},
    )


__all__ = (
    "BackendRecoveryCoordinator", "BackendRecoveryState",
    "RecoveryRevalidationResult", "RecoveryRevalidator",
)
