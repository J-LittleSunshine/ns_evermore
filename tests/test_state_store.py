# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import copy
import dataclasses
import unittest

from ns_common.config import NsRuntimeStateStoreConfig
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
    StateOrderedIndexEntry,
    StateOrderedIndexKey,
    StateOrderedIndexMutation,
    StateOrderedIndexMutationKind,
    StateOrderedIndexReadAssertion,
    StateScanResult,
    StateStoreCapabilities,
    StateStoreCapability,
    StateStoreHealthStatus,
    StateStoreLifecycleState,
    StateStoreRepository,
    StateStoreRepositoryRole,
    StateTransaction,
    StateTransactionResult,
    StateTransitionLogAppend,
    StateRecordReadAssertion,
    create_state_store_composition,
)
from ns_common.time import ControlledClock

from tests._state_store_contract_model import DeterministicStateStoreContractModel


def _scope(
    store: DeterministicStateStoreContractModel,
    namespace: StateNamespace | None = None,
    *,
    capabilities: frozenset[StateCallerCapability] | None = None,
) -> StateAccessScope:
    return store.issue_contract_test_scope(
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

    def test_ordered_index_public_values_reject_forgery_and_nonfinite_scores(self) -> None:
        namespace = StateNamespace.tenant(tenant_id="tenant-1", domain="delivery")
        index = StateOrderedIndexKey(
            namespace=namespace,
            name="delivery.ready",
            bucket="tenant-1",
        )
        mutation = StateOrderedIndexMutation(
            index=index,
            kind=StateOrderedIndexMutationKind.ADD,
            member="delivery:1",
            score=1.0,
        )
        for score in (float("nan"), float("inf"), float("-inf"), True):
            with self.subTest(score=score):
                with self.assertRaises(NsValidationError):
                    dataclasses.replace(mutation, score=score)
                with self.assertRaises(NsValidationError):
                    StateOrderedIndexEntry(member="delivery:1", score=score)
        with self.assertRaises(NsValidationError):
            dataclasses.replace(mutation, kind="add")
        present = StateOrderedIndexReadAssertion.present(
            index,
            "delivery:1",
            score=1.0,
        )
        with self.assertRaises(NsValidationError):
            dataclasses.replace(present, expected_score=float("nan"))
        with self.assertRaises(NsValidationError):
            StateOrderedIndexReadAssertion(
                index=index,
                member="delivery:1",
                expect_present=False,
                expected_score=1.0,
            )

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
        self.store = DeterministicStateStoreContractModel(clock=self.clock)
        self.scope = _scope(self.store)

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
        self.assertIs(
            StateStoreHealthStatus.CLOSED,
            (await self.store.health()).status,
        )
        with self.assertRaises(NsRuntimeStateStoreClosedError):
            await self.store.compare_and_set(
                scope=self.scope,
                mutation=_create(key),
            )

    async def test_scope_authority_cannot_be_constructed_replaced_or_reused(
        self,
    ) -> None:
        self.assertFalse(hasattr(self.store, "_issue_access_scope"))
        self.assertFalse(hasattr(self.store, "_create_repository"))
        with self.assertRaises(NsValidationError):
            StateStoreRepository(
                store=self.store,
                role=StateStoreRepositoryRole.DELIVERY_SCHEDULER,
                runtime_id="runtime-forged",
                audit_namespace=None,
                _token=None,
            )
        with self.assertRaises(NsValidationError):
            StateAccessScope(
                atomic_scope=self.scope.atomic_scope,
                authority=self.scope.authority,
                caller=self.scope.caller,
                capabilities=frozenset(StateCallerCapability),
            )
        with self.assertRaises(NsValidationError):
            dataclasses.replace(
                self.scope,
                capabilities=frozenset(StateCallerCapability),
            )
        narrow = self.store.issue_contract_test_scope(
            atomic_scope=self.scope.atomic_scope,
            authority=self.scope.authority,
            caller=self.scope.caller,
            capabilities=frozenset({StateCallerCapability.READ}),
        )
        copied = copy.copy(narrow)
        object.__setattr__(
            copied,
            "capabilities",
            frozenset(StateCallerCapability),
        )

        class ForgedScope(StateAccessScope):
            pass

        with self.assertRaises(NsValidationError):
            ForgedScope(
                atomic_scope=self.scope.atomic_scope,
                authority=self.scope.authority,
                caller=self.scope.caller,
                capabilities=frozenset(StateCallerCapability),
            )

        other = DeterministicStateStoreContractModel(clock=self.clock)
        self.addAsyncCleanup(other.close)
        await other.open()
        await self.store.open()
        with self.assertRaises(NsRuntimeStateStoreCapabilityUnavailableError):
            await self.store.read(
                scope=copied,
                key=_key(copied, "copied-scope"),
                consistency=StateConsistency.LINEARIZABLE,
            )
        with self.assertRaises(NsRuntimeStateStoreCapabilityUnavailableError):
            await other.read(
                scope=self.scope,
                key=_key(self.scope, "cross-store"),
                consistency=StateConsistency.LINEARIZABLE,
            )

    async def test_transaction_result_cardinality_and_type_mismatch_fail_closed(
        self,
    ) -> None:
        class WrongResultStore(DeterministicStateStoreContractModel):
            mode = ""

            async def _transact(self, transaction):
                result = await super()._transact(transaction)
                if self.mode == "records_missing":
                    return StateTransactionResult(
                        records=(),
                        log_positions=result.log_positions,
                    )
                if self.mode == "records_extra":
                    return StateTransactionResult(
                        records=result.records + (None,),
                        log_positions=result.log_positions,
                    )
                if self.mode == "logs_missing":
                    return StateTransactionResult(
                        records=result.records,
                        log_positions=(),
                    )
                if self.mode == "logs_extra":
                    return StateTransactionResult(
                        records=result.records,
                        log_positions=result.log_positions + (99,),
                    )
                return object()

        for mode in (
            "records_missing",
            "records_extra",
            "logs_missing",
            "logs_extra",
            "wrong_type",
        ):
            with self.subTest(mode=mode):
                store = WrongResultStore(clock=self.clock)
                store.mode = mode
                self.addAsyncCleanup(store.close)
                await store.open()
                scope = _scope(store)
                key = _key(scope, f"wrong-cardinality-{mode}")
                transaction = StateTransaction(
                    scope=scope,
                    mutations=(_create(key),),
                    log_appends=(
                        (StateTransitionLogAppend(
                            key=_key(scope, f"log-{mode}"),
                            document=_document(1),
                        ),)
                        if mode in {"logs_missing", "logs_extra"}
                        else ()
                    ),
                )
                with self.assertRaises(
                    NsRuntimeStateStoreIndeterminateWriteError,
                ):
                    await store.transact(transaction)

    async def test_repository_capabilities_are_fixed_and_cross_role_denied(
        self,
    ) -> None:
        repositories = self.store.repository_composition().delivery_repositories(
            runtime_id="runtime-contract",
        )
        self.assertNotEqual(
            repositories.payload.role,
            repositories.scheduler.role,
        )
        with self.assertRaises(NsValidationError):
            repositories.payload.registry_scope()
        with self.assertRaises(NsValidationError):
            repositories.registry.delivery_scope(
                tenant_id="tenant-1",
                bucket_id=0,
                layout_generation=1,
            )
        with self.assertRaises(NsValidationError):
            copy.copy(repositories.scheduler)
        await self.store.open()
        payload_scope = repositories.payload.delivery_scope(
            tenant_id="tenant-1",
            bucket_id=0,
            layout_generation=1,
        )
        with self.assertRaises(
            NsRuntimeStateStoreCapabilityUnavailableError,
        ):
            await self.store.transact(StateTransaction(
                scope=payload_scope,
                mutations=(_create(_key(payload_scope, "payload-write")),),
            ))

    async def test_production_store_has_closed_repositories_and_exact_resources(
        self,
    ) -> None:
        audit_namespace = StateNamespace.audit(domain="processor")
        composition = create_state_store_composition(
            config=NsRuntimeStateStoreConfig(
                backend="redis",
                endpoint="redis://127.0.0.1:6379/0",
                namespace="authority-contract-test",
            ),
            clock=self.clock,
            runtime_id="runtime-production",
            audit_namespaces=(audit_namespace,),
        )
        assert composition is not None
        store = composition.store
        repositories = composition.delivery_repositories(
            runtime_id="runtime-production",
        )
        self.assertIs(
            repositories,
            composition.delivery_repositories(
                runtime_id="runtime-production",
            ),
        )
        self.assertFalse(hasattr(store, "_create_repository"))
        self.assertFalse(any(
            "repository_owner" in name
            for name in dir(store)
        ))
        self.assertFalse(any(
            isinstance(value, StateStoreRepository)
            for value in vars(store).values()
        ))
        with self.assertRaises(AttributeError):
            getattr(store, "_StateStore__repository_owner")
        cloned_store = object.__new__(type(store))
        for name, value in vars(store).items():
            setattr(cloned_store, name, value)
        self.assertFalse(hasattr(cloned_store, "_create_repository"))
        self.assertFalse(any(
            "scope_issuer" in name and value is not None
            for name, value in vars(store).items()
        ))
        production_validator = vars(store).get(
            "_StateStore__production_scope_validator",
        )
        self.assertIsNotNone(production_validator)
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PrivateKey,
        )
        from ns_common.state_store.authority import _StateScopeIssuer
        validator_closure_values = tuple(
            cell.cell_contents
            for cell in production_validator._callback.__closure__
        )
        self.assertFalse(any(
            isinstance(value, (_StateScopeIssuer, Ed25519PrivateKey))
            for value in validator_closure_values
        ))
        with self.assertRaises(NsValidationError):
            copy.copy(production_validator)
        from ns_common.state_store.store import (
            _ProductionStateScopeValidator,
        )
        with self.assertRaises(NsValidationError):
            _ProductionStateScopeValidator(lambda scope: True)
        forged_validator = object.__new__(_ProductionStateScopeValidator)
        forged_validator._callback = lambda scope: True
        forged_validator._signature = b"\0" * 32
        self.assertFalse(forged_validator.is_valid())
        with self.assertRaises(
            NsRuntimeStateStoreCapabilityUnavailableError,
        ):
            type(composition)(store=store, owner=object())

        scheduler_scope = repositories.scheduler.delivery_scope(
            tenant_id="tenant-1",
            bucket_id=0,
            layout_generation=2,
        )
        payload_scope = repositories.payload.delivery_scope(
            tenant_id="tenant-1",
            bucket_id=0,
            layout_generation=2,
        )
        admission_scope = repositories.admission.delivery_scope(
            tenant_id="tenant-1",
            bucket_id=0,
            layout_generation=2,
        )
        registry_scope = repositories.registry.registry_scope()
        self.assertFalse(hasattr(scheduler_scope, "_issuer"))
        with self.assertRaises(
            NsRuntimeStateStoreCapabilityUnavailableError,
        ):
            repositories.scheduler._issue_atomic_scope(StateAtomicScope(
                namespace=scheduler_scope.namespace,
                partition="caller-selected-partition",
            ))
        with self.assertRaises(
            NsRuntimeStateStoreCapabilityUnavailableError,
        ):
            repositories.registry._issue_atomic_scope(StateAtomicScope(
                namespace=registry_scope.namespace,
                partition="layout-1-bucket-0",
            ))
        copied_scheduler_scope = copy.copy(scheduler_scope)
        self.assertIsNot(copied_scheduler_scope, scheduler_scope)
        with self.assertRaises(NsValidationError):
            dataclasses.replace(scheduler_scope, caller="forged")
        object.__setattr__(
            copied_scheduler_scope,
            "capabilities",
            frozenset(StateCallerCapability),
        )
        with self.assertRaises(
            NsRuntimeStateStoreCapabilityUnavailableError,
        ):
            await store.read(
                scope=copied_scheduler_scope,
                key=StateKey(
                    namespace=copied_scheduler_scope.namespace,
                    object_type="delivery",
                    object_id="copied-scope",
                ),
                consistency=StateConsistency.LINEARIZABLE,
            )

        async def denied_read(scope, object_type):
            with self.assertRaises(
                NsRuntimeStateStoreCapabilityUnavailableError,
            ):
                await store.read(
                    scope=scope,
                    key=StateKey(
                        namespace=scope.namespace,
                        object_type=object_type,
                        object_id="attack",
                    ),
                    consistency=StateConsistency.LINEARIZABLE,
                )

        await denied_read(scheduler_scope, "payload_body")
        await denied_read(payload_scope, "delivery")
        await denied_read(registry_scope, "delivery")

        for object_type, schema_name in (
            ("attempt", "delivery_attempt"),
            ("delivery_owner", "delivery_owner"),
            ("delivery_scheduler_cursor", "delivery_scheduler_cursor"),
        ):
            with self.subTest(admission_object=object_type):
                with self.assertRaises(
                    NsRuntimeStateStoreCapabilityUnavailableError,
                ):
                    await store.transact(StateTransaction(
                        scope=admission_scope,
                        mutations=(StateMutation(
                            key=StateKey(
                                namespace=admission_scope.namespace,
                                object_type=object_type,
                                object_id="attack",
                            ),
                            assertion=StateAssertion.absent(),
                            kind=StateMutationKind.CREATE,
                            document=StateDocument(
                                schema_name=schema_name,
                                schema_version=1,
                                state_version=1,
                                payload=b"{}",
                            ),
                        ),),
                    ))

        for scope, object_type, schema_name in (
            (scheduler_scope, "unknown_object", "delivery_delivery"),
            (scheduler_scope, "delivery", "unknown_schema"),
            (registry_scope, "delivery_authority_layout", "unknown_schema"),
        ):
            with self.assertRaises(
                NsRuntimeStateStoreCapabilityUnavailableError,
            ):
                await store.transact(StateTransaction(
                    scope=scope,
                    mutations=(StateMutation(
                        key=StateKey(
                            namespace=scope.namespace,
                            object_type=object_type,
                            object_id="attack",
                        ),
                        assertion=StateAssertion.absent(),
                        kind=StateMutationKind.CREATE,
                        document=StateDocument(
                            schema_name=schema_name,
                            schema_version=1,
                            state_version=1,
                            payload=b"{}",
                        ),
                    ),),
                ))

        for scope, name in (
            (scheduler_scope, "delivery.unknown"),
            (registry_scope, "delivery.prepared"),
        ):
            with self.assertRaises(
                NsRuntimeStateStoreCapabilityUnavailableError,
            ):
                await store.read_ordered_index(
                    scope=scope,
                    index=StateOrderedIndexKey(
                        namespace=scope.namespace,
                        name=name,
                        bucket="delivery",
                    ),
                    limit=1,
                )
        with self.assertRaises(
            NsRuntimeStateStoreCapabilityUnavailableError,
        ):
            await store.read_ordered_index(
                scope=scheduler_scope,
                index=StateOrderedIndexKey(
                    namespace=scheduler_scope.namespace,
                    name="delivery.ready",
                    bucket="wrong-bucket",
                ),
                limit=1,
            )

        with self.assertRaises(
            NsRuntimeStateStoreCapabilityUnavailableError,
        ):
            await store.transact(StateTransaction(
                scope=scheduler_scope,
                mutations=(),
                log_appends=(StateTransitionLogAppend(
                    key=StateKey(
                        namespace=scheduler_scope.namespace,
                        object_type="unknown_log",
                        object_id="attack",
                    ),
                    document=StateDocument(
                        schema_name="unknown_log_schema",
                        schema_version=1,
                        state_version=1,
                        payload=b"{}",
                    ),
                ),),
            ))

        audit_repository = composition.strong_audit_repository(
            namespace=audit_namespace,
        )
        audit_scope = audit_repository.audit_scope()
        with self.assertRaises(
            NsRuntimeStateStoreCapabilityUnavailableError,
        ):
            await store.append(
                scope=audit_scope,
                key=StateKey(
                    namespace=audit_scope.namespace,
                    object_type="unknown_audit_log",
                    object_id="final",
                ),
                document=StateDocument(
                    schema_name="runtime.unknown_audit",
                    schema_version=1,
                    state_version=1,
                    payload=b"{}",
                ),
            )

    async def test_transaction_result_is_model_bound_and_replay_safe(
        self,
    ) -> None:
        await self.store.open()
        first_key = _key(self.scope, "result-binding-1")
        transaction = StateTransaction(
            scope=self.scope,
            mutations=(_create(first_key),),
        )
        result = await self.store.transact(transaction)
        same_shape = StateTransaction(
            scope=self.scope,
            mutations=(_create(first_key),),
        )
        self.assertTrue(result.is_for_transaction(transaction))
        self.assertFalse(result.is_for_transaction(same_shape))
        with self.assertRaises(NsValidationError):
            copy.copy(transaction)
        cloned_transaction = object.__new__(StateTransaction)
        for field in dataclasses.fields(StateTransaction):
            object.__setattr__(
                cloned_transaction,
                field.name,
                getattr(transaction, field.name),
            )
        self.assertFalse(result.is_for_transaction(cloned_transaction))
        with self.assertRaises(NsValidationError):
            StateTransactionResult(
                records=result.records,
                log_positions=result.log_positions,
            )
        with self.assertRaises((NsValidationError, TypeError)):
            dataclasses.replace(result, records=result.records)
        with self.assertRaises(NsValidationError):
            copy.copy(result)
        with self.assertRaises(NsValidationError):
            copy.deepcopy(result)

        forged = object.__new__(StateTransactionResult)
        for field in dataclasses.fields(StateTransactionResult):
            object.__setattr__(forged, field.name, getattr(result, field.name))
        object.__setattr__(forged, "_transaction_binding", object())
        self.assertFalse(forged.is_for_transaction(transaction))

        second_key = _key(self.scope, "result-binding-2")
        two_mutations = StateTransaction(
            scope=self.scope,
            mutations=(
                _create(second_key),
                _create(_key(self.scope, "result-binding-3")),
            ),
        )
        second_result = await self.store.transact(two_mutations)
        with self.assertRaises(NsValidationError):
            StateTransactionResult.for_transaction(
                two_mutations,
                records=tuple(reversed(second_result.records)),
            )

        class ResultSubclass(StateTransactionResult):
            pass

        with self.assertRaises(NsValidationError):
            ResultSubclass.for_transaction(
                transaction,
                records=result.records,
            )

    async def test_contract_exposes_no_unconditional_put(self) -> None:
        self.assertFalse(hasattr(self.store, "put"))
        self.assertFalse(hasattr(self.store, "set"))

    async def test_scan_is_typed_paginated_and_scope_bounded(self) -> None:
        await self.store.open()
        for object_id in ("scan-c", "scan-a", "scan-b"):
            await self.store.compare_and_set(
                scope=self.scope,
                mutation=_create(_key(self.scope, object_id)),
            )
        first = await self.store.scan(
            scope=self.scope,
            object_type="contract_record",
            limit=2,
        )
        self.assertIsInstance(first, StateScanResult)
        self.assertEqual(("scan-a", "scan-b"), tuple(
            record.key.object_id for record in first.records
        ))
        self.assertEqual("2", first.next_cursor)
        second = await self.store.scan(
            scope=self.scope,
            object_type="contract_record",
            cursor=first.next_cursor,
            limit=2,
        )
        self.assertEqual(("scan-c",), tuple(
            record.key.object_id for record in second.records
        ))
        self.assertIsNone(second.next_cursor)
        with self.assertRaises(NsValidationError):
            StateScanResult(
                records=[],  # type: ignore[arg-type]
                next_cursor=None,
                observed_at=self.clock.utc_now(),
            )
        with self.assertRaises(NsValidationError):
            dataclasses.replace(first, next_cursor="0")
        without_scan = _scope(
            self.store,
            capabilities=frozenset({StateCallerCapability.READ}),
        )
        with self.assertRaises(NsRuntimeStateStoreCapabilityUnavailableError):
            await self.store.scan(
                scope=without_scan,
                object_type="contract_record",
            )

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
                scope=(restricted_scope := _scope(restricted)),
                mutation=_create(_key(restricted_scope, "capability")),
            )
        self.assertEqual({}, restricted.records)

        await self.store.open()
        other_scope = _scope(
            self.store,
            StateNamespace.audit(domain="other"),
        )
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

    async def test_read_preconditions_are_atomic_before_record_index_and_log_writes(
        self,
    ) -> None:
        await self.store.open()
        guarded_key = _key(self.scope, "read-guard")
        write_key = _key(self.scope, "read-write")
        guarded = await self.store.compare_and_set(
            scope=self.scope,
            mutation=_create(guarded_key),
        )
        assert guarded is not None
        index = StateOrderedIndexKey(
            namespace=self.scope.namespace,
            name="delivery.ready",
            bucket="contract",
        )
        await self.store.transact(StateTransaction(
            scope=self.scope,
            mutations=(_create(write_key),),
            ordered_index_mutations=(StateOrderedIndexMutation(
                index=index,
                kind=StateOrderedIndexMutationKind.ADD,
                member="delivery:guarded",
                score=7.0,
            ),),
        ))
        write_record = self.store.records[write_key]
        log_key = _key(self.scope, "read-assertion-log")
        transaction = StateTransaction(
            scope=self.scope,
            mutations=(_replace(
                write_key,
                write_record.revision,
                _document(2),
            ),),
            record_assertions=(StateRecordReadAssertion.present(
                guarded_key,
                revision=guarded.revision,
                state_version=guarded.document.state_version,
            ),),
            ordered_index_assertions=(
                StateOrderedIndexReadAssertion.present(
                    index,
                    "delivery:guarded",
                    score=7.0,
                ),
            ),
            ordered_index_mutations=(StateOrderedIndexMutation(
                index=index,
                kind=StateOrderedIndexMutationKind.ADD,
                member="delivery:new",
                score=8.0,
            ),),
            log_appends=(StateTransitionLogAppend(
                key=log_key,
                document=_document(1),
            ),),
        )
        await self.store.transact(transaction)
        advanced = self.store.records[write_key]
        self.assertEqual(2, advanced.document.state_version)

        stale = dataclasses.replace(
            transaction,
            mutations=(_replace(
                write_key,
                advanced.revision,
                _document(3),
            ),),
            ordered_index_assertions=(
                StateOrderedIndexReadAssertion.present(
                    index,
                    "delivery:guarded",
                    score=9.0,
                ),
            ),
        )
        committed_records = self.store.records
        committed_indexes = self.store.ordered_indexes
        committed_logs = self.store.logs
        with self.assertRaises(NsRuntimeStateStoreConflictError):
            await self.store.transact(stale)
        self.assertEqual(committed_records, self.store.records)
        self.assertEqual(committed_indexes, self.store.ordered_indexes)
        self.assertEqual(committed_logs, self.store.logs)

        missing_create = dataclasses.replace(
            stale,
            record_assertions=(StateRecordReadAssertion.absent(guarded_key),),
            ordered_index_assertions=(
                StateOrderedIndexReadAssertion.present(
                    index,
                    "delivery:guarded",
                    score=7.0,
                ),
            ),
        )
        with self.assertRaises(NsRuntimeStateStoreConflictError):
            await self.store.transact(missing_create)
        self.assertEqual(committed_records, self.store.records)
        self.assertEqual(committed_indexes, self.store.ordered_indexes)
        self.assertEqual(committed_logs, self.store.logs)

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
