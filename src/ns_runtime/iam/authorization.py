# -*- coding: utf-8 -*-
"""Message authorization boundary without implementing the P07 pipeline."""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import secrets
from abc import ABC, abstractmethod
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
_PRODUCTION_MESSAGE_AUTHORIZATION_ISSUER = object()
_CONTRACT_TEST_MESSAGE_AUTHORIZATION_ISSUER = object()


class ContractTestIamAuthorizationAdapter(ABC):
    """Explicit non-production backend used by authorization contract tests."""

    @abstractmethod
    async def access_check(
        self,
        request: IamAccessCheckRequest,
    ) -> IamAccessDecision:
        raise NotImplementedError


@dataclass(frozen=True, slots=True, kw_only=True, init=False)
class MessageAuthorizationResult:
    """One service-issued result bound to its exact request and snapshots."""

    request: IamAccessCheckRequest
    session_snapshot: PermissionSnapshot
    effective_snapshot: PermissionSnapshot
    decision: IamAccessDecision
    risk: OperationRiskContext
    _service: object
    _signature: bytes

    def __init__(
        self,
        *,
        request: IamAccessCheckRequest,
        session_snapshot: PermissionSnapshot,
        effective_snapshot: PermissionSnapshot,
        decision: IamAccessDecision,
        risk: OperationRiskContext,
        _service: object | None = None,
        _signature: bytes | None = None,
        _construction_token: object | None = None,
    ) -> None:
        if (
            type(self) is not MessageAuthorizationResult
            or type(_service) is not MessageAuthorizationService
            or not isinstance(_signature, bytes)
            or not _service._consume_authorization_result_token(
                _construction_token,
            )
        ):
            _invalid("authorization_result.issuer")
        for name, value in (
            ("request", request),
            ("session_snapshot", session_snapshot),
            ("effective_snapshot", effective_snapshot),
            ("decision", decision),
            ("risk", risk),
            ("_service", _service),
            ("_signature", _signature),
        ):
            object.__setattr__(self, name, value)
        self.__post_init__()

    def __post_init__(self) -> None:
        if not isinstance(self.request, IamAccessCheckRequest):
            _invalid("authorization_result.request")
        if not isinstance(self.session_snapshot, PermissionSnapshot):
            _invalid("authorization_result.session_snapshot")
        if not isinstance(self.effective_snapshot, PermissionSnapshot):
            _invalid("authorization_result.effective_snapshot")
        if not isinstance(self.decision, IamAccessDecision) or not self.decision.allowed:
            _invalid("authorization_result.decision")
        if not isinstance(self.risk, OperationRiskContext):
            _invalid("authorization_result.risk")

    def is_issued_by(self, service: "MessageAuthorizationService") -> bool:
        if type(service) is not MessageAuthorizationService:
            return False
        try:
            expected = service._authorization_result_signature(
                request=self.request,
                session_snapshot=self.session_snapshot,
                effective_snapshot=self.effective_snapshot,
                decision=self.decision,
                risk=self.risk,
            )
        except (AttributeError, NsValidationError):
            return False
        return bool(
            type(self) is MessageAuthorizationResult
            and self._service is service
            and hmac.compare_digest(self._signature, expected)
        )

    def __copy__(self) -> "MessageAuthorizationResult":
        del self
        _invalid("authorization_result.copy")

    def __deepcopy__(self, memo: dict[int, object]) -> "MessageAuthorizationResult":
        del self, memo
        _invalid("authorization_result.copy")


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
        if (
            type(iam_client) is not IamClient
            or not iam_client._is_production_adapter()
        ):
            _invalid("iam_client")
        self._initialize(
            iam_client=iam_client,
            clock=clock,
            mode=mode,
            cache_ttl_seconds=cache_ttl_seconds,
            snapshot_refresher=snapshot_refresher,
            unavailable_policy=unavailable_policy,
            authority_issuer=_PRODUCTION_MESSAGE_AUTHORIZATION_ISSUER,
        )
        iam_client._bind_authorization_service(self)

    @classmethod
    def for_contract_tests(
        cls,
        *,
        iam_client: ContractTestIamAuthorizationAdapter,
        clock: Clock,
        mode: AuthorizationMode,
        cache_ttl_seconds: float,
        snapshot_refresher: SnapshotRefresher | None = None,
        unavailable_policy: BackendUnavailablePolicy | None = None,
    ) -> "MessageAuthorizationService":
        if type(iam_client) is ContractTestIamAuthorizationAdapter or not isinstance(
            iam_client,
            ContractTestIamAuthorizationAdapter,
        ):
            _invalid("test_iam_client")
        value = object.__new__(cls)
        value._initialize(
            iam_client=iam_client,
            clock=clock,
            mode=mode,
            cache_ttl_seconds=cache_ttl_seconds,
            snapshot_refresher=snapshot_refresher,
            unavailable_policy=unavailable_policy,
            authority_issuer=_CONTRACT_TEST_MESSAGE_AUTHORIZATION_ISSUER,
        )
        return value

    def _initialize(
        self,
        *,
        iam_client: object,
        clock: Clock,
        mode: AuthorizationMode,
        cache_ttl_seconds: float,
        snapshot_refresher: SnapshotRefresher | None,
        unavailable_policy: BackendUnavailablePolicy | None,
        authority_issuer: object,
    ) -> None:
        if authority_issuer not in {
            _PRODUCTION_MESSAGE_AUTHORIZATION_ISSUER,
            _CONTRACT_TEST_MESSAGE_AUTHORIZATION_ISSUER,
        }:
            _invalid("authority_issuer")
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
        self._authority_issuer = authority_issuer
        self._authorization_result_key = secrets.token_bytes(32)
        self._pending_authorization_result_token: object | None = None
        self._decisions: dict[tuple[object, ...], tuple[IamAccessDecision, float]] = {}
        self._invalidations: dict[str, PermissionInvalidation] = {}
        self._lock = asyncio.Lock()

    @property
    def production_authority(self) -> bool:
        return self._has_authority(
            _PRODUCTION_MESSAGE_AUTHORIZATION_ISSUER,
        )

    @property
    def contract_test_authority(self) -> bool:
        return self._has_authority(
            _CONTRACT_TEST_MESSAGE_AUTHORIZATION_ISSUER,
        )

    def _has_authority(self, issuer: object) -> bool:
        if (
            type(self) is not MessageAuthorizationService
            or getattr(self, "_authority_issuer", None) is not issuer
            or "authorize" in vars(self)
            or getattr(type(self), "authorize", None)
            is not MessageAuthorizationService.authorize
        ):
            return False
        if issuer is _PRODUCTION_MESSAGE_AUTHORIZATION_ISSUER:
            return bool(
                type(getattr(self, "_iam", None)) is IamClient
                and self._iam._is_production_adapter()
                and self._iam._owns_authorization_service(self)
            )
        return isinstance(
            getattr(self, "_iam", None),
            ContractTestIamAuthorizationAdapter,
        )

    def invalidate(self, event: PermissionInvalidation) -> None:
        if not isinstance(event, PermissionInvalidation):
            _invalid("invalidation")
        self._invalidations[event.permission_snapshot_ref] = event
        for key in tuple(self._decisions):
            if key[0] == event.permission_snapshot_ref:
                del self._decisions[key]

    def __copy__(self) -> "MessageAuthorizationService":
        _invalid("authorization_service.copy")

    def __deepcopy__(
        self,
        memo: dict[int, object],
    ) -> "MessageAuthorizationService":
        del memo
        _invalid("authorization_service.copy")

    async def authorize(
        self,
        *,
        snapshot: PermissionSnapshot,
        request: IamAccessCheckRequest,
        risk: OperationRiskContext,
    ) -> MessageAuthorizationResult:
        if not isinstance(snapshot, PermissionSnapshot):
            _invalid("snapshot")
        if not isinstance(request, IamAccessCheckRequest):
            _invalid("request")
        if not isinstance(risk, OperationRiskContext):
            _invalid("risk")
        if (
            self._authority_issuer is _PRODUCTION_MESSAGE_AUTHORIZATION_ISSUER
            and not self.production_authority
        ):
            _invalid("iam_client")
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
            return self._issue_authorization_result(
                request=request,
                session_snapshot=snapshot,
                effective_snapshot=effective,
                decision=self._require_allow(cached),
                risk=effective_risk,
            )
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
            return self._issue_authorization_result(
                request=request,
                session_snapshot=snapshot,
                effective_snapshot=effective,
                decision=degraded,
                risk=effective_risk,
            )
        if decision.permission_version != effective.permission_version:
            self._drop_snapshot_decisions(effective.permission_snapshot_ref)
            raise _denied("permission_version_changed")
        if decision.refresh_required:
            self._drop_snapshot_decisions(effective.permission_snapshot_ref)
            raise _denied("permission_refresh_required")
        if self._mode is AuthorizationMode.CACHE:
            async with self._lock:
                self._decisions[key] = (decision, self._clock.monotonic())
        return self._issue_authorization_result(
            request=request,
            session_snapshot=snapshot,
            effective_snapshot=effective,
            decision=self._require_allow(decision),
            risk=effective_risk,
        )

    def _issue_authorization_result(
        self,
        *,
        request: IamAccessCheckRequest,
        session_snapshot: PermissionSnapshot,
        effective_snapshot: PermissionSnapshot,
        decision: IamAccessDecision,
        risk: OperationRiskContext,
    ) -> MessageAuthorizationResult:
        signature = self._authorization_result_signature(
            request=request,
            session_snapshot=session_snapshot,
            effective_snapshot=effective_snapshot,
            decision=decision,
            risk=risk,
        )
        token = object()
        self._pending_authorization_result_token = token
        try:
            return MessageAuthorizationResult(
                request=request,
                session_snapshot=session_snapshot,
                effective_snapshot=effective_snapshot,
                decision=decision,
                risk=risk,
                _service=self,
                _signature=signature,
                _construction_token=token,
            )
        finally:
            self._pending_authorization_result_token = None

    def _consume_authorization_result_token(self, token: object) -> bool:
        return (
            token is not None
            and self._pending_authorization_result_token is token
        )

    def _authorization_result_signature(
        self,
        *,
        request: IamAccessCheckRequest,
        session_snapshot: PermissionSnapshot,
        effective_snapshot: PermissionSnapshot,
        decision: IamAccessDecision,
        risk: OperationRiskContext,
    ) -> bytes:
        if not self._has_authority(getattr(self, "_authority_issuer", None)):
            _invalid("authorization_result.service")
        payload = json.dumps({
            "request": request.to_wire(),
            "session_snapshot": _snapshot_binding(session_snapshot),
            "effective_snapshot": _snapshot_binding(effective_snapshot),
            "decision": decision.to_wire(),
            "risk": {
                "high_risk_control": risk.high_risk_control,
                "cross_tenant": risk.cross_tenant,
                "new_configuration": risk.new_configuration,
                "global_coordination_write": risk.global_coordination_write,
            },
        }, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hmac.new(
            self._authorization_result_key,
            payload,
            hashlib.sha256,
        ).digest()

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


def _snapshot_binding(snapshot: PermissionSnapshot) -> dict[str, object]:
    if not isinstance(snapshot, PermissionSnapshot):
        _invalid("authorization_result.snapshot")
    return {
        "identity": snapshot.identity,
        "tenant_id": snapshot.tenant_id,
        "principal_type": snapshot.principal_type.value,
        "component_type": snapshot.component_type,
        "capabilities": sorted(snapshot.capabilities),
        "permission_snapshot_ref": snapshot.permission_snapshot_ref,
        "permission_digest": snapshot.permission_digest,
        "permission_version": snapshot.permission_version,
        "iam_mode": snapshot.iam_mode,
        "issued_at": snapshot.issued_at.isoformat(),
        "expires_at": snapshot.expires_at.isoformat(),
        "resume_eligible": snapshot.resume_eligible,
    }


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Runtime authorization value is invalid.",
        details={"component": "runtime_authorization", "field": field_name},
    )


__all__ = (
    "AuthorizationMode", "BackendUnavailablePolicy",
    "ContractTestIamAuthorizationAdapter",
    "MessageAuthorizationResult", "MessageAuthorizationService",
    "OperationRiskContext", "SnapshotRefresher",
)
