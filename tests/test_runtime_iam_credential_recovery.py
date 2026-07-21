# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime, timezone
import unittest

from ns_common.exceptions import NsRuntimeIamDeniedError
from ns_common.iam import RuntimeRoleScope
from ns_common.time import ControlledClock
from ns_backend.iam.runtime_contracts import (
    InMemoryRuntimeCredentialStatusStore,
    RuntimeNodeCredentialAuthority,
)
from ns_runtime.iam import (
    BackendRecoveryCoordinator,
    BackendRecoveryState,
    EncryptedCredentialCache,
    RecoveryRevalidationResult,
    RuntimeNodeCredentialVerifier,
)


NOW = datetime(2026, 7, 21, tzinfo=timezone.utc)


class _Revalidator:
    def __init__(self, outcomes: list[RecoveryRevalidationResult]) -> None:
        self.outcomes = outcomes
        self.calls = 0
        self.on_call = None

    async def revalidate(self) -> RecoveryRevalidationResult:
        self.calls += 1
        if self.on_call is not None:
            self.on_call()
        return self.outcomes.pop(0)


def _revalidation(**changes: bool) -> RecoveryRevalidationResult:
    values = {
        "credential_valid": True,
        "role_valid": True,
        "config_valid": True,
        "lease_valid": True,
        "fencing_valid": True,
        "session_snapshot_valid": True,
    }
    values.update(changes)
    return RecoveryRevalidationResult(**values)


class RuntimeCredentialCacheTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.clock = ControlledClock(utc_start=NOW)
        self.signing_key = b"signature-key-material-32-bytes!!"
        self.authority = RuntimeNodeCredentialAuthority(
            signing_key=self.signing_key,
            status_store=InMemoryRuntimeCredentialStatusStore(),
            clock=self.clock,
            credential_id_factory=lambda: "credential:cache1",
            ttl_seconds=30,
        )
        self.credential = await self.authority.issue(
            identity="runtime:1",
            tenant_id="tenant:system",
            roles=frozenset({RuntimeRoleScope.SUB_NODE}),
            capabilities=frozenset({"runtime.connection"}),
        )

    def _cache(self) -> EncryptedCredentialCache:
        return EncryptedCredentialCache(
            encryption_key=b"e" * 32,
            verifier=RuntimeNodeCredentialVerifier(
                signing_key=self.signing_key,
                clock=self.clock,
            ),
            clock=self.clock,
            ttl_seconds=10,
            nonce_factory=lambda size: b"n" * size,
        )

    def test_cache_retains_ciphertext_not_plaintext_and_checks_role(self) -> None:
        cache = self._cache()
        claims = cache.put(
            self.credential.token,
            required_role=RuntimeRoleScope.SUB_NODE,
        )
        encrypted = cache._entries[claims.credential_id].ciphertext  # noqa: SLF001
        self.assertNotIn(self.credential.token.encode(), encrypted)
        self.assertNotIn(self.credential.token, repr(cache))
        self.assertEqual(
            self.credential.token,
            cache.get(
                claims.credential_id,
                required_role=RuntimeRoleScope.SUB_NODE,
            ),
        )
        with self.assertRaises(NsRuntimeIamDeniedError):
            cache.get(
                claims.credential_id,
                required_role=RuntimeRoleScope.ACTIVE_MASTER,
            )

    def test_signature_tamper_ciphertext_tamper_ttl_and_revoke_fail_closed(self) -> None:
        cache = self._cache()
        tampered_token = self.credential.token[:-1] + (
            "A" if self.credential.token[-1] != "A" else "B"
        )
        with self.assertRaises(NsRuntimeIamDeniedError):
            cache.put(tampered_token, required_role=RuntimeRoleScope.SUB_NODE)
        claims = cache.put(
            self.credential.token,
            required_role=RuntimeRoleScope.SUB_NODE,
        )
        entry = cache._entries[claims.credential_id]  # noqa: SLF001
        entry.ciphertext = entry.ciphertext[:-1] + bytes([entry.ciphertext[-1] ^ 1])
        with self.assertRaises(NsRuntimeIamDeniedError):
            cache.get(claims.credential_id, required_role=RuntimeRoleScope.SUB_NODE)
        cache.put(self.credential.token, required_role=RuntimeRoleScope.SUB_NODE)
        self.clock.advance(10)
        with self.assertRaises(NsRuntimeIamDeniedError):
            cache.get(claims.credential_id, required_role=RuntimeRoleScope.SUB_NODE)
        cache.put(self.credential.token, required_role=RuntimeRoleScope.SUB_NODE)
        cache.revoke(claims.credential_id)
        with self.assertRaises(NsRuntimeIamDeniedError):
            cache.get(claims.credential_id, required_role=RuntimeRoleScope.SUB_NODE)


class BackendRecoveryTestCase(unittest.IsolatedAsyncioTestCase):
    async def test_recovery_requires_all_fresh_evidence_and_new_generation(self) -> None:
        revalidator = _Revalidator([
            _revalidation(lease_valid=False),
            _revalidation(),
        ])
        coordinator = BackendRecoveryCoordinator(revalidator=revalidator)
        coordinator.mark_unavailable()
        with self.assertRaises(NsRuntimeIamDeniedError):
            await coordinator.recover()
        self.assertEqual(BackendRecoveryState.UNAVAILABLE, coordinator.state)
        self.assertEqual(0, coordinator.authorization_generation)
        result = await coordinator.recover()
        self.assertTrue(result.fully_valid)
        self.assertEqual(BackendRecoveryState.AVAILABLE, coordinator.state)
        self.assertEqual(1, coordinator.authorization_generation)
        self.assertEqual(2, revalidator.calls)

        racing = _Revalidator([_revalidation(), _revalidation()])
        raced_coordinator = BackendRecoveryCoordinator(revalidator=racing)
        raced_coordinator.mark_unavailable()
        racing.on_call = raced_coordinator.mark_unavailable
        with self.assertRaises(NsRuntimeIamDeniedError):
            await raced_coordinator.recover()
        self.assertEqual(BackendRecoveryState.UNAVAILABLE, raced_coordinator.state)
        self.assertEqual(0, raced_coordinator.authorization_generation)
        racing.on_call = None
        await raced_coordinator.recover()
        self.assertEqual(1, raced_coordinator.authorization_generation)


if __name__ == "__main__":
    unittest.main()
