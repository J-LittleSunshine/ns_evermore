# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import unittest

from ns_common.exceptions import (
    NsRuntimeStateStoreCapabilityUnavailableError,
    NsRuntimeStateStoreClosedError,
    NsRuntimeStateStoreConflictError,
    NsRuntimeStateStoreIndeterminateWriteError,
    NsRuntimeStateStoreNamespaceViolationError,
    NsRuntimeStateStoreNotReadyError,
    NsRuntimeStateStoreStaleReadError,
    NsRuntimeStateStoreTimeoutError,
    NsRuntimeStateStoreUnavailableError,
    NsRuntimeStateStoreVersionMismatchError,
    NsValidationError,
)
from ns_common.state_store import (
    STATE_AUTHORITY_BOUNDARIES,
    StateAccessScope,
    StateAssertion,
    StateAtomicScope,
    StateAuthorityClassification,
    StateAuthorityKind,
    StateCallerCapability,
    StateConsistency,
    StateDocument,
    StateKey,
    StateMutation,
    StateMutationKind,
    StateNamespace,
    StateNamespaceKind,
    StateStoreCapabilities,
    StateStoreCapability,
    StateStoreHealthStatus,
    StateStoreLifecycleState,
    StateTransaction,
)
from ns_common.time import ControlledClock

from tests._state_store_contract_model import DeterministicStateStoreContractModel


def _scope(
    namespace: StateNamespace | None = None,
    *,
    capabilities: frozenset[StateCallerCapability] | None = None,
) -> StateAccessScope:
    return StateAccessScope(
        atomic_scope=StateAtomicScope(
            namespace=namespace or StateNamespace.audit(domain="processor"),
            partition="contract",
        ),
        authority=StateAuthorityKind.STRONG_AUDIT,
        caller="contract-test",
        capabilities=capabilities or frozenset(StateCallerCapability),
    )


def _key(scope: StateAccessScope, object_id: str) -> StateKey:
    return StateKey(
        namespace=scope.namespace,
        object_type="contract_record",
        object_id=object_id,
    )


def _document(
    state_version: int,
    *,
    schema_version: int = 1,
    epoch: int | None = 3,
    payload: bytes = b"safe",
) -> StateDocument:
    return StateDocument(
        schema_name="contract.record",
        schema_version=schema_version,
        state_version=state_version,
        epoch=epoch,
        payload=payload,
    )


def _create(key: StateKey, document: StateDocument | None = None) -> StateMutation:
    return StateMutation(
        key=key,
        assertion=StateAssertion.absent(),
        kind=StateMutationKind.CREATE,
        document=document or _document(1),
    )


def _replace(
    key: StateKey,
    revision: object,
    document: StateDocument,
    *,
    state_version: int | None = None,
    epoch: int | None = None,
) -> StateMutation:
    return StateMutation(
        key=key,
        assertion=StateAssertion.matches(
            revision,  # type: ignore[arg-type]
            state_version=state_version,
            epoch=epoch,
        ),
        kind=StateMutationKind.REPLACE,
        document=document,
    )


class StateAuthorityContractTestCase(unittest.TestCase):

    def test_authority_boundaries_preserve_p05_p06_and_p07_owners(self) -> None:
        self.assertEqual(
            StateAuthorityClassification.LOCAL,
            STATE_AUTHORITY_BOUNDARIES[StateAuthorityKind.CONNECTION],
        )
        self.assertEqual(
            StateAuthorityClassification.LOCAL,
            STATE_AUTHORITY_BOUNDARIES[StateAuthorityKind.SESSION],
        )
        self.assertEqual(
            StateAuthorityClassification.EXTERNAL,
            STATE_AUTHORITY_BOUNDARIES[StateAuthorityKind.PERMISSION_SNAPSHOT],
        )
        self.assertEqual(
            StateAuthorityClassification.EXTERNAL,
            STATE_AUTHORITY_BOUNDARIES[StateAuthorityKind.CREDENTIAL],
        )
        self.assertEqual(
            StateAuthorityClassification.TRANSIENT,
            STATE_AUTHORITY_BOUNDARIES[StateAuthorityKind.PROCESSOR_EXECUTION],
        )
        self.assertEqual(
            StateAuthorityClassification.STATE_STORE,
            STATE_AUTHORITY_BOUNDARIES[StateAuthorityKind.STRONG_AUDIT],
        )
        self.assertEqual(
            StateAuthorityClassification.RESERVED,
            STATE_AUTHORITY_BOUNDARIES[StateAuthorityKind.FUTURE_AUTHORITY],
        )

        with self.assertRaises(NsValidationError):
            StateAccessScope(
                atomic_scope=StateAtomicScope(
                    namespace=StateNamespace.system(domain="connection"),
                    partition="contract",
                ),
                authority=StateAuthorityKind.CONNECTION,
                caller="forbidden-owner",
                capabilities=frozenset({StateCallerCapability.READ}),
            )

    def test_namespace_kind_is_typed_and_dimension_checked(self) -> None:
        values = (
            StateNamespace.tenant(tenant_id="tenant-1", domain="future"),
            StateNamespace.system(domain="future"),
            StateNamespace.runtime(runtime_id="runtime:1", domain="future"),
            StateNamespace.plugin(plugin_name="plugin.demo", domain="future"),
            StateNamespace.audit(domain="processor", tenant_id="tenant-1"),
        )
        self.assertEqual(set(StateNamespaceKind), {value.kind for value in values})
        with self.assertRaises(NsValidationError):
            StateNamespace(
                kind=StateNamespaceKind.SYSTEM,
                domain="future",
                tenant_id="tenant-1",
            )

    def test_revision_cannot_be_issued_by_business_code(self) -> None:
        from ns_common.state_store import StateRevision

        with self.assertRaises(NsValidationError):
            StateRevision("caller:1")


class StateStoreContractTestCase(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:
        self.clock = ControlledClock()
        self.scope = _scope()
        self.store = DeterministicStateStoreContractModel(clock=self.clock)

    async def asyncTearDown(self) -> None:
        await self.store.close()

    async def test_lifecycle_rejects_before_open_and_after_close(self) -> None:
        key = _key(self.scope, "lifecycle")
        self.assertIs(StateStoreLifecycleState.NEW, self.store.state)
        with self.assertRaises(NsRuntimeStateStoreNotReadyError):
            await self.store.read(
                scope=self.scope,
                key=key,
                consistency=StateConsistency.LINEARIZABLE,
            )
        self.assertIs(StateStoreHealthStatus.NOT_READY, (await self.store.health()).status)

        await self.store.open()
        await self.store.open()
        self.assertEqual(1, self.store.open_count)
        self.assertIs(StateStoreLifecycleState.OPEN, self.store.state)
        await self.store.close()
        await self.store.close()
        self.assertEqual(1, self.store.close_count)
        self.assertIs(StateStoreLifecycleState.CLOSED, self.store.state)
        self.assertIs(StateStoreHealthStatus.CLOSED, (await self.store.health()).status)
        with self.assertRaises(NsRuntimeStateStoreClosedError):
            await self.store.compare_and_set(
                scope=self.scope,
                mutation=_create(key),
            )

    async def test_contract_exposes_no_unconditional_put(self) -> None:
        self.assertFalse(hasattr(self.store, "put"))
        self.assertFalse(hasattr(self.store, "set"))

    async def test_cancelled_close_while_waiting_preserves_retryable_ownership(self) -> None:
        await self.store.open()
        self.store.read_started = asyncio.Event()
        self.store.release_read = asyncio.Event()
        read_task = asyncio.create_task(
            self.store.read(
                scope=self.scope,
                key=_key(self.scope, "active-read"),
                consistency=StateConsistency.LINEARIZABLE,
            ),
        )
        await self.store.read_started.wait()
        close_task = asyncio.create_task(self.store.close())
        while self.store.state is not StateStoreLifecycleState.CLOSING:
            await asyncio.sleep(0)
        close_task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await close_task
        self.assertIs(StateStoreLifecycleState.OPEN, self.store.state)
        self.assertEqual(0, self.store.close_count)

        self.store.release_read.set()
        await read_task
        await self.store.close()
        self.assertIs(StateStoreLifecycleState.CLOSED, self.store.state)
        self.assertEqual(1, self.store.close_count)

    async def test_capability_and_namespace_fail_before_mutation(self) -> None:
        restricted = DeterministicStateStoreContractModel(
            clock=self.clock,
            capabilities=StateStoreCapabilities(
                features=frozenset({
                    StateStoreCapability.READ,
                    StateStoreCapability.LINEARIZABLE_READ,
                }),
                authorities=frozenset({StateAuthorityKind.STRONG_AUDIT}),
            ),
        )
        await restricted.open()
        self.addAsyncCleanup(restricted.close)
        with self.assertRaises(NsRuntimeStateStoreCapabilityUnavailableError):
            await restricted.compare_and_set(
                scope=self.scope,
                mutation=_create(_key(self.scope, "capability")),
            )
        self.assertEqual({}, restricted.records)

        await self.store.open()
        other_scope = _scope(StateNamespace.audit(domain="other"))
        with self.assertRaises(NsRuntimeStateStoreNamespaceViolationError):
            await self.store.read(
                scope=self.scope,
                key=_key(other_scope, "cross-domain"),
                consistency=StateConsistency.LINEARIZABLE,
            )
        with self.assertRaises(NsRuntimeStateStoreNamespaceViolationError):
            await self.store.read(
                scope=self.scope,
                key="raw-key",  # type: ignore[arg-type]
                consistency=StateConsistency.LINEARIZABLE,
            )

    async def test_cas_version_epoch_and_schema_contract(self) -> None:
        await self.store.open()
        key = _key(self.scope, "versioned")
        created = await self.store.compare_and_set(
            scope=self.scope,
            mutation=_create(key),
        )
        assert created is not None

        replaced = await self.store.compare_and_set(
            scope=self.scope,
            mutation=_replace(
                key,
                created.revision,
                _document(2),
                state_version=1,
                epoch=3,
            ),
        )
        assert replaced is not None
        self.assertNotEqual(created.revision, replaced.revision)

        with self.assertRaises(NsRuntimeStateStoreConflictError):
            await self.store.compare_and_set(
                scope=self.scope,
                mutation=_replace(key, created.revision, _document(2)),
            )
        with self.assertRaises(NsRuntimeStateStoreConflictError):
            await self.store.compare_and_set(
                scope=self.scope,
                mutation=_replace(
                    key,
                    replaced.revision,
                    _document(3),
                    epoch=2,
                ),
            )
        with self.assertRaises(NsRuntimeStateStoreVersionMismatchError):
            await self.store.compare_and_set(
                scope=self.scope,
                mutation=_replace(
                    key,
                    replaced.revision,
                    _document(3, schema_version=2),
                ),
            )
        current = self.store.records[key]
        self.assertEqual(2, current.document.state_version)
        self.assertEqual(replaced.revision, current.revision)

    async def test_concurrent_cas_has_exactly_one_winner(self) -> None:
        await self.store.open()
        key = _key(self.scope, "concurrent")
        current = await self.store.compare_and_set(
            scope=self.scope,
            mutation=_create(key),
        )
        assert current is not None

        results = await asyncio.gather(
            *(
                self.store.compare_and_set(
                    scope=self.scope,
                    mutation=_replace(
                        key,
                        current.revision,
                        _document(2, payload=f"winner-{index}".encode()),
                    ),
                )
                for index in range(12)
            ),
            return_exceptions=True,
        )
        self.assertEqual(1, sum(not isinstance(value, BaseException) for value in results))
        self.assertEqual(
            11,
            sum(isinstance(value, NsRuntimeStateStoreConflictError) for value in results),
        )

    async def test_transaction_is_atomic_when_any_assertion_conflicts(self) -> None:
        await self.store.open()
        first_key = _key(self.scope, "transaction-first")
        second_key = _key(self.scope, "transaction-second")
        created = await self.store.transact(
            StateTransaction(
                scope=self.scope,
                mutations=(_create(first_key), _create(second_key)),
            ),
        )
        first, second = created.records
        assert first is not None and second is not None

        advanced = await self.store.compare_and_set(
            scope=self.scope,
            mutation=_replace(second_key, second.revision, _document(2)),
        )
        assert advanced is not None
        with self.assertRaises(NsRuntimeStateStoreConflictError):
            await self.store.transact(
                StateTransaction(
                    scope=self.scope,
                    mutations=(
                        _replace(first_key, first.revision, _document(2)),
                        _replace(second_key, second.revision, _document(2)),
                    ),
                ),
            )
        self.assertEqual(1, self.store.records[first_key].document.state_version)
        self.assertEqual(advanced.revision, self.store.records[second_key].revision)

    async def test_minimum_revision_and_explicit_stale_read(self) -> None:
        await self.store.open()
        old_key = _key(self.scope, "old")
        new_key = _key(self.scope, "new")
        old = await self.store.compare_and_set(
            scope=self.scope,
            mutation=_create(old_key),
        )
        newer = await self.store.compare_and_set(
            scope=self.scope,
            mutation=_create(new_key),
        )
        assert old is not None and newer is not None

        stale = await self.store.read(
            scope=self.scope,
            key=old_key,
            consistency=StateConsistency.STALE_ALLOWED,
            minimum_revision=newer.revision,
        )
        self.assertTrue(stale.stale)
        with self.assertRaises(NsRuntimeStateStoreStaleReadError):
            await self.store.read(
                scope=self.scope,
                key=old_key,
                consistency=StateConsistency.AT_LEAST_REVISION,
                minimum_revision=newer.revision,
            )
        current = await self.store.read(
            scope=self.scope,
            key=old_key,
            consistency=StateConsistency.AT_LEAST_REVISION,
            minimum_revision=old.revision,
        )
        self.assertFalse(current.stale)

    async def test_failure_mapping_never_retries_indeterminate_write(self) -> None:
        await self.store.open()
        key = _key(self.scope, "failure")
        self.store.read_error = NsRuntimeStateStoreUnavailableError()
        with self.assertRaises(NsRuntimeStateStoreUnavailableError):
            await self.store.read(
                scope=self.scope,
                key=key,
                consistency=StateConsistency.LINEARIZABLE,
            )
        self.assertEqual(1, self.store.read_count)

        self.store.read_error = asyncio.TimeoutError()
        with self.assertRaises(NsRuntimeStateStoreTimeoutError):
            await self.store.read(
                scope=self.scope,
                key=key,
                consistency=StateConsistency.LINEARIZABLE,
            )
        self.assertEqual(2, self.store.read_count)

        self.store.write_error = asyncio.TimeoutError()
        with self.assertRaises(NsRuntimeStateStoreIndeterminateWriteError):
            await self.store.compare_and_set(
                scope=self.scope,
                mutation=_create(key),
            )
        self.assertEqual(1, self.store.write_count)

        self.store.write_error = NsRuntimeStateStoreTimeoutError(
            details={"component": "contract_model", "operation": "write"},
        )
        with self.assertRaises(NsRuntimeStateStoreIndeterminateWriteError):
            await self.store.compare_and_set(
                scope=self.scope,
                mutation=_create(_key(self.scope, "stable-timeout")),
            )
        self.assertEqual(2, self.store.write_count)
        self.assertEqual({}, self.store.records)

    async def test_recovery_revalidates_health_contract_generation(self) -> None:
        await self.store.open()
        self.store.health_status = StateStoreHealthStatus.UNAVAILABLE
        self.assertIs(StateStoreHealthStatus.UNAVAILABLE, (await self.store.health()).status)
        self.store.health_status = StateStoreHealthStatus.READY
        self.store.health_generation += 1
        with self.assertRaises(NsRuntimeStateStoreUnavailableError) as context:
            await self.store.health()
        self.assertEqual(
            "contract_generation_mismatch",
            context.exception.details["reason"],
        )
        self.store.health_generation = self.store.capabilities().contract_generation
        self.assertTrue((await self.store.health()).ready)


if __name__ == "__main__":
    unittest.main()
