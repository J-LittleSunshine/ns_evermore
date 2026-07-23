# -*- coding: utf-8 -*-
"""Immutable StateStore value, version, and transaction contracts."""

from __future__ import annotations

import math
import re
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from ns_common.exceptions import NsValidationError

from .authority import StateAccessScope, StateNamespace


_NAME_PATTERN = re.compile(r"[a-z][a-z0-9_.-]{0,127}")
_OBJECT_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,511}")
_REVISION_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,255}")
_REVISION_ISSUER = object()


@dataclass(frozen=True, slots=True, kw_only=True)
class StateKey:
    namespace: StateNamespace
    object_type: str
    object_id: str = field(repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.namespace, StateNamespace):
            _invalid("key.namespace")
        _validate_name(self.object_type, "key.object_type")
        if (
            not isinstance(self.object_id, str)
            or _OBJECT_ID_PATTERN.fullmatch(self.object_id) is None
        ):
            _invalid("key.object_id")


@dataclass(frozen=True, slots=True, init=False)
class StateRevision:
    """Opaque provider-issued compare-and-set token.

    Callers can retain and compare token objects for equality, but cannot
    construct or parse a revision through the public contract.
    """

    _token: str = field(repr=False)

    def __init__(self, token: str, *, _issuer: object = None) -> None:
        if _issuer is not _REVISION_ISSUER:
            _invalid("revision.issuer")
        if not isinstance(token, str) or _REVISION_PATTERN.fullmatch(token) is None:
            _invalid("revision.token")
        object.__setattr__(self, "_token", token)

    @classmethod
    def _issue(cls, token: str) -> "StateRevision":
        """Provider-only constructor used by concrete conformance subjects."""

        return cls(token, _issuer=_REVISION_ISSUER)

    def _provider_token(self) -> str:
        return self._token

    def __repr__(self) -> str:
        return "StateRevision(<opaque>)"


@dataclass(frozen=True, slots=True, kw_only=True)
class StateDocument:
    schema_name: str
    schema_version: int
    state_version: int
    payload: bytes = field(repr=False)
    epoch: int | None = None

    def __post_init__(self) -> None:
        _validate_name(self.schema_name, "document.schema_name")
        _positive_int(self.schema_version, "document.schema_version")
        _positive_int(self.state_version, "document.state_version")
        if not isinstance(self.payload, bytes):
            _invalid("document.payload")
        if self.epoch is not None:
            _non_negative_int(self.epoch, "document.epoch")


@dataclass(frozen=True, slots=True, kw_only=True)
class StateRecord:
    key: StateKey
    document: StateDocument = field(repr=False)
    revision: StateRevision = field(repr=False)
    committed_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.key, StateKey):
            _invalid("record.key")
        if not isinstance(self.document, StateDocument):
            _invalid("record.document")
        if not isinstance(self.revision, StateRevision):
            _invalid("record.revision")
        object.__setattr__(
            self,
            "committed_at",
            _utc(self.committed_at, "record.committed_at"),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class StateAssertion:
    expect_absent: bool = False
    expected_revision: StateRevision | None = field(default=None, repr=False)
    expected_state_version: int | None = None
    expected_epoch: int | None = None

    def __post_init__(self) -> None:
        if type(self.expect_absent) is not bool:
            _invalid("assertion.expect_absent")
        if self.expect_absent:
            if any(
                value is not None
                for value in (
                    self.expected_revision,
                    self.expected_state_version,
                    self.expected_epoch,
                )
            ):
                _invalid("assertion.absent_combination")
            return
        if not isinstance(self.expected_revision, StateRevision):
            _invalid("assertion.expected_revision")
        if self.expected_state_version is not None:
            _positive_int(
                self.expected_state_version,
                "assertion.expected_state_version",
            )
        if self.expected_epoch is not None:
            _non_negative_int(self.expected_epoch, "assertion.expected_epoch")

    @classmethod
    def absent(cls) -> "StateAssertion":
        return cls(expect_absent=True)

    @classmethod
    def matches(
        cls,
        revision: StateRevision,
        *,
        state_version: int | None = None,
        epoch: int | None = None,
    ) -> "StateAssertion":
        return cls(
            expected_revision=revision,
            expected_state_version=state_version,
            expected_epoch=epoch,
        )


class StateMutationKind(str, Enum):
    CREATE = "create"
    REPLACE = "replace"
    DELETE = "delete"


class StateOrderedIndexMutationKind(str, Enum):
    ADD = "add"
    REMOVE = "remove"


@dataclass(frozen=True, slots=True, kw_only=True)
class StateOrderedIndexKey:
    namespace: StateNamespace
    name: str
    bucket: str

    def __post_init__(self) -> None:
        if not isinstance(self.namespace, StateNamespace):
            _invalid("ordered_index.namespace")
        _validate_name(self.name, "ordered_index.name")
        _validate_name(self.bucket, "ordered_index.bucket")


@dataclass(frozen=True, slots=True, kw_only=True)
class StateOrderedIndexMutation:
    index: StateOrderedIndexKey
    kind: StateOrderedIndexMutationKind
    member: str
    score: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.index, StateOrderedIndexKey):
            _invalid("ordered_index_mutation.index")
        if not isinstance(self.kind, StateOrderedIndexMutationKind):
            _invalid("ordered_index_mutation.kind")
        if not isinstance(self.member, str) or _OBJECT_ID_PATTERN.fullmatch(self.member) is None:
            _invalid("ordered_index_mutation.member")
        if self.kind is StateOrderedIndexMutationKind.ADD:
            if type(self.score) not in {int, float} or not math.isfinite(self.score):
                _invalid("ordered_index_mutation.score")
        elif self.score is not None:
            _invalid("ordered_index_mutation.score")


@dataclass(frozen=True, slots=True, kw_only=True)
class StateRecordReadAssertion:
    """Read-only transaction precondition over one authority record."""

    key: StateKey
    expect_present: bool
    expected_revision: StateRevision | None = field(default=None, repr=False)
    expected_state_version: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.key, StateKey):
            _invalid("record_assertion.key")
        if type(self.expect_present) is not bool:
            _invalid("record_assertion.expect_present")
        if not self.expect_present and (
            self.expected_revision is not None
            or self.expected_state_version is not None
        ):
            _invalid("record_assertion.absent_combination")
        if (
            self.expected_revision is not None
            and not isinstance(self.expected_revision, StateRevision)
        ):
            _invalid("record_assertion.expected_revision")
        if self.expected_state_version is not None:
            _positive_int(
                self.expected_state_version,
                "record_assertion.expected_state_version",
            )

    @classmethod
    def absent(cls, key: StateKey) -> "StateRecordReadAssertion":
        return cls(key=key, expect_present=False)

    @classmethod
    def present(
        cls,
        key: StateKey,
        *,
        revision: StateRevision | None = None,
        state_version: int | None = None,
    ) -> "StateRecordReadAssertion":
        return cls(
            key=key,
            expect_present=True,
            expected_revision=revision,
            expected_state_version=state_version,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class StateOrderedIndexReadAssertion:
    """Read-only transaction precondition over one ordered-index member."""

    index: StateOrderedIndexKey
    member: str
    expect_present: bool
    expected_score: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.index, StateOrderedIndexKey):
            _invalid("ordered_index_assertion.index")
        if (
            not isinstance(self.member, str)
            or _OBJECT_ID_PATTERN.fullmatch(self.member) is None
        ):
            _invalid("ordered_index_assertion.member")
        if type(self.expect_present) is not bool:
            _invalid("ordered_index_assertion.expect_present")
        if not self.expect_present and self.expected_score is not None:
            _invalid("ordered_index_assertion.absent_combination")
        if self.expected_score is not None and (
            type(self.expected_score) not in {int, float}
            or not math.isfinite(self.expected_score)
        ):
            _invalid("ordered_index_assertion.expected_score")

    @classmethod
    def absent(
        cls,
        index: StateOrderedIndexKey,
        member: str,
    ) -> "StateOrderedIndexReadAssertion":
        return cls(index=index, member=member, expect_present=False)

    @classmethod
    def present(
        cls,
        index: StateOrderedIndexKey,
        member: str,
        *,
        score: float | None = None,
    ) -> "StateOrderedIndexReadAssertion":
        return cls(
            index=index,
            member=member,
            expect_present=True,
            expected_score=score,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class StateTransitionLogAppend:
    key: StateKey
    document: StateDocument = field(repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.key, StateKey) or not isinstance(self.document, StateDocument):
            _invalid("transition_log_append")


@dataclass(frozen=True, slots=True, kw_only=True)
class StateOrderedIndexEntry:
    member: str
    score: float

    def __post_init__(self) -> None:
        if not isinstance(self.member, str) or _OBJECT_ID_PATTERN.fullmatch(self.member) is None:
            _invalid("ordered_index_entry.member")
        if type(self.score) not in {int, float} or not math.isfinite(self.score):
            _invalid("ordered_index_entry.score")


@dataclass(frozen=True, slots=True, kw_only=True)
class StateOrderedIndexCursor:
    member: str
    score: float

    def __post_init__(self) -> None:
        StateOrderedIndexEntry(member=self.member, score=self.score)


@dataclass(frozen=True, slots=True, kw_only=True)
class StateOrderedIndexReadResult:
    entries: tuple[StateOrderedIndexEntry, ...]
    observed_at: datetime
    total_count: int
    next_cursor: StateOrderedIndexCursor | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.entries, tuple) or any(
            not isinstance(value, StateOrderedIndexEntry) for value in self.entries
        ):
            _invalid("ordered_index_result.entries")
        object.__setattr__(self, "observed_at", _utc(self.observed_at, "ordered_index_result.observed_at"))
        _non_negative_int(self.total_count, "ordered_index_result.total_count")
        if self.total_count < len(self.entries):
            _invalid("ordered_index_result.total_count")
        if self.next_cursor is not None:
            if not isinstance(self.next_cursor, StateOrderedIndexCursor):
                _invalid("ordered_index_result.next_cursor")
            if not self.entries or (
                self.next_cursor.member != self.entries[-1].member
                or self.next_cursor.score != self.entries[-1].score
            ):
                _invalid("ordered_index_result.next_cursor_binding")


@dataclass(frozen=True, slots=True, kw_only=True)
class StateMutation:
    key: StateKey
    assertion: StateAssertion
    kind: StateMutationKind
    document: StateDocument | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.key, StateKey):
            _invalid("mutation.key")
        if not isinstance(self.assertion, StateAssertion):
            _invalid("mutation.assertion")
        if not isinstance(self.kind, StateMutationKind):
            _invalid("mutation.kind")
        if self.kind is StateMutationKind.CREATE:
            if not self.assertion.expect_absent or not isinstance(self.document, StateDocument):
                _invalid("mutation.create")
        elif self.kind is StateMutationKind.REPLACE:
            if self.assertion.expect_absent or not isinstance(self.document, StateDocument):
                _invalid("mutation.replace")
        elif self.kind is StateMutationKind.DELETE:
            if self.assertion.expect_absent or self.document is not None:
                _invalid("mutation.delete")


@dataclass(frozen=True, slots=True, kw_only=True)
class StateTransaction:
    scope: StateAccessScope
    mutations: tuple[StateMutation, ...]
    ordered_index_mutations: tuple[StateOrderedIndexMutation, ...] = ()
    log_appends: tuple[StateTransitionLogAppend, ...] = ()
    record_assertions: tuple[StateRecordReadAssertion, ...] = ()
    ordered_index_assertions: tuple[StateOrderedIndexReadAssertion, ...] = ()
    _result_binding: object = field(
        default_factory=object, init=False, repr=False, compare=False,
    )
    _result_key: bytes = field(
        default_factory=lambda: secrets.token_bytes(32),
        init=False, repr=False, compare=False,
    )
    _pending_result_token: object | None = field(
        default=None, init=False, repr=False, compare=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.scope, StateAccessScope):
            _invalid("transaction.scope")
        if (not isinstance(self.mutations, tuple)
                or not isinstance(self.ordered_index_mutations, tuple)
                or not isinstance(self.log_appends, tuple)
                or not isinstance(self.record_assertions, tuple)
                or not isinstance(self.ordered_index_assertions, tuple)
                or not (self.mutations or self.ordered_index_mutations or self.log_appends)):
            _invalid("transaction.mutations")
        if any(not isinstance(value, StateMutation) for value in self.mutations):
            _invalid("transaction.mutations")
        keys = tuple(value.key for value in self.mutations)
        if len(set(keys)) != len(keys):
            _invalid("transaction.duplicate_key")
        if any(not isinstance(value, StateOrderedIndexMutation)
               for value in self.ordered_index_mutations):
            _invalid("transaction.ordered_index_mutations")
        if any(not isinstance(value, StateTransitionLogAppend) for value in self.log_appends):
            _invalid("transaction.log_appends")
        if any(
            not isinstance(value, StateRecordReadAssertion)
            for value in self.record_assertions
        ):
            _invalid("transaction.record_assertions")
        if any(
            not isinstance(value, StateOrderedIndexReadAssertion)
            for value in self.ordered_index_assertions
        ):
            _invalid("transaction.ordered_index_assertions")
        asserted_record_keys = tuple(value.key for value in self.record_assertions)
        if len(set(asserted_record_keys)) != len(asserted_record_keys):
            _invalid("transaction.duplicate_record_assertion")
        asserted_index_members = tuple(
            (value.index, value.member)
            for value in self.ordered_index_assertions
        )
        if len(set(asserted_index_members)) != len(asserted_index_members):
            _invalid("transaction.duplicate_ordered_index_assertion")

    def _begin_result_construction(self) -> object:
        token = object()
        object.__setattr__(self, "_pending_result_token", token)
        return token

    def _consume_result_token(self, token: object) -> bool:
        return token is not None and self._pending_result_token is token

    def _end_result_construction(self, token: object) -> None:
        if self._pending_result_token is token:
            object.__setattr__(self, "_pending_result_token", None)

    def __copy__(self) -> "StateTransaction":
        del self
        _invalid("transaction.copy")

    def __deepcopy__(self, memo: dict[int, object]) -> "StateTransaction":
        del self, memo
        _invalid("transaction.copy")


@dataclass(frozen=True, slots=True, kw_only=True, init=False)
class StateTransactionResult:
    records: tuple[StateRecord | None, ...]
    log_positions: tuple[int, ...] = ()
    transaction_fingerprint: str
    _transaction_identity: StateTransaction = field(repr=False, compare=False)
    _transaction_binding: object = field(repr=False, compare=False)
    _binding_signature: bytes = field(repr=False, compare=False)

    def __init__(
        self,
        *,
        records: tuple[StateRecord | None, ...],
        log_positions: tuple[int, ...] = (),
        _transaction: StateTransaction | None = None,
        _construction_token: object | None = None,
    ) -> None:
        if (
            type(self) is not StateTransactionResult
            or type(_transaction) is not StateTransaction
            or not _transaction._consume_result_token(_construction_token)
        ):
            _invalid("transaction_result.issuer")
        transaction_fingerprint = _state_transaction_fingerprint(_transaction)
        for name, value in (
            ("records", records),
            ("log_positions", log_positions),
            ("transaction_fingerprint", transaction_fingerprint),
            ("_transaction_identity", _transaction),
            ("_transaction_binding", _transaction._result_binding),
            ("_binding_signature", b""),
        ):
            object.__setattr__(self, name, value)
        self._validate_for_transaction(_transaction)
        object.__setattr__(
            self,
            "_binding_signature",
            _state_transaction_result_signature(self, _transaction),
        )

    @classmethod
    def for_transaction(
        cls,
        transaction: StateTransaction,
        *,
        records: tuple[StateRecord | None, ...],
        log_positions: tuple[int, ...] = (),
    ) -> "StateTransactionResult":
        if cls is not StateTransactionResult or type(transaction) is not StateTransaction:
            _invalid("transaction_result.transaction")
        token = transaction._begin_result_construction()
        try:
            return cls(
                records=records,
                log_positions=log_positions,
                _transaction=transaction,
                _construction_token=token,
            )
        finally:
            transaction._end_result_construction(token)

    def _validate_for_transaction(self, transaction: StateTransaction) -> None:
        if not isinstance(self.records, tuple) or any(
            value is not None and not isinstance(value, StateRecord)
            for value in self.records
        ):
            _invalid("transaction_result.records")
        if not isinstance(self.log_positions, tuple) or any(
            isinstance(value, bool) or not isinstance(value, int) or value <= 0
            for value in self.log_positions
        ):
            _invalid("transaction_result.log_positions")
        if len(self.records) != len(transaction.mutations):
            _invalid("transaction_result.records_cardinality")
        if len(self.log_positions) != len(transaction.log_appends):
            _invalid("transaction_result.log_positions_cardinality")
        for mutation, record in zip(transaction.mutations, self.records):
            if mutation.kind is StateMutationKind.DELETE:
                if record is not None:
                    _invalid("transaction_result.deleted_record")
                continue
            if (
                not isinstance(record, StateRecord)
                or record.key != mutation.key
                or record.document != mutation.document
            ):
                _invalid("transaction_result.record_binding")
        if (
            self.transaction_fingerprint
            != _state_transaction_fingerprint(transaction)
        ):
            _invalid("transaction_result.transaction_fingerprint")

    def is_for_transaction(self, transaction: StateTransaction) -> bool:
        if type(transaction) is not StateTransaction:
            return False
        try:
            self._validate_for_transaction(transaction)
        except NsValidationError:
            return False
        return bool(
            type(self) is StateTransactionResult
            and self._transaction_identity is transaction
            and self._transaction_binding is transaction._result_binding
            and hmac.compare_digest(
                self._binding_signature,
                _state_transaction_result_signature(self, transaction),
            )
        )

    def __copy__(self) -> "StateTransactionResult":
        del self
        _invalid("transaction_result.copy")

    def __deepcopy__(self, memo: dict[int, object]) -> "StateTransactionResult":
        del self, memo
        _invalid("transaction_result.copy")


def _state_transaction_fingerprint(transaction: StateTransaction) -> str:
    def document_value(document: StateDocument | None) -> object:
        if document is None:
            return None
        return {
            "schema_name": document.schema_name,
            "schema_version": document.schema_version,
            "state_version": document.state_version,
            "epoch": document.epoch,
            "payload_sha256": hashlib.sha256(document.payload).hexdigest(),
        }

    payload = {
        "scope": {
            "namespace": repr(transaction.scope.namespace),
            "partition": transaction.scope.atomic_scope.partition,
            "authority": transaction.scope.authority.value,
            "caller": transaction.scope.caller,
            "capabilities": sorted(
                capability.value for capability in transaction.scope.capabilities
            ),
        },
        "mutations": [{
            "key": repr(value.key),
            "kind": value.kind.value,
            "assertion": repr(value.assertion),
            "document": document_value(value.document),
        } for value in transaction.mutations],
        "ordered_index_mutations": [
            repr(value) for value in transaction.ordered_index_mutations
        ],
        "log_appends": [{
            "key": repr(value.key),
            "document": document_value(value.document),
        } for value in transaction.log_appends],
        "record_assertions": [
            repr(value) for value in transaction.record_assertions
        ],
        "ordered_index_assertions": [
            repr(value) for value in transaction.ordered_index_assertions
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _state_transaction_result_signature(
    result: StateTransactionResult,
    transaction: StateTransaction,
) -> bytes:
    payload = json.dumps({
        "transaction_fingerprint": result.transaction_fingerprint,
        "records": [
            None if record is None else {
                "key": repr(record.key),
                "document": {
                    "schema_name": record.document.schema_name,
                    "schema_version": record.document.schema_version,
                    "state_version": record.document.state_version,
                    "epoch": record.document.epoch,
                    "payload_sha256": hashlib.sha256(
                        record.document.payload,
                    ).hexdigest(),
                },
                "revision": record.revision._provider_token(),
                "committed_at": record.committed_at.isoformat(),
            }
            for record in result.records
        ],
        "log_positions": result.log_positions,
    }, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hmac.new(transaction._result_key, payload, hashlib.sha256).digest()


class StateConsistency(str, Enum):
    LINEARIZABLE = "linearizable"
    AT_LEAST_REVISION = "at_least_revision"
    STALE_ALLOWED = "stale_allowed"


@dataclass(frozen=True, slots=True, kw_only=True)
class StateReadResult:
    record: StateRecord | None
    observed_at: datetime
    stale: bool

    def __post_init__(self) -> None:
        if self.record is not None and not isinstance(self.record, StateRecord):
            _invalid("read_result.record")
        object.__setattr__(
            self,
            "observed_at",
            _utc(self.observed_at, "read_result.observed_at"),
        )
        if type(self.stale) is not bool:
            _invalid("read_result.stale")


@dataclass(frozen=True, slots=True, kw_only=True)
class StateScanResult:
    records: tuple[StateRecord, ...]
    next_cursor: str | None
    observed_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.records, tuple) or any(
            not isinstance(value, StateRecord) for value in self.records
        ):
            _invalid("scan_result.records")
        if self.next_cursor is not None and (
            type(self.next_cursor) is not str
            or not self.next_cursor.isdigit()
            or self.next_cursor == "0"
        ):
            _invalid("scan_result.next_cursor")
        object.__setattr__(
            self,
            "observed_at",
            _utc(self.observed_at, "scan_result.observed_at"),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class StateAppendResult:
    revision: StateRevision = field(repr=False)
    position: int
    committed_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.revision, StateRevision):
            _invalid("append_result.revision")
        _positive_int(self.position, "append_result.position")
        object.__setattr__(
            self,
            "committed_at",
            _utc(self.committed_at, "append_result.committed_at"),
        )


class StateStoreHealthStatus(str, Enum):
    NOT_READY = "not_ready"
    READY = "ready"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    CLOSED = "closed"


@dataclass(frozen=True, slots=True, kw_only=True)
class StateStoreHealth:
    status: StateStoreHealthStatus
    checked_at: datetime
    contract_generation: int

    def __post_init__(self) -> None:
        if not isinstance(self.status, StateStoreHealthStatus):
            _invalid("health.status")
        object.__setattr__(
            self,
            "checked_at",
            _utc(self.checked_at, "health.checked_at"),
        )
        _positive_int(self.contract_generation, "health.contract_generation")

    @property
    def ready(self) -> bool:
        return self.status is StateStoreHealthStatus.READY


def _validate_name(value: object, field_name: str) -> None:
    if not isinstance(value, str) or _NAME_PATTERN.fullmatch(value) is None:
        _invalid(field_name)


def _positive_int(value: object, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        _invalid(field_name)


def _non_negative_int(value: object, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        _invalid(field_name)


def _utc(value: object, field_name: str) -> datetime:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        _invalid(field_name)
    return value.astimezone(timezone.utc)


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "StateStore contract value is invalid.",
        details={"component": "state_store", "field": field_name},
    )


__all__ = (
    "StateAppendResult",
    "StateAssertion",
    "StateConsistency",
    "StateDocument",
    "StateKey",
    "StateMutation",
    "StateMutationKind",
    "StateOrderedIndexEntry",
    "StateOrderedIndexCursor",
    "StateOrderedIndexKey",
    "StateOrderedIndexMutation",
    "StateOrderedIndexMutationKind",
    "StateOrderedIndexReadAssertion",
    "StateOrderedIndexReadResult",
    "StateReadResult",
    "StateRecordReadAssertion",
    "StateRecord",
    "StateRevision",
    "StateScanResult",
    "StateStoreHealth",
    "StateStoreHealthStatus",
    "StateTransaction",
    "StateTransitionLogAppend",
    "StateTransactionResult",
)
