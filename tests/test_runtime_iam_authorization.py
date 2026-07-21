# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from ns_common.exceptions import NsRuntimeIamDeniedError, NsRuntimeIamUnavailableError
from ns_common.iam import (
    IamAccessCheckRequest,
    IamAccessDecision,
    IamCredentialStatus,
    IamIntrospectionResult,
    IamPrincipalType,
    IamTargetContext,
    PermissionInvalidation,
)
from ns_common.time import ControlledClock
from ns_runtime.iam import (
    AuthorizationMode,
    BackendUnavailablePolicy,
    MessageAuthorizationService,
    OperationRiskContext,
    PermissionSnapshot,
)
from ns_runtime.iam.client import IamClient


NOW = datetime(2026, 7, 21, tzinfo=timezone.utc)


class _Iam(IamClient):
    def __init__(self, outcomes: list[object], clock: ControlledClock) -> None:
        self.outcomes = outcomes
        self.clock = clock
        self.requests: list[IamAccessCheckRequest] = []

    async def access_check(self, request: IamAccessCheckRequest) -> IamAccessDecision:
        self.requests.append(request)
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, Exception):
            raise outcome
        if isinstance(outcome, IamAccessDecision):
            return outcome
        return IamAccessDecision(
            allowed=bool(outcome),
            reason="allowed" if outcome else "denied",
            permission_version=request.permission_version,
            decided_at=self.clock.utc_now(),
        )


def _snapshot(**changes: object) -> PermissionSnapshot:
    values: dict[str, object] = {
        "identity": "identity:1",
        "tenant_id": "tenant:1",
        "principal_type": IamPrincipalType.CLIENT,
        "component_type": "client",
        "capabilities": frozenset({"runtime.connection"}),
        "permission_snapshot_ref": "permission:1",
        "permission_digest": "sha256:1",
        "permission_version": "version:1",
        "issued_at": NOW,
        "expires_at": NOW + timedelta(minutes=5),
        "credential_status": IamCredentialStatus.ACTIVE,
        "resume_eligible": True,
    }
    values.update(changes)
    return PermissionSnapshot.from_introspection(
        IamIntrospectionResult(**values),  # type: ignore[arg-type]
        iam_mode="cache",
    )


def _request(**changes: object) -> IamAccessCheckRequest:
    values: dict[str, object] = {
        "identity": "identity:1",
        "tenant_id": "tenant:1",
        "permission_snapshot_ref": "permission:1",
        "permission_version": "version:1",
        "message_type": "connection.heartbeat",
        "target": IamTargetContext(kind="identity", tenant_id="tenant:1"),
    }
    values.update(changes)
    return IamAccessCheckRequest(**values)  # type: ignore[arg-type]


class RuntimeAuthorizationTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_strict_mode_calls_backend_for_every_message(self) -> None:
        clock = ControlledClock(utc_start=NOW)
        iam = _Iam([True, True], clock)
        service = MessageAuthorizationService(
            iam_client=iam,
            clock=clock,
            mode=AuthorizationMode.STRICT,
            cache_ttl_seconds=60,
        )
        for _ in range(2):
            _, decision = await service.authorize(
                snapshot=_snapshot(),
                request=_request(),
                risk=OperationRiskContext(),
            )
            self.assertTrue(decision.allowed)
        self.assertEqual(2, len(iam.requests))

    async def test_cache_mode_honors_ttl_and_rechecks_after_expiry(self) -> None:
        clock = ControlledClock(utc_start=NOW)
        iam = _Iam([True, True], clock)
        service = MessageAuthorizationService(
            iam_client=iam,
            clock=clock,
            mode=AuthorizationMode.CACHE,
            cache_ttl_seconds=5,
        )
        for _ in range(2):
            await service.authorize(
                snapshot=_snapshot(),
                request=_request(),
                risk=OperationRiskContext(),
            )
        self.assertEqual(1, len(iam.requests))
        clock.advance(5)
        await service.authorize(
            snapshot=_snapshot(),
            request=_request(),
            risk=OperationRiskContext(),
        )
        self.assertEqual(2, len(iam.requests))

    async def test_invalidation_refreshes_version_and_drops_old_decisions(self) -> None:
        clock = ControlledClock(utc_start=NOW)
        iam = _Iam([True, True], clock)
        refreshed = _snapshot(
            permission_version="version:2",
            permission_digest="sha256:2",
            issued_at=NOW,
            expires_at=NOW + timedelta(minutes=5),
        )
        refresh_calls: list[PermissionSnapshot] = []

        async def refresh(snapshot: PermissionSnapshot) -> PermissionSnapshot:
            refresh_calls.append(snapshot)
            return refreshed

        service = MessageAuthorizationService(
            iam_client=iam,
            clock=clock,
            mode=AuthorizationMode.CACHE,
            cache_ttl_seconds=60,
            snapshot_refresher=refresh,
        )
        await service.authorize(
            snapshot=_snapshot(),
            request=_request(management=True),
            risk=OperationRiskContext(high_risk_control=True),
        )
        service.invalidate(PermissionInvalidation(
            permission_snapshot_ref="permission:1",
            previous_version="version:1",
            current_version="version:2",
            invalidated_at=NOW,
            reason="role_changed",
        ))
        effective, _ = await service.authorize(
            snapshot=_snapshot(), request=_request(), risk=OperationRiskContext(),
        )
        self.assertEqual("version:2", effective.permission_version)
        self.assertEqual("version:2", iam.requests[-1].permission_version)
        self.assertEqual(1, len(refresh_calls))
        self.assertEqual(2, len(iam.requests))

    async def test_stale_snapshot_and_tenant_tampering_are_rejected_before_backend(self) -> None:
        clock = ControlledClock(utc_start=NOW)
        iam = _Iam([True, True], clock)
        service = MessageAuthorizationService(
            iam_client=iam,
            clock=clock,
            mode=AuthorizationMode.STRICT,
            cache_ttl_seconds=60,
        )
        stale = _snapshot(
            issued_at=NOW - timedelta(minutes=10),
            expires_at=NOW - timedelta(minutes=1),
        )
        with self.assertRaises(NsRuntimeIamDeniedError):
            await service.authorize(
                snapshot=stale, request=_request(), risk=OperationRiskContext(),
            )
        with self.assertRaises(NsRuntimeIamDeniedError):
            await service.authorize(
                snapshot=_snapshot(),
                request=_request(tenant_id="tenant:attacker"),
                risk=OperationRiskContext(),
            )
        with self.assertRaises(NsRuntimeIamDeniedError):
            await service.authorize(
                snapshot=_snapshot(),
                request=_request(target=IamTargetContext(
                    kind="tenant", tenant_id="tenant:2",
                )),
                risk=OperationRiskContext(),
            )
        self.assertEqual([], iam.requests)

    async def test_permission_version_change_is_not_silently_cached(self) -> None:
        clock = ControlledClock(utc_start=NOW)
        iam = _Iam([IamAccessDecision(
            allowed=True,
            reason="allowed",
            permission_version="version:2",
            decided_at=NOW,
        )], clock)
        service = MessageAuthorizationService(
            iam_client=iam,
            clock=clock,
            mode=AuthorizationMode.CACHE,
            cache_ttl_seconds=60,
        )
        with self.assertRaises(NsRuntimeIamDeniedError):
            await service.authorize(
                snapshot=_snapshot(), request=_request(), risk=OperationRiskContext(),
            )

    async def test_backend_unavailable_matrix_rejects_all_authoritative_operations(self) -> None:
        policy = BackendUnavailablePolicy()
        cached = IamAccessDecision(
            allowed=True,
            reason="cached_allow",
            permission_version="version:1",
            decided_at=NOW,
        )
        self.assertIs(cached, policy.decide(
            cached_decision=cached,
            snapshot_current=True,
            risk=OperationRiskContext(),
        ))
        risks = (
            OperationRiskContext(high_risk_control=True),
            OperationRiskContext(cross_tenant=True),
            OperationRiskContext(new_configuration=True),
            OperationRiskContext(global_coordination_write=True),
        )
        for risk in risks:
            with self.subTest(risk=risk):
                with self.assertRaises(NsRuntimeIamDeniedError):
                    policy.decide(
                        cached_decision=cached,
                        snapshot_current=True,
                        risk=risk,
                    )

        clock = ControlledClock(utc_start=NOW)
        unavailable = NsRuntimeIamUnavailableError(details={"reason": "test"})
        iam = _Iam([True, unavailable], clock)
        service = MessageAuthorizationService(
            iam_client=iam,
            clock=clock,
            mode=AuthorizationMode.CACHE,
            cache_ttl_seconds=60,
        )
        await service.authorize(
            snapshot=_snapshot(), request=_request(), risk=OperationRiskContext(),
        )
        with self.assertRaises(NsRuntimeIamDeniedError):
            await service.authorize(
                snapshot=_snapshot(),
                request=_request(management=True),
                risk=OperationRiskContext(high_risk_control=True),
            )
        self.assertEqual(2, len(iam.requests))


if __name__ == "__main__":
    unittest.main()
