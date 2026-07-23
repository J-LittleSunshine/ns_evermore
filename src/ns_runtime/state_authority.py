# -*- coding: utf-8 -*-
"""Narrow runtime authority services built above the P08 StateStore contract."""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from ns_common.exceptions import NsValidationError
from ns_common.state_store import (
    StateAccessScope,
    StateAppendResult,
    StateAtomicScope,
    StateAuthorityKind,
    StateCallerCapability,
    StateDocument,
    StateKey,
    StateNamespace,
    StateNamespaceKind,
    StateRevision,
    StateStore,
)
from ns_runtime.processor.audit import (
    AuditConsistency,
    AuditSink,
    ProcessorAuditRecord,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class StrongAuditCommit:
    revision: StateRevision = field(repr=False)
    position: int
    committed_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.revision, StateRevision):
            _invalid("commit.revision")
        if (
            isinstance(self.position, bool)
            or not isinstance(self.position, int)
            or self.position <= 0
        ):
            _invalid("commit.position")
        if (
            not isinstance(self.committed_at, datetime)
            or self.committed_at.tzinfo is None
            or self.committed_at.utcoffset() is None
        ):
            _invalid("commit.committed_at")

    @classmethod
    def from_append_result(
        cls,
        result: StateAppendResult,
    ) -> "StrongAuditCommit":
        if not isinstance(result, StateAppendResult):
            _invalid("append_result")
        return cls(
            revision=result.revision,
            position=result.position,
            committed_at=result.committed_at,
        )


class StrongAuditAuthorityService(ABC):
    """Only authority service implementations may touch strong audit state."""

    @abstractmethod
    async def append(self, record: ProcessorAuditRecord) -> StrongAuditCommit:
        raise NotImplementedError


class StateStoreStrongAuditAuthorityService(StrongAuditAuthorityService):
    """Provider-neutral strong-audit binding; it never exposes StateStore."""

    _SCHEMA_NAME = "runtime.processor_audit"
    _SCHEMA_VERSION = 1

    def __init__(
        self,
        *,
        state_store: StateStore,
        namespace: StateNamespace,
    ) -> None:
        if not isinstance(state_store, StateStore):
            _invalid("state_store")
        if (
            not isinstance(namespace, StateNamespace)
            or namespace.kind is not StateNamespaceKind.AUDIT
        ):
            _invalid("namespace")
        self._state_store = state_store
        self._scope = state_store._issue_access_scope(
            atomic_scope=StateAtomicScope(
                namespace=namespace,
                partition="processor-final",
            ),
            authority=StateAuthorityKind.STRONG_AUDIT,
            caller="strong-audit-authority",
            capabilities=frozenset({StateCallerCapability.APPEND}),
        )
        self._key = StateKey(
            namespace=namespace,
            object_type="processor_audit_log",
            object_id="final",
        )

    async def append(self, record: ProcessorAuditRecord) -> StrongAuditCommit:
        if not isinstance(record, ProcessorAuditRecord):
            _invalid("record")
        if record.required_consistency is not AuditConsistency.STRONG_REQUIRED:
            _invalid("record.required_consistency")
        result = await self._state_store.append(
            scope=self._scope,
            key=self._key,
            document=StateDocument(
                schema_name=self._SCHEMA_NAME,
                schema_version=self._SCHEMA_VERSION,
                state_version=1,
                payload=_canonical_audit_bytes(record),
            ),
        )
        return StrongAuditCommit.from_append_result(result)


class AuthorityRoutingAuditSink(AuditSink):
    """Route strong records to authority and ordinary records to a local sink."""

    def __init__(
        self,
        *,
        strong_authority: StrongAuditAuthorityService,
        ordinary_sink: AuditSink,
    ) -> None:
        if not isinstance(strong_authority, StrongAuditAuthorityService):
            _invalid("strong_authority")
        if not isinstance(ordinary_sink, AuditSink):
            _invalid("ordinary_sink")
        self._strong_authority = strong_authority
        self._ordinary_sink = ordinary_sink

    async def emit(self, record: ProcessorAuditRecord) -> None:
        if not isinstance(record, ProcessorAuditRecord):
            _invalid("record")
        if record.required_consistency is AuditConsistency.STRONG_REQUIRED:
            commit = await self._strong_authority.append(record)
            if not isinstance(commit, StrongAuditCommit):
                _invalid("strong_authority.commit")
            return
        await self._ordinary_sink.emit(record)


def _canonical_audit_bytes(record: ProcessorAuditRecord) -> bytes:
    return json.dumps(
        {
            "action": record.action.value,
            "config_version": record.config_version,
            "error": record.error,
            "message_category": record.safe_summary.category,
            "message_type": record.safe_summary.message_type,
            "object_reference": record.safe_summary.object_reference,
            "occurred_at": record.occurred_at.isoformat().replace("+00:00", "Z"),
            "policy_version": record.policy_version,
            "processor": record.processor,
            "required_consistency": record.required_consistency.value,
            "trace_reference": record.trace.value,
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Strong audit authority value is invalid.",
        details={"component": "strong_audit_authority", "field": field_name},
    )


__all__ = (
    "AuthorityRoutingAuditSink",
    "StateStoreStrongAuditAuthorityService",
    "StrongAuditAuthorityService",
    "StrongAuditCommit",
)
