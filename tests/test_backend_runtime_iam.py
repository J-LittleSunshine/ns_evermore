# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import unittest

from ns_common.exceptions import NsValidationError
from ns_common.iam import (
    IamAccessCheckRequest,
    IamAccessDecision,
    IamCredentialStatus,
    IamIntrospectionRequest,
    IamPrincipalType,
    IamTargetContext,
    PayloadRefValidationRequest,
    PayloadRefValidationResult,
    PermissionInvalidation,
    RuntimeBootstrapRequest,
    RuntimeRoleScope,
)
from ns_common.time import ControlledClock
from ns_backend.iam.runtime_contracts import (
    BackendRuntimeIamService,
    InMemoryRuntimeCredentialStatusStore,
    PermissionInvalidationLedger,
    ResolvedPrincipal,
    RuntimeBootstrapPolicy,
    RuntimeNodeCredentialAuthority,
)


NOW = datetime(2026, 7, 21, tzinfo=timezone.utc)


class _Resolver:
    def __init__(self, principals: dict[str, ResolvedPrincipal]) -> None:
        self.principals = principals

    async def resolve(self, token: str) -> ResolvedPrincipal | None:
        return self.principals.get(token)


class _PermissionPolicy:
    def __init__(self, clock: ControlledClock) -> None:
        self.clock = clock
        self.requests: list[IamAccessCheckRequest] = []

    async def decide(self, request: IamAccessCheckRequest) -> IamAccessDecision:
        self.requests.append(request)
        return IamAccessDecision(
            allowed=not request.management,
            reason="allowed" if not request.management else "management_denied",
            permission_version=request.permission_version,
            decided_at=self.clock.utc_now(),
        )


class _PayloadPolicy:
    def __init__(self, clock: ControlledClock) -> None:
        self.clock = clock
        self.requests: list[PayloadRefValidationRequest] = []

    async def validate(
        self,
        request: PayloadRefValidationRequest,
    ) -> PayloadRefValidationResult:
        self.requests.append(request)
        return PayloadRefValidationResult(
            valid=request.object_id == "object:1",
            reason="valid" if request.object_id == "object:1" else "object_unknown",
            expires_at=self.clock.utc_now() + timedelta(minutes=5),
            revoked=False,
            object_id=request.object_id if request.object_id == "object:1" else None,
            version=request.version if request.object_id == "object:1" else None,
            checksum=request.checksum if request.object_id == "object:1" else None,
            tenant_id=request.tenant_id if request.object_id == "object:1" else None,
            size_bytes=123 if request.object_id == "object:1" else None,
        )


def _principal(principal_type: IamPrincipalType) -> ResolvedPrincipal:
    return ResolvedPrincipal(
        identity=f"identity:{principal_type.value}",
        tenant_id="tenant:1",
        principal_type=principal_type,
        component_type=(
            "runtime" if principal_type is IamPrincipalType.RUNTIME_NODE
            else principal_type.value
        ),
        allowed_capabilities=frozenset({"runtime.connection", "runtime.heartbeat"}),
        permission_snapshot_ref=f"permission:{principal_type.value}",
        permission_digest="sha256:1234",
        permission_version="version:1",
        issued_at=NOW,
        expires_at=NOW + timedelta(minutes=10),
        credential_status=IamCredentialStatus.ACTIVE,
        resume_eligible=True,
    )


class BackendRuntimeIamContractTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.clock = ControlledClock(utc_start=NOW)
        self.principals = {
            f"token-{item.value}": _principal(item)
            for item in IamPrincipalType
        }
        self.permissions = _PermissionPolicy(self.clock)
        self.payloads = _PayloadPolicy(self.clock)
        self.service = BackendRuntimeIamService(
            principal_resolver=_Resolver(self.principals),
            permission_policy=self.permissions,
            payload_ref_policy=self.payloads,
            clock=self.clock,
        )

    async def test_all_principal_types_have_the_same_complete_contract(self) -> None:
        self.assertEqual(6, len(IamPrincipalType))
        for principal_type in IamPrincipalType:
            with self.subTest(principal_type=principal_type.value):
                resolved = self.principals[f"token-{principal_type.value}"]
                result = await self.service.introspect(IamIntrospectionRequest(
                    token=f"token-{principal_type.value}",
                    component_type=resolved.component_type,
                    requested_capabilities=frozenset({"runtime.connection"}),
                    protocol_version="1.0.0",
                ))
                self.assertIsNotNone(result)
                assert result is not None
                self.assertEqual(principal_type, result.principal_type)
                self.assertEqual(IamCredentialStatus.ACTIVE, result.credential_status)
                self.assertEqual(
                    {
                        "identity", "tenant_id", "principal_type", "component_type",
                        "capabilities", "permission_snapshot_ref", "permission_digest",
                        "permission_version", "issued_at", "expires_at",
                        "credential_status", "resume_eligible",
                    },
                    set(result.to_wire()),
                )

    async def test_invalid_expired_revoked_and_hostile_claims_fail_closed(self) -> None:
        self.assertIsNone(await self.service.introspect(IamIntrospectionRequest(
            token="invalid-token",
            component_type="client",
            requested_capabilities=frozenset({"runtime.connection"}),
            protocol_version="1.0.0",
        )))
        base = self.principals["token-client"]
        self.principals["expired"] = replace(
            base,
            issued_at=NOW - timedelta(minutes=20),
            expires_at=NOW - timedelta(minutes=1),
        )
        expired = await self.service.introspect(IamIntrospectionRequest(
            token="expired",
            component_type="client",
            requested_capabilities=frozenset({"runtime.connection"}),
            protocol_version="1.0.0",
        ))
        self.assertEqual(IamCredentialStatus.EXPIRED, expired.credential_status)  # type: ignore[union-attr]
        self.principals["revoked"] = replace(
            base,
            credential_status=IamCredentialStatus.REVOKED,
        )
        revoked = await self.service.introspect(IamIntrospectionRequest(
            token="revoked",
            component_type="client",
            requested_capabilities=frozenset({"runtime.connection"}),
            protocol_version="1.0.0",
        ))
        self.assertEqual(IamCredentialStatus.REVOKED, revoked.credential_status)  # type: ignore[union-attr]
        self.assertIsNone(await self.service.introspect(IamIntrospectionRequest(
            token="token-client",
            component_type="management",
            requested_capabilities=frozenset({"runtime.connection"}),
            protocol_version="1.0.0",
        )))
        self.assertIsNone(await self.service.introspect(IamIntrospectionRequest(
            token="token-client",
            component_type="client",
            requested_capabilities=frozenset({"runtime.management"}),
            protocol_version="1.0.0",
        )))

    async def test_access_and_payload_ref_contracts_preserve_security_context(self) -> None:
        access = IamAccessCheckRequest(
            identity="identity:client",
            tenant_id="tenant:1",
            permission_snapshot_ref="permission:client",
            permission_version="version:1",
            message_type="task.dispatch",
            target=IamTargetContext(
                kind="tenant",
                tenant_id="tenant:2",
                reference="target:2",
            ),
            cross_tenant=True,
            management=False,
            task_creation=True,
        )
        decision = await self.service.access_check(access)
        self.assertTrue(decision.allowed)
        self.assertIs(access, self.permissions.requests[0])
        hostile = replace(access, cross_tenant=False)
        denied = await self.service.access_check(hostile)
        self.assertFalse(denied.allowed)
        self.assertEqual("cross_tenant_context_mismatch", denied.reason)
        self.assertEqual(1, len(self.permissions.requests))
        payload = PayloadRefValidationRequest(
            object_id="object:1",
            version="version:7",
            checksum="sha256:abcd",
            tenant_id="tenant:1",
            owner_identity="identity:client",
            source_identity="identity:client",
            target=access.target,
            callback_message_type="task.result",
        )
        result = await self.service.validate_payload_ref(payload)
        self.assertTrue(result.valid)
        self.assertIs(payload, self.payloads.requests[0])

    async def test_node_credential_issue_refresh_revoke_and_bootstrap_role_scope(self) -> None:
        store = InMemoryRuntimeCredentialStatusStore()
        authority = RuntimeNodeCredentialAuthority(
            signing_key=b"s" * 32,
            status_store=store,
            clock=self.clock,
            credential_id_factory=iter(("credential:1", "credential:2")).__next__,
            ttl_seconds=60,
        )
        issued = await authority.issue(
            identity="runtime:1",
            tenant_id="tenant:system",
            roles=frozenset({RuntimeRoleScope.SUB_NODE}),
            capabilities=frozenset({"runtime.connection"}),
        )
        self.assertTrue(issued.token.startswith("nsrn1."))
        self.assertNotIn("access", issued.token[:6])
        self.assertEqual(issued, await authority.verify(issued.token))
        policy = RuntimeBootstrapPolicy(
            config_version="config:7",
            policy_version="policy:9",
        )
        allowed = policy.authorize(
            RuntimeBootstrapRequest(
                runtime_id="runtime:1",
                requested_role=RuntimeRoleScope.SUB_NODE,
                credential_id=issued.credential_id,
            ),
            credential=issued,
        )
        self.assertTrue(allowed.role_authorized)
        self.assertFalse(allowed.candidate_master)
        with self.assertRaises(NsValidationError):
            await authority.refresh(replace(
                issued,
                credential_id="credential:other",
            ))
        self.assertIsNotNone(await authority.verify(issued.token))
        refreshed = await authority.refresh(issued)
        self.assertIsNone(await authority.verify(issued.token))
        self.assertIsNotNone(await authority.verify(refreshed.token))
        await authority.revoke(refreshed.credential_id)
        self.assertIsNone(await authority.verify(refreshed.token))

    async def test_permission_invalidation_polling_contract(self) -> None:
        ledger = PermissionInvalidationLedger()
        event = PermissionInvalidation(
            permission_snapshot_ref="permission:client",
            previous_version="version:1",
            current_version="version:2",
            invalidated_at=NOW,
            reason="role_changed",
        )
        ledger.publish(event)
        self.assertIs(event, ledger.poll("permission:client", "version:1"))
        self.assertIsNone(ledger.poll("permission:client", "version:2"))


if __name__ == "__main__":
    unittest.main()
