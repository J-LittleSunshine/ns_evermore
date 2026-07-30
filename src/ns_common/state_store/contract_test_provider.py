# -*- coding: utf-8 -*-
"""Deterministic, network-free StateStore used only by contract tests."""

from __future__ import annotations

import asyncio

from ns_common.exceptions import (
    NsRuntimeStateStoreConflictError,
    NsRuntimeStateStoreVersionMismatchError,
)
from ns_common.time import Clock

from .authority import (
    StateAccessScope,
    StateAuthorityKind,
    StateCallerCapability,
    StateNamespace,
    StateStoreCapabilities,
    _issue_state_access_scope,
    _new_state_scope_issuer,
)
from .model import (
    StateAppendResult,
    StateAssertion,
    StateConsistency,
    StateDocument,
    StateKey,
    StateMutation,
    StateMutationKind,
    StateOrderedIndexCursor,
    StateOrderedIndexEntry,
    StateOrderedIndexKey,
    StateOrderedIndexMutationKind,
    StateOrderedIndexReadAssertion,
    StateOrderedIndexReadResult,
    StateReadResult,
    StateRecord,
    StateRecordReadAssertion,
    StateRevision,
    StateScanResult,
    StateStoreHealth,
    StateStoreHealthStatus,
    StateTransaction,
    StateTransactionResult,
)
from .store import (
    StateStore,
    StateStoreDeliveryRepositories,
    StateStoreRepository,
    StateStoreRepositoryRole,
    _bind_state_store_repository,
)


class ContractTestStateStoreComposition:
    """Explicit contract-test realm; never accepts production configuration."""

    __slots__ = ("store", "_delivery", "_runtime_id", "_audit", "_issuer")

    def __init__(
        self,
        *,
        clock: Clock,
        capabilities: StateStoreCapabilities | None,
        runtime_id: str | None,
        audit_namespaces: tuple[StateNamespace, ...],
    ) -> None:
        issuer = _new_state_scope_issuer(contract_test=True)
        store = DeterministicContractTestStateStore(
            clock=clock,
            capabilities=capabilities,
            issuer=issuer,
        )
        self.store = store
        self._runtime_id = runtime_id
        self._issuer = issuer
        self._delivery = (
            None
            if runtime_id is None
            else StateStoreDeliveryRepositories(
                admission=self._repository(
                    role=StateStoreRepositoryRole.DELIVERY_ADMISSION,
                    runtime_id=runtime_id,
                ),
                scheduler=self._repository(
                    role=StateStoreRepositoryRole.DELIVERY_SCHEDULER,
                    runtime_id=runtime_id,
                ),
                payload=self._repository(
                    role=StateStoreRepositoryRole.DELIVERY_PAYLOAD,
                    runtime_id=runtime_id,
                ),
                registry=self._repository(
                    role=StateStoreRepositoryRole.DELIVERY_REGISTRY,
                    runtime_id=runtime_id,
                ),
            )
        )
        self._audit = {
            namespace: self._repository(
                role=StateStoreRepositoryRole.STRONG_AUDIT,
                audit_namespace=namespace,
            )
            for namespace in audit_namespaces
        }

    def _repository(
        self,
        *,
        role: StateStoreRepositoryRole,
        runtime_id: str | None = None,
        audit_namespace: StateNamespace | None = None,
    ) -> StateStoreRepository:
        repository_ref: StateStoreRepository | None = None

        def issue(atomic_scope):
            return _issue_state_access_scope(
                self._issuer,
                atomic_scope=atomic_scope,
                authority=(
                    StateAuthorityKind.STRONG_AUDIT
                    if role is StateStoreRepositoryRole.STRONG_AUDIT
                    else StateAuthorityKind.DELIVERY_ADMISSION
                ),
                caller="contract-test-repository",
                capabilities=frozenset(StateCallerCapability),
            )

        def current(candidate):
            return repository_ref is candidate

        repository_ref = _bind_state_store_repository(
            store=self.store,
            role=role,
            runtime_id=runtime_id,
            audit_namespace=audit_namespace,
            issue_atomic_scope=issue,
            is_current_repository=current,
        )
        return repository_ref

    def delivery_repositories(
        self,
        *,
        runtime_id: str,
    ) -> StateStoreDeliveryRepositories:
        if self._delivery is None or runtime_id != self._runtime_id:
            raise NsRuntimeStateStoreConflictError(details={
                "component": "contract_test_state_store",
                "reason": "repository_set_closed",
            })
        return self._delivery

    def strong_audit_repository(
        self,
        *,
        namespace: StateNamespace,
    ) -> StateStoreRepository:
        value = self._audit.get(namespace)
        if value is None:
            raise NsRuntimeStateStoreConflictError(details={
                "component": "contract_test_state_store",
                "reason": "audit_repository_unavailable",
            })
        return value


class DeterministicContractTestStateStore(StateStore):
    """Small in-memory semantic model with no socket or provider imports."""

    def __init__(
        self,
        *,
        clock: Clock,
        capabilities: StateStoreCapabilities | None,
        issuer: object,
    ) -> None:
        super().__init__(
            capabilities=capabilities or StateStoreCapabilities.p10_contract(),
            clock=clock,
            _contract_test_authority=True,
            _scope_issuer=issuer,
        )
        self.clock = clock
        self._records: dict[StateKey, StateRecord] = {}
        self._logs: dict[
            StateKey, list[tuple[StateDocument, StateRevision]]
        ] = {}
        self._ordered_indexes: dict[
            tuple[object, StateOrderedIndexKey], dict[str, float]
        ] = {}
        self._revision_order: dict[StateRevision, int] = {}
        self._revision_sequence = 0
        self._lock = asyncio.Lock()

    async def _open(self) -> None:
        return None

    async def _close(self) -> None:
        return None

    async def _read(
        self,
        *,
        scope: StateAccessScope,
        key: StateKey,
        consistency: StateConsistency,
        minimum_revision: StateRevision | None,
    ) -> StateReadResult:
        del scope, consistency
        async with self._lock:
            record = self._records.get(key)
            stale = False
            if minimum_revision is not None:
                minimum = self._revision_order.get(minimum_revision)
                current = (
                    self._revision_order.get(record.revision)
                    if record is not None
                    else None
                )
                stale = minimum is None or current is None or current < minimum
            return StateReadResult(
                record=record,
                observed_at=self.clock.utc_now(),
                stale=stale,
            )

    async def _compare_and_set(
        self,
        *,
        scope: StateAccessScope,
        mutation: StateMutation,
    ) -> StateRecord | None:
        del scope
        async with self._lock:
            self._validate_mutation(mutation, self._records)
            return self._apply_mutation(mutation)

    async def _scan(
        self,
        *,
        scope: StateAccessScope,
        object_type: str,
        cursor: str | None,
        limit: int,
    ) -> StateScanResult:
        offset = 0 if cursor is None else int(cursor)
        async with self._lock:
            values = tuple(
                record
                for key, record in sorted(
                    self._records.items(),
                    key=lambda item: (
                        item[0].object_type,
                        item[0].object_id,
                    ),
                )
                if key.namespace == scope.namespace
                and key.object_type == object_type
            )
            page = values[offset:offset + limit]
            next_offset = offset + len(page)
            return StateScanResult(
                records=page,
                next_cursor=(
                    str(next_offset)
                    if next_offset < len(values)
                    else None
                ),
                observed_at=self.clock.utc_now(),
            )

    async def _transact(
        self,
        transaction: StateTransaction,
    ) -> StateTransactionResult:
        async with self._lock:
            snapshot = dict(self._records)
            for assertion in transaction.record_assertions:
                self._validate_record_assertion(assertion, snapshot)
            for assertion in transaction.ordered_index_assertions:
                self._validate_ordered_index_assertion(
                    transaction.scope,
                    assertion,
                )
            for mutation in transaction.mutations:
                self._validate_mutation(mutation, snapshot)
            records = tuple(
                self._apply_mutation(mutation)
                for mutation in transaction.mutations
            )
            for mutation in transaction.ordered_index_mutations:
                values = self._ordered_indexes.setdefault(
                    (transaction.scope.atomic_scope, mutation.index),
                    {},
                )
                if mutation.kind is StateOrderedIndexMutationKind.ADD:
                    assert mutation.score is not None
                    values[mutation.member] = float(mutation.score)
                else:
                    values.pop(mutation.member, None)
            positions: list[int] = []
            for append in transaction.log_appends:
                entries = self._logs.setdefault(append.key, [])
                revision = self._next_revision()
                entries.append((append.document, revision))
                positions.append(len(entries))
            return StateTransactionResult.for_transaction(
                transaction,
                records=records,
                log_positions=tuple(positions),
            )

    async def _read_ordered_index(
        self,
        *,
        scope: StateAccessScope,
        index: StateOrderedIndexKey,
        limit: int,
        max_score: float | None,
        start_after: StateOrderedIndexCursor | None,
    ) -> StateOrderedIndexReadResult:
        async with self._lock:
            values = sorted(
                self._ordered_indexes.get(
                    (scope.atomic_scope, index),
                    {},
                ).items(),
                key=lambda item: (item[1], item[0]),
            )
            if max_score is not None:
                values = [
                    item for item in values if item[1] <= max_score
                ]
            offset = 0
            if start_after is not None:
                marker = (start_after.member, start_after.score)
                try:
                    offset = values.index(marker) + 1
                except ValueError:
                    self._conflict("cursor_stale")
            page = values[offset:offset + limit]
            return StateOrderedIndexReadResult(
                entries=tuple(
                    StateOrderedIndexEntry(member=member, score=score)
                    for member, score in page
                ),
                observed_at=self.clock.utc_now(),
                total_count=len(values),
                next_cursor=(
                    StateOrderedIndexCursor(
                        member=page[-1][0],
                        score=page[-1][1],
                    )
                    if page and offset + len(page) < len(values)
                    else None
                ),
            )

    async def _append(
        self,
        *,
        scope: StateAccessScope,
        key: StateKey,
        document: StateDocument,
        assertion: StateAssertion | None,
    ) -> StateAppendResult:
        del scope
        async with self._lock:
            entries = self._logs.setdefault(key, [])
            if assertion is not None:
                current = entries[-1][1] if entries else None
                if assertion.expect_absent and entries:
                    self._conflict("expected_absent")
                if (
                    not assertion.expect_absent
                    and current != assertion.expected_revision
                ):
                    self._conflict("revision")
            revision = self._next_revision()
            entries.append((document, revision))
            return StateAppendResult(
                revision=revision,
                position=len(entries),
                committed_at=self.clock.utc_now(),
            )

    async def _health(self) -> StateStoreHealth:
        return StateStoreHealth(
            status=StateStoreHealthStatus.READY,
            checked_at=self.clock.utc_now(),
            contract_generation=self.capabilities().contract_generation,
        )

    def _validate_record_assertion(
        self,
        assertion: StateRecordReadAssertion,
        records: dict[StateKey, StateRecord],
    ) -> None:
        current = records.get(assertion.key)
        if not assertion.expect_present:
            if current is not None:
                self._conflict("record_assertion_expected_absent")
            return
        if current is None:
            self._conflict("record_assertion_missing")
        assert current is not None
        if (
            assertion.expected_revision is not None
            and current.revision != assertion.expected_revision
        ):
            self._conflict("record_assertion_revision")
        if (
            assertion.expected_state_version is not None
            and current.document.state_version
            != assertion.expected_state_version
        ):
            self._conflict("record_assertion_state_version")

    def _validate_ordered_index_assertion(
        self,
        scope: StateAccessScope,
        assertion: StateOrderedIndexReadAssertion,
    ) -> None:
        values = self._ordered_indexes.get(
            (scope.atomic_scope, assertion.index),
            {},
        )
        current = values.get(assertion.member)
        if not assertion.expect_present:
            if current is not None:
                self._conflict("ordered_index_assertion_expected_absent")
            return
        if current is None:
            self._conflict("ordered_index_assertion_missing")
        if (
            assertion.expected_score is not None
            and current != assertion.expected_score
        ):
            self._conflict("ordered_index_assertion_score")

    def _validate_mutation(
        self,
        mutation: StateMutation,
        records: dict[StateKey, StateRecord],
    ) -> None:
        current = records.get(mutation.key)
        assertion = mutation.assertion
        if assertion.expect_absent:
            if current is not None:
                self._conflict("expected_absent")
            assert mutation.document is not None
            if mutation.document.state_version != 1:
                self._version_mismatch("initial_state_version")
            return
        if current is None:
            self._conflict("missing")
        assert current is not None
        if current.revision != assertion.expected_revision:
            self._conflict("revision")
        if (
            assertion.expected_state_version is not None
            and current.document.state_version
            != assertion.expected_state_version
        ):
            self._conflict("state_version")
        if (
            assertion.expected_epoch is not None
            and current.document.epoch != assertion.expected_epoch
        ):
            self._conflict("epoch")
        if mutation.document is not None:
            if (
                mutation.document.schema_name
                != current.document.schema_name
                or mutation.document.schema_version
                != current.document.schema_version
            ):
                self._version_mismatch("schema")
            if (
                mutation.document.state_version
                != current.document.state_version + 1
            ):
                self._version_mismatch("state_version")

    def _apply_mutation(
        self,
        mutation: StateMutation,
    ) -> StateRecord | None:
        if mutation.kind is StateMutationKind.DELETE:
            del self._records[mutation.key]
            return None
        assert mutation.document is not None
        record = StateRecord(
            key=mutation.key,
            document=mutation.document,
            revision=self._next_revision(),
            committed_at=self.clock.utc_now(),
        )
        self._records[mutation.key] = record
        return record

    def _next_revision(self) -> StateRevision:
        self._revision_sequence += 1
        revision = StateRevision._issue(
            f"contract:{self._revision_sequence}",
        )
        self._revision_order[revision] = self._revision_sequence
        return revision

    @staticmethod
    def _conflict(reason: str) -> None:
        raise NsRuntimeStateStoreConflictError(details={
            "component": "contract_test_state_store",
            "reason": reason,
        })

    @staticmethod
    def _version_mismatch(reason: str) -> None:
        raise NsRuntimeStateStoreVersionMismatchError(details={
            "component": "contract_test_state_store",
            "reason": reason,
        })


__all__ = (
    "ContractTestStateStoreComposition",
    "DeterministicContractTestStateStore",
)
