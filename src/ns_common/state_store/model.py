# -*- coding: utf-8 -*-
"""Immutable StateStore value, version, and transaction contracts."""

from __future__ import annotations

import re
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

    def __post_init__(self) -> None:
        if not isinstance(self.scope, StateAccessScope):
            _invalid("transaction.scope")
        if not isinstance(self.mutations, tuple) or not self.mutations:
            _invalid("transaction.mutations")
        if any(not isinstance(value, StateMutation) for value in self.mutations):
            _invalid("transaction.mutations")
        keys = tuple(value.key for value in self.mutations)
        if len(set(keys)) != len(keys):
            _invalid("transaction.duplicate_key")


@dataclass(frozen=True, slots=True, kw_only=True)
class StateTransactionResult:
    records: tuple[StateRecord | None, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.records, tuple) or any(
            value is not None and not isinstance(value, StateRecord)
            for value in self.records
        ):
            _invalid("transaction_result.records")


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
    "StateReadResult",
    "StateRecord",
    "StateRevision",
    "StateStoreHealth",
    "StateStoreHealthStatus",
    "StateTransaction",
    "StateTransactionResult",
)
