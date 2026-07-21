# -*- coding: utf-8 -*-
"""Message authorization boundary without implementing the P07 pipeline."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum
from typing import Awaitable, Callable

from ns_common.exceptions import (
    NsRuntimeIamDeniedError,
    NsRuntimeIamUnavailableError,
    NsValidationError,
)
from ns_common.iam import IamAccessCheckRequest, IamAccessDecision, PermissionInvalidation
from ns_common.time import Clock

from .client import IamClient
from .models import PermissionSnapshot


class AuthorizationMode(str, Enum):
    STRICT = "strict"
    CACHE = "cache"


@dataclass(frozen=True, slots=True, kw_only=True)
class OperationRiskContext:
    high_risk_control: bool = False
    cross_tenant: bool = False
    new_configuration: bool = False
    global_coordination_write: bool = False

    def __post_init__(self) -> None:
        if any(not isinstance(value, bool) for value in (
            self.high_risk_control,
            self.cross_tenant,
            self.new_configuration,
            self.global_coordination_write,
        )):
            _invalid("risk_context")

    @property
    def requires_backend_authority(self) -> bool:
        return any((
            self.high_risk_control,
            self.cross_tenant,
            self.new_configuration,
            self.global_coordination_write,
        ))


class BackendUnavailablePolicy:
    """Only a current, previously allowed low-risk decision may degrade."""

    def decide(
        self,
        *,
        cached_decision: IamAccessDecision | None,
        snapshot_current: bool,
        risk: OperationRiskContext,
    ) -> IamAccessDecision:
        if (
            risk.requires_backend_authority
            or not snapshot_current
            or cached_decision is None
            or not cached_decision.allowed
        ):
            raise NsRuntimeIamDeniedError(
                details={
                    "component": "runtime_authorization",
                    "operation": "backend_unavailable",
                    "reason": "authoritative_check_required",
                },
            )
        return cached_decision


SnapshotRefresher = Callable[[PermissionSnapshot], Awaitable[PermissionSnapshot]]


class MessageAuthorizationService:
    """Perform tenant hard check, then permission check, before any processor."""

    def __init__(
        self,
        *,
        iam_client: IamClient,
        clock: Clock,
        mode: AuthorizationMode,
        cache_ttl_seconds: float,
        snapshot_refresher: SnapshotRefresher | None = None,
        unavailable_policy: BackendUnavailablePolicy | None = None,
    ) -> None:
        if not isinstance(iam_client, IamClient):
            _invalid("iam_client")
        if not isinstance(clock, Clock):
            _invalid("clock")
        if not isinstance(mode, AuthorizationMode):
            _invalid("mode")
        if (
            isinstance(cache_ttl_seconds, bool)
            or not isinstance(cache_ttl_seconds, (int, float))
            or float(cache_ttl_seconds) <= 0
        ):
            _invalid("cache_ttl_seconds")
        if snapshot_refresher is not None and not callable(snapshot_refresher):
            _invalid("snapshot_refresher")
        self._iam = iam_client
        self._clock = clock
        self._mode = mode
        self._ttl = float(cache_ttl_seconds)
        self._refresher = snapshot_refresher
        self._unavailable = unavailable_policy or BackendUnavailablePolicy()
        self._decisions: dict[tuple[object, ...], tuple[IamAccessDecision, float]] = {}
        self._invalidations: dict[str, PermissionInvalidation] = {}
        self._lock = asyncio.Lock()

    def invalidate(self, event: PermissionInvalidation) -> None:
        if not isinstance(event, PermissionInvalidation):
            _invalid("invalidation")
        self._invalidations[event.permission_snapshot_ref] = event
        for key in tuple(self._decisions):
            if key[0] == event.permission_snapshot_ref:
                del self._decisions[key]

    async def authorize(
        self,
        *,
        snapshot: PermissionSnapshot,
        request: IamAccessCheckRequest,
        risk: OperationRiskContext,
    ) -> tuple[PermissionSnapshot, IamAccessDecision]:
        if not isinstance(snapshot, PermissionSnapshot):
            _invalid("snapshot")
        if not isinstance(request, IamAccessCheckRequest):
            _invalid("request")
        if not isinstance(risk, OperationRiskContext):
            _invalid("risk")
        self._tenant_hard_check(snapshot=snapshot, request=request)
        effective_risk = OperationRiskContext(
            high_risk_control=(risk.high_risk_control or request.management),
            cross_tenant=(risk.cross_tenant or request.cross_tenant),
            new_configuration=(
                risk.new_configuration or request.message_type.startswith("config.")
            ),
            global_coordination_write=(
                risk.global_coordination_write
                or request.message_type.startswith("cluster.")
            ),
        )
        effective = await self._refresh_if_invalidated(snapshot)
        if effective.permission_version != request.permission_version:
            request = replace(
                request,
                permission_snapshot_ref=effective.permission_snapshot_ref,
                permission_version=effective.permission_version,
            )
        now = self._clock.utc_now()
        if not effective.is_current(now):
            raise _denied("stale_permission_snapshot")
        if request.permission_version != effective.permission_version:
            raise _denied("permission_version_mismatch")
        key = self._cache_key(effective, request)
        cached = self._current_cached(key)
        if (
            self._mode is AuthorizationMode.CACHE
            and cached is not None
            and not effective_risk.requires_backend_authority
        ):
            return effective, self._require_allow(cached)
        try:
            decision = await self._iam.access_check(request)
        except NsRuntimeIamUnavailableError:
            if self._mode is AuthorizationMode.STRICT:
                raise
            degraded = self._unavailable.decide(
                cached_decision=cached,
                snapshot_current=effective.is_current(now),
                risk=effective_risk,
            )
            return effective, degraded
        if decision.permission_version != effective.permission_version:
            self._drop_snapshot_decisions(effective.permission_snapshot_ref)
            raise _denied("permission_version_changed")
        if decision.refresh_required:
            self._drop_snapshot_decisions(effective.permission_snapshot_ref)
            raise _denied("permission_refresh_required")
        if self._mode is AuthorizationMode.CACHE:
            async with self._lock:
                self._decisions[key] = (decision, self._clock.monotonic())
        return effective, self._require_allow(decision)

    async def _refresh_if_invalidated(
        self,
        snapshot: PermissionSnapshot,
    ) -> PermissionSnapshot:
        event = self._invalidations.get(snapshot.permission_snapshot_ref)
        if event is None or event.current_version == snapshot.permission_version:
            return snapshot
        if self._refresher is None:
            raise _denied("permission_snapshot_invalidated")
        try:
            refreshed = await self._refresher(snapshot)
        except NsRuntimeIamUnavailableError:
            raise _denied("permission_snapshot_refresh_unavailable") from None
        if (
            refreshed.permission_snapshot_ref != snapshot.permission_snapshot_ref
            or refreshed.permission_version != event.current_version
            or refreshed.identity != snapshot.identity
            or refreshed.tenant_id != snapshot.tenant_id
            or refreshed.component_type != snapshot.component_type
            or not refreshed.capabilities.issubset(snapshot.capabilities)
            or refreshed.expires_at > snapshot.expires_at
            or (refreshed.resume_eligible and not snapshot.resume_eligible)
        ):
            raise _denied("permission_snapshot_refresh_inconsistent")
        self._invalidations.pop(snapshot.permission_snapshot_ref, None)
        self._drop_snapshot_decisions(snapshot.permission_snapshot_ref)
        return refreshed

    @staticmethod
    def _tenant_hard_check(
        *,
        snapshot: PermissionSnapshot,
        request: IamAccessCheckRequest,
    ) -> None:
        if request.identity != snapshot.identity or request.tenant_id != snapshot.tenant_id:
            raise _denied("session_authority_mismatch")
        if (
            request.permission_snapshot_ref != snapshot.permission_snapshot_ref
            or request.permission_version != snapshot.permission_version
        ):
            raise _denied("session_permission_mismatch")
        target_tenant = request.target.tenant_id
        crosses = target_tenant is not None and target_tenant != snapshot.tenant_id
        if crosses != request.cross_tenant:
            raise _denied("tenant_boundary_mismatch")

    def _current_cached(
        self,
        key: tuple[object, ...],
    ) -> IamAccessDecision | None:
        item = self._decisions.get(key)
        if item is None:
            return None
        decision, stored_at = item
        if self._clock.monotonic() - stored_at >= self._ttl:
            del self._decisions[key]
            return None
        return decision

    @staticmethod
    def _cache_key(
        snapshot: PermissionSnapshot,
        request: IamAccessCheckRequest,
    ) -> tuple[object, ...]:
        return (
            snapshot.permission_snapshot_ref,
            snapshot.permission_version,
            request.message_type,
            request.target.kind,
            request.target.tenant_id,
            request.target.reference,
            request.cross_tenant,
            request.management,
            request.task_creation,
        )

    def _drop_snapshot_decisions(self, snapshot_ref: str) -> None:
        for key in tuple(self._decisions):
            if key[0] == snapshot_ref:
                del self._decisions[key]

    @staticmethod
    def _require_allow(decision: IamAccessDecision) -> IamAccessDecision:
        if not decision.allowed:
            raise _denied("permission_denied")
        return decision


def _denied(reason: str) -> NsRuntimeIamDeniedError:
    return NsRuntimeIamDeniedError(
        details={
            "component": "runtime_authorization",
            "operation": "authorize",
            "reason": reason,
        },
    )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Runtime authorization value is invalid.",
        details={"component": "runtime_authorization", "field": field_name},
    )


__all__ = (
    "AuthorizationMode", "BackendUnavailablePolicy",
    "MessageAuthorizationService", "OperationRiskContext", "SnapshotRefresher",
)
