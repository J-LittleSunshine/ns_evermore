# -*- coding: utf-8 -*-
"""Narrow P10/P11 persistence contracts without production StateAccessScope."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from ns_common.exceptions import NsValidationError
from ns_common.state_store import (
    StateAccessScope,
    StateConsistency,
    StateDocument,
    StateKey,
    StateMutation,
    StateNamespace,
    StateOrderedIndexCursor,
    StateOrderedIndexKey,
    StateOrderedIndexMutation,
    StateOrderedIndexReadAssertion,
    StateOrderedIndexReadResult,
    StateReadResult,
    StateRecord,
    StateRecordReadAssertion,
    StateStoreRepository,
    StateStoreRepositoryRole,
    StateTransaction,
    StateTransitionLogAppend,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class DeliveryPersistencePartition:
    tenant_id: str
    bucket_id: int
    layout_generation: int
    namespace: StateNamespace

    def __post_init__(self) -> None:
        if (
            type(self.tenant_id) is not str
            or not self.tenant_id
            or type(self.bucket_id) is not int
            or self.bucket_id < 0
            or type(self.layout_generation) is not int
            or self.layout_generation <= 0
            or type(self.namespace) is not StateNamespace
        ):
            _invalid("partition")


@dataclass(frozen=True, slots=True, kw_only=True)
class DeliveryPersistenceTransaction:
    partition: DeliveryPersistencePartition
    mutations: tuple[StateMutation, ...]
    ordered_index_mutations: tuple[StateOrderedIndexMutation, ...] = ()
    log_appends: tuple[StateTransitionLogAppend, ...] = ()
    record_assertions: tuple[StateRecordReadAssertion, ...] = ()
    ordered_index_assertions: tuple[StateOrderedIndexReadAssertion, ...] = ()

    def __post_init__(self) -> None:
        if type(self.partition) is not DeliveryPersistencePartition:
            _invalid("transaction.partition")
        if (
            type(self.mutations) is not tuple
            or type(self.ordered_index_mutations) is not tuple
            or type(self.log_appends) is not tuple
            or type(self.record_assertions) is not tuple
            or type(self.ordered_index_assertions) is not tuple
            or not (
                self.mutations
                or self.ordered_index_mutations
                or self.log_appends
            )
        ):
            _invalid("transaction.operations")
        for values, expected, field in (
            (self.mutations, StateMutation, "transaction.mutations"),
            (
                self.ordered_index_mutations,
                StateOrderedIndexMutation,
                "transaction.ordered_index_mutations",
            ),
            (
                self.log_appends,
                StateTransitionLogAppend,
                "transaction.log_appends",
            ),
            (
                self.record_assertions,
                StateRecordReadAssertion,
                "transaction.record_assertions",
            ),
            (
                self.ordered_index_assertions,
                StateOrderedIndexReadAssertion,
                "transaction.ordered_index_assertions",
            ),
        ):
            if any(type(value) is not expected for value in values):
                _invalid(field)

    @property
    def fingerprint(self) -> str:
        return "sha256:" + hashlib.sha256(
            _canonical_transaction_bytes(self),
        ).hexdigest()


@dataclass(frozen=True, slots=True, kw_only=True, init=False)
class DeliveryPersistenceTransactionResult:
    records: tuple[StateRecord | None, ...]
    log_positions: tuple[int, ...]
    request_fingerprint: str
    _transaction_identity: DeliveryPersistenceTransaction
    _result_digest: str

    def __init__(self, *args: object, **kwargs: object) -> None:
        del self, args, kwargs
        _invalid("transaction_result.issuer")

    @classmethod
    def for_transaction(
        cls,
        transaction: DeliveryPersistenceTransaction,
        *,
        records: tuple[StateRecord | None, ...],
        log_positions: tuple[int, ...],
    ) -> "DeliveryPersistenceTransactionResult":
        if cls is not DeliveryPersistenceTransactionResult:
            _invalid("transaction_result.type")
        _validate_transaction_result(
            transaction,
            records=records,
            log_positions=log_positions,
        )
        value = object.__new__(cls)
        request_fingerprint = transaction.fingerprint
        for name, item in (
            ("records", records),
            ("log_positions", log_positions),
            ("request_fingerprint", request_fingerprint),
            ("_transaction_identity", transaction),
            (
                "_result_digest",
                _transaction_result_digest(
                    records=records,
                    log_positions=log_positions,
                    request_fingerprint=request_fingerprint,
                ),
            ),
        ):
            object.__setattr__(value, name, item)
        return value

    def is_for_transaction(
        self,
        transaction: DeliveryPersistenceTransaction,
    ) -> bool:
        if (
            type(self) is not DeliveryPersistenceTransactionResult
            or type(transaction) is not DeliveryPersistenceTransaction
            or self._transaction_identity is not transaction
            or self.request_fingerprint != transaction.fingerprint
        ):
            return False
        try:
            _validate_transaction_result(
                transaction,
                records=self.records,
                log_positions=self.log_positions,
            )
            expected_digest = _transaction_result_digest(
                records=self.records,
                log_positions=self.log_positions,
                request_fingerprint=self.request_fingerprint,
            )
        except (AttributeError, NsValidationError, TypeError, ValueError):
            return False
        return self._result_digest == expected_digest

    def __copy__(self) -> "DeliveryPersistenceTransactionResult":
        _invalid("transaction_result.copy")

    def __deepcopy__(
        self, memo: dict[int, object],
    ) -> "DeliveryPersistenceTransactionResult":
        del memo
        _invalid("transaction_result.copy")


@runtime_checkable
class DeliveryAdmissionPersistence(Protocol):
    def delivery_scope(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
    ) -> DeliveryPersistencePartition: ...

    async def read(
        self, *, scope: DeliveryPersistencePartition, key: StateKey,
        consistency: StateConsistency,
    ) -> StateReadResult: ...

    async def transact(
        self, transaction: DeliveryPersistenceTransaction,
    ) -> DeliveryPersistenceTransactionResult: ...


@runtime_checkable
class DeliverySchedulerPersistence(DeliveryAdmissionPersistence, Protocol):
    async def read_ordered_index(
        self, *, scope: DeliveryPersistencePartition,
        index: StateOrderedIndexKey, limit: int,
        max_score: float | None = None,
        start_after: StateOrderedIndexCursor | None = None,
    ) -> StateOrderedIndexReadResult: ...


@runtime_checkable
class DeliveryPayloadPersistence(Protocol):
    def delivery_scope(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
    ) -> DeliveryPersistencePartition: ...

    async def read(
        self, *, scope: DeliveryPersistencePartition, key: StateKey,
        consistency: StateConsistency,
    ) -> StateReadResult: ...


@runtime_checkable
class DeliveryRegistryPersistence(Protocol):
    @property
    def runtime_id(self) -> str: ...

    @property
    def namespace(self) -> StateNamespace: ...

    async def read(
        self, *, key: StateKey, consistency: StateConsistency,
    ) -> StateReadResult: ...

    async def transact(
        self, transaction: DeliveryPersistenceTransaction,
    ) -> DeliveryPersistenceTransactionResult: ...

    async def read_ordered_index(
        self, *, index: StateOrderedIndexKey, limit: int,
        start_after: StateOrderedIndexCursor | None = None,
    ) -> StateOrderedIndexReadResult: ...


@runtime_checkable
class StrongAuditPersistence(Protocol):
    async def append_processor_audit(
        self, *, document: StateDocument,
    ) -> object: ...

    async def append_connection_audit(
        self, *, document: StateDocument,
    ) -> object: ...


class ContractTestRepositoryPersistence:
    """Explicit adapter for contract-test repositories only."""

    __slots__ = ("_repository", "_store", "_role")

    def __init__(
        self,
        repository: StateStoreRepository,
        *,
        role: StateStoreRepositoryRole,
    ) -> None:
        if (
            type(repository) is not StateStoreRepository
            or repository._contract_issue_scope is None
            or repository._role is not role
        ):
            _invalid("contract_repository")
        self._repository = repository
        self._store = repository._store
        self._role = role

    @property
    def runtime_id(self) -> str:
        value = self._repository._runtime_id
        if type(value) is not str:
            _invalid("registry.runtime_id")
        return value

    @property
    def namespace(self) -> StateNamespace:
        return self._repository.registry_scope().namespace

    def delivery_scope(
        self, *, tenant_id: str, bucket_id: int, layout_generation: int,
    ) -> DeliveryPersistencePartition:
        scope = self._repository.delivery_scope(
            tenant_id=tenant_id,
            bucket_id=bucket_id,
            layout_generation=layout_generation,
        )
        return DeliveryPersistencePartition(
            tenant_id=tenant_id,
            bucket_id=bucket_id,
            layout_generation=layout_generation,
            namespace=scope.namespace,
        )

    def _scope(
        self,
        value: DeliveryPersistencePartition | StateAccessScope,
    ) -> StateAccessScope:
        if type(value) is StateAccessScope:
            # Compatibility is confined to an exact contract-test repository.
            # A production raw repository is rejected by this adapter's
            # constructor, so business code cannot smuggle a production scope.
            generation, bucket = _partition_dimensions(
                value.atomic_scope.partition,
            )
            expected = self._repository.delivery_scope(
                tenant_id=value.namespace.tenant_id,
                bucket_id=bucket,
                layout_generation=generation,
            )
            if (
                value._issuer_realm != "contract_test"
                or value.atomic_scope != expected.atomic_scope
                or value.authority != expected.authority
                or value.caller != expected.caller
                or value.capabilities != expected.capabilities
            ):
                _invalid("partition.contract_scope")
            return value
        scope = self._repository.delivery_scope(
            tenant_id=value.tenant_id,
            bucket_id=value.bucket_id,
            layout_generation=value.layout_generation,
        )
        if scope.namespace != value.namespace:
            _invalid("partition.namespace")
        return scope

    async def read(
        self, *, key: StateKey, consistency: StateConsistency,
        scope: DeliveryPersistencePartition | None = None,
    ) -> StateReadResult:
        if scope is None:
            raw_scope = self._repository.registry_scope()
        else:
            raw_scope = self._scope(scope)
        return await self._store.read(
            scope=raw_scope,
            key=key,
            consistency=consistency,
        )

    async def transact(
        self,
        transaction: DeliveryPersistenceTransaction,
    ) -> DeliveryPersistenceTransactionResult:
        if type(transaction) is not DeliveryPersistenceTransaction:
            _invalid("transaction")
        if self._role is StateStoreRepositoryRole.DELIVERY_REGISTRY:
            scope = self._repository.registry_scope()
        else:
            scope = self._scope(transaction.partition)
        raw = StateTransaction(
            scope=scope,
            mutations=transaction.mutations,
            ordered_index_mutations=transaction.ordered_index_mutations,
            log_appends=transaction.log_appends,
            record_assertions=transaction.record_assertions,
            ordered_index_assertions=transaction.ordered_index_assertions,
        )
        result = await self._store.transact(raw)
        return DeliveryPersistenceTransactionResult.for_transaction(
            transaction,
            records=result.records,
            log_positions=result.log_positions,
        )

    async def read_ordered_index(
        self, *, index: StateOrderedIndexKey, limit: int,
        scope: DeliveryPersistencePartition | None = None,
        max_score: float | None = None,
        start_after: StateOrderedIndexCursor | None = None,
    ) -> StateOrderedIndexReadResult:
        raw_scope = (
            self._repository.registry_scope()
            if scope is None
            else self._scope(scope)
        )
        return await self._store.read_ordered_index(
            scope=raw_scope,
            index=index,
            limit=limit,
            max_score=max_score,
            start_after=start_after,
        )


def contract_test_persistence(
    repository: StateStoreRepository,
    role: StateStoreRepositoryRole,
) -> ContractTestRepositoryPersistence:
    return ContractTestRepositoryPersistence(repository, role=role)


def _canonical_transaction_bytes(
    value: DeliveryPersistenceTransaction,
) -> bytes:
    if type(value) is not DeliveryPersistenceTransaction:
        _invalid("transaction")
    return _canonical_json_bytes({
        "partition": {
            "tenant_id": value.partition.tenant_id,
            "bucket_id": value.partition.bucket_id,
            "layout_generation": value.partition.layout_generation,
            "namespace": _namespace_values(value.partition.namespace),
        },
        "mutations": [
            {
                "key": _key_values(item.key),
                "kind": item.kind.value,
                "assertion": {
                    "expect_absent": item.assertion.expect_absent,
                    "expected_revision": _revision_value(
                        item.assertion.expected_revision,
                    ),
                    "expected_state_version": (
                        item.assertion.expected_state_version
                    ),
                    "expected_epoch": item.assertion.expected_epoch,
                },
                "document": _document_values(item.document),
            }
            for item in value.mutations
        ],
        "record_assertions": [
            {
                "key": _key_values(item.key),
                "expect_present": item.expect_present,
                "expected_revision": _revision_value(
                    item.expected_revision,
                ),
                "expected_state_version": item.expected_state_version,
            }
            for item in value.record_assertions
        ],
        "ordered_index_mutations": [
            {
                "index": _index_values(item.index),
                "kind": item.kind.value,
                "member": item.member,
                "score": item.score,
            }
            for item in value.ordered_index_mutations
        ],
        "ordered_index_assertions": [
            {
                "index": _index_values(item.index),
                "member": item.member,
                "expect_present": item.expect_present,
                "expected_score": item.expected_score,
            }
            for item in value.ordered_index_assertions
        ],
        "log_appends": [
            {
                "key": _key_values(item.key),
                "document": _document_values(item.document),
            }
            for item in value.log_appends
        ],
    })


def _validate_transaction_result(
    transaction: DeliveryPersistenceTransaction,
    *,
    records: tuple[StateRecord | None, ...],
    log_positions: tuple[int, ...],
) -> None:
    if (
        type(transaction) is not DeliveryPersistenceTransaction
        or type(records) is not tuple
        or len(records) != len(transaction.mutations)
        or type(log_positions) is not tuple
        or len(log_positions) != len(transaction.log_appends)
        or any(
            type(value) is not int or value <= 0
            for value in log_positions
        )
    ):
        _invalid("transaction_result")
    for mutation, record in zip(transaction.mutations, records):
        if mutation.kind.value == "delete":
            if record is not None:
                _invalid("transaction_result.delete")
            continue
        if (
            type(record) is not StateRecord
            or record.key != mutation.key
            or record.document != mutation.document
        ):
            _invalid("transaction_result.record_binding")


def _transaction_result_digest(
    *,
    records: tuple[StateRecord | None, ...],
    log_positions: tuple[int, ...],
    request_fingerprint: str,
) -> str:
    return "sha256:" + hashlib.sha256(_canonical_json_bytes({
        "request_fingerprint": request_fingerprint,
        "records": [
            None if record is None else {
                "key": _key_values(record.key),
                "document": _document_values(record.document),
                "revision": record.revision._provider_token(),
                "committed_at": record.committed_at.isoformat(),
            }
            for record in records
        ],
        "log_positions": list(log_positions),
    })).hexdigest()


def _namespace_values(value: StateNamespace) -> dict[str, object]:
    return {
        "kind": value.kind.value,
        "domain": value.domain,
        "tenant_id": value.tenant_id,
        "runtime_id": value.runtime_id,
        "plugin_name": value.plugin_name,
    }


def _key_values(value: StateKey) -> dict[str, object]:
    return {
        "namespace": _namespace_values(value.namespace),
        "object_type": value.object_type,
        "object_id": value.object_id,
    }


def _index_values(value: StateOrderedIndexKey) -> dict[str, object]:
    return {
        "namespace": _namespace_values(value.namespace),
        "name": value.name,
        "bucket": value.bucket,
    }


def _document_values(
    value: StateDocument | None,
) -> dict[str, object] | None:
    if value is None:
        return None
    return {
        "schema_name": value.schema_name,
        "schema_version": value.schema_version,
        "state_version": value.state_version,
        "epoch": value.epoch,
        "payload_sha256": hashlib.sha256(value.payload).hexdigest(),
    }


def _revision_value(value: object) -> str | None:
    if value is None:
        return None
    provider_token = getattr(value, "_provider_token", None)
    if not callable(provider_token):
        _invalid("revision")
    result = provider_token()
    if type(result) is not str:
        _invalid("revision")
    return result


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError):
        _invalid("canonical")


def _invalid(field: str) -> None:
    raise NsValidationError(
        "Delivery persistence value is invalid.",
        details={"component": "delivery_persistence", "field": field},
    )


def _partition_dimensions(value: str) -> tuple[int, int]:
    prefix = "layout-"
    separator = "-bucket-"
    if type(value) is not str or not value.startswith(prefix):
        _invalid("partition")
    generation_text, found, bucket_text = value[len(prefix):].partition(
        separator,
    )
    if (
        not found
        or not generation_text.isdecimal()
        or not bucket_text.isdecimal()
    ):
        _invalid("partition")
    generation = int(generation_text)
    bucket = int(bucket_text)
    if generation <= 0 or bucket < 0:
        _invalid("partition")
    return generation, bucket


__all__ = (
    "ContractTestRepositoryPersistence",
    "DeliveryAdmissionPersistence",
    "DeliveryPayloadPersistence",
    "DeliveryPersistencePartition",
    "DeliveryPersistenceTransaction",
    "DeliveryPersistenceTransactionResult",
    "DeliveryRegistryPersistence",
    "DeliverySchedulerPersistence",
    "StrongAuditPersistence",
    "contract_test_persistence",
)
