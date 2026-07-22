# -*- coding: utf-8 -*-
"""Deterministic in-test model for the P08 abstract conformance suite."""

from __future__ import annotations

import asyncio

from ns_common.exceptions import (
    NsRuntimeStateStoreConflictError,
    NsRuntimeStateStoreVersionMismatchError,
)
from ns_common.state_store import (
    StateAccessScope,
    StateAppendResult,
    StateAssertion,
    StateConsistency,
    StateDocument,
    StateKey,
    StateMutation,
    StateMutationKind,
    StateOrderedIndexEntry,
    StateOrderedIndexKey,
    StateOrderedIndexMutationKind,
    StateOrderedIndexReadResult,
    StateReadResult,
    StateRecord,
    StateRevision,
    StateScanResult,
    StateStore,
    StateStoreCapabilities,
    StateStoreHealth,
    StateStoreHealthStatus,
    StateTransaction,
    StateTransactionResult,
)
from ns_common.time import Clock


class DeterministicStateStoreContractModel(StateStore):
    """A non-production semantic model; it is not a storage adapter."""

    def __init__(
        self,
        *,
        clock: Clock,
        capabilities: StateStoreCapabilities | None = None,
        events: list[str] | None = None,
    ) -> None:
        super().__init__(
            capabilities=capabilities or StateStoreCapabilities.p08_contract(),
            clock=clock,
        )
        self.clock = clock
        self.events = events
        self.open_count = 0
        self.close_count = 0
        self.read_count = 0
        self.write_count = 0
        self.read_error: BaseException | None = None
        self.write_error: BaseException | None = None
        self.health_error: BaseException | None = None
        self.health_status = StateStoreHealthStatus.READY
        self.health_generation = self.capabilities().contract_generation
        self.read_started: asyncio.Event | None = None
        self.release_read: asyncio.Event | None = None
        self._records: dict[StateKey, StateRecord] = {}
        self._logs: dict[StateKey, list[tuple[StateDocument, StateRevision]]] = {}
        self._ordered_indexes: dict[StateOrderedIndexKey, dict[str, float]] = {}
        self._revision_order: dict[StateRevision, int] = {}
        self._revision_sequence = 0
        self._lock = asyncio.Lock()

    @property
    def records(self) -> dict[StateKey, StateRecord]:
        return dict(self._records)

    @property
    def logs(self) -> dict[StateKey, tuple[StateDocument, ...]]:
        return {
            key: tuple(document for document, _ in entries)
            for key, entries in self._logs.items()
        }

    @property
    def ordered_indexes(self) -> dict[StateOrderedIndexKey, dict[str, float]]:
        return {key: dict(values) for key, values in self._ordered_indexes.items()}

    async def _open(self) -> None:
        self.open_count += 1
        if self.events is not None:
            self.events.append("state_store:open")

    async def _close(self) -> None:
        self.close_count += 1
        if self.events is not None:
            self.events.append("state_store:close")

    async def _read(
        self,
        *,
        scope: StateAccessScope,
        key: StateKey,
        consistency: StateConsistency,
        minimum_revision: StateRevision | None,
    ) -> StateReadResult:
        del scope
        self.read_count += 1
        if self.read_started is not None:
            self.read_started.set()
        if self.release_read is not None:
            await self.release_read.wait()
        if self.read_error is not None:
            raise self.read_error
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
        self.write_count += 1
        if self.write_error is not None:
            raise self.write_error
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
        self.read_count += 1
        if self.read_error is not None:
            raise self.read_error
        offset = 0 if cursor is None else int(cursor)
        async with self._lock:
            values = tuple(
                record for key, record in sorted(
                    self._records.items(),
                    key=lambda item: (item[0].object_type, item[0].object_id),
                )
                if key.namespace == scope.namespace
                and key.object_type == object_type
            )
            page = values[offset:offset + limit]
            next_offset = offset + len(page)
            return StateScanResult(
                records=page,
                next_cursor=(str(next_offset) if next_offset < len(values) else None),
                observed_at=self.clock.utc_now(),
            )

    async def _transact(
        self,
        transaction: StateTransaction,
    ) -> StateTransactionResult:
        self.write_count += 1
        if self.write_error is not None:
            raise self.write_error
        async with self._lock:
            snapshot = dict(self._records)
            for mutation in transaction.mutations:
                self._validate_mutation(mutation, snapshot)
            records = tuple(
                self._apply_mutation(mutation)
                for mutation in transaction.mutations
            )
            for mutation in transaction.ordered_index_mutations:
                values = self._ordered_indexes.setdefault(mutation.index, {})
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
            return StateTransactionResult(records=records, log_positions=tuple(positions))

    async def _read_ordered_index(
        self, *, scope: StateAccessScope, index: StateOrderedIndexKey,
        limit: int, max_score: float | None,
    ) -> StateOrderedIndexReadResult:
        del scope
        self.read_count += 1
        async with self._lock:
            values = sorted(
                self._ordered_indexes.get(index, {}).items(),
                key=lambda item: (item[1], item[0]),
            )
            if max_score is not None:
                values = [item for item in values if item[1] <= max_score]
            return StateOrderedIndexReadResult(
                entries=tuple(StateOrderedIndexEntry(member=member, score=score)
                              for member, score in values[:limit]),
                observed_at=self.clock.utc_now(),
                total_count=len(values),
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
        self.write_count += 1
        if self.write_error is not None:
            raise self.write_error
        async with self._lock:
            entries = self._logs.setdefault(key, [])
            if assertion is not None:
                current_revision = entries[-1][1] if entries else None
                if assertion.expect_absent:
                    if entries:
                        self._conflict("expected_absent")
                elif current_revision != assertion.expected_revision:
                    self._conflict("revision")
            revision = self._next_revision()
            entries.append((document, revision))
            return StateAppendResult(
                revision=revision,
                position=len(entries),
                committed_at=self.clock.utc_now(),
            )

    async def _health(self) -> StateStoreHealth:
        if self.health_error is not None:
            raise self.health_error
        return StateStoreHealth(
            status=self.health_status,
            checked_at=self.clock.utc_now(),
            contract_generation=self.health_generation,
        )

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
                mutation.document.schema_name != current.document.schema_name
                or mutation.document.schema_version
                != current.document.schema_version
            ):
                self._version_mismatch("schema")
            if (
                mutation.document.state_version
                != current.document.state_version + 1
            ):
                self._version_mismatch("state_version")

    def _apply_mutation(self, mutation: StateMutation) -> StateRecord | None:
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
        revision = StateRevision._issue(f"contract:{self._revision_sequence}")
        self._revision_order[revision] = self._revision_sequence
        return revision

    @staticmethod
    def _conflict(reason: str) -> None:
        raise NsRuntimeStateStoreConflictError(
            details={"component": "state_store_contract_model", "reason": reason},
        )

    @staticmethod
    def _version_mismatch(reason: str) -> None:
        raise NsRuntimeStateStoreVersionMismatchError(
            details={"component": "state_store_contract_model", "reason": reason},
        )


__all__ = ("DeterministicStateStoreContractModel",)
