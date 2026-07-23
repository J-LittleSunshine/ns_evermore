# -*- coding: utf-8 -*-
"""DR-1 atomic authority over the backend-neutral P08 StateStore."""

from __future__ import annotations

import base64
import hashlib
import json
from abc import ABC, abstractmethod
import dataclasses
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from ns_common.exceptions import (
    NsRuntimeStateStoreConflictError, NsRuntimeStateStoreUnavailableError,
    NsValidationError,
)
from ns_common.state_store import (
    StateAccessScope, StateAssertion, StateAtomicScope, StateAuthorityKind,
    StateCallerCapability, StateConsistency, StateDocument, StateKey,
    StateMutation, StateMutationKind, StateNamespace, StateStore,
    StateRecord, StateTransaction, StateTransactionResult,
    StateOrderedIndexKey, StateOrderedIndexMutation,
    StateOrderedIndexMutationKind, StateTransitionLogAppend,
)

from .models import (
    ATOMIC_ADMISSION_VERSION, DEDUP_EVIDENCE_VERSION, DR1_SCHEMA_VERSION, DedupEvidence,
    DeliveryRecord, DeliverySummaryStatus, DuplicateLifecycle,
    DeliveryRecordStatus, AdmissionPriority,
    MessageDeliverySummary, cancel_initializing_graph,
    compute_dedup_evidence_fingerprint, validate_initialization_graph,
)
from ns_runtime.routing import ResolvedRoutingPlan
from .serde import delivery_to_dict, summary_to_dict


@dataclass(frozen=True, slots=True, kw_only=True)
class AdmissionInitialization:
    schema_version: str = ATOMIC_ADMISSION_VERSION
    plan: ResolvedRoutingPlan
    root_summary: MessageDeliverySummary
    shard_summaries: tuple[MessageDeliverySummary, ...]
    deliveries: tuple[DeliveryRecord, ...]
    dedup: DedupEvidence
    initialization_batch_size: int
    payload_body_ref: str | None = None
    payload_body: bytes | None = dataclasses.field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.schema_version != ATOMIC_ADMISSION_VERSION:
            _invalid("initialization.schema_version")
        if (isinstance(self.initialization_batch_size, bool)
                or not isinstance(self.initialization_batch_size, int)
                or self.initialization_batch_size <= 0):
            _invalid("initialization.batch_size")
        if (self.payload_body_ref is None) is not (self.payload_body is None):
            _invalid("initialization.payload_body")
        if self.payload_body_ref is not None:
            if type(self.payload_body_ref) is not str or not self.payload_body_ref:
                _invalid("initialization.payload_body_ref")
            if not isinstance(self.payload_body, bytes) or not self.payload_body:
                _invalid("initialization.payload_body")
            if any(
                delivery.payload_evidence.body_ref != self.payload_body_ref
                for delivery in self.deliveries
            ):
                _invalid("initialization.payload_body_binding")
            evidence = self.root_summary.payload_evidence
            if (
                evidence is None
                or evidence.body_ref != self.payload_body_ref
                or evidence.size_bytes != len(self.payload_body)
                or evidence.digest
                != "sha256:" + hashlib.sha256(self.payload_body).hexdigest()
            ):
                _invalid("initialization.payload_body_evidence")
        validate_initialization_graph(
            plan=self.plan, root=self.root_summary,
            shards=self.shard_summaries, deliveries=self.deliveries,
            dedup=self.dedup,
        )


class AtomicAdmissionOutcome(str, Enum):
    CREATED = "created"
    DUPLICATE = "duplicate"
    CANCELLED_INITIALIZATION = "cancelled_initialization"


@dataclass(frozen=True, slots=True, kw_only=True)
class AtomicAdmissionResult:
    schema_version: str = ATOMIC_ADMISSION_VERSION
    outcome: AtomicAdmissionOutcome
    root_summary: MessageDeliverySummary | None
    dedup: DedupEvidence

    def __post_init__(self) -> None:
        if self.schema_version != ATOMIC_ADMISSION_VERSION:
            _invalid("atomic_result.schema_version")
        if not isinstance(self.outcome, AtomicAdmissionOutcome):
            _invalid("atomic_result.outcome")
        if not isinstance(self.dedup, DedupEvidence):
            _invalid("atomic_result.dedup")
        if self.outcome in {
            AtomicAdmissionOutcome.CREATED,
            AtomicAdmissionOutcome.CANCELLED_INITIALIZATION,
        }:
            if not isinstance(self.root_summary, MessageDeliverySummary):
                _invalid("atomic_result.root_summary")
            if self.root_summary.summary_id != self.dedup.summary_id:
                _invalid("atomic_result.summary_dedup")
            if (self.outcome is AtomicAdmissionOutcome.CANCELLED_INITIALIZATION
                    and (self.root_summary.status
                         is not DeliverySummaryStatus.CANCELLED
                         or self.dedup.lifecycle is not DuplicateLifecycle.CANCELLED)):
                _invalid("atomic_result.cancelled_initialization")
        elif self.root_summary is not None:
            _invalid("atomic_result.duplicate_summary")


class DeliveryAdmissionStore(ABC):
    """One atomic dedup + Summary + prepared DeliveryRecord operation."""

    @abstractmethod
    async def initialize(self, value: AdmissionInitialization) -> AtomicAdmissionResult:
        raise NotImplementedError


class UnavailableDeliveryAdmissionStore(DeliveryAdmissionStore):
    async def initialize(self, value: AdmissionInitialization) -> AtomicAdmissionResult:
        if not isinstance(value, AdmissionInitialization):
            _invalid("unavailable.initialization")
        raise NsRuntimeStateStoreUnavailableError(details={
            "component": "delivery_admission", "operation": "initialize",
            "reason": "strong_provider_unavailable",
        })


class StateStoreDeliveryAdmissionStore(DeliveryAdmissionStore):
    """Production adapter. It never falls back to cache or process memory."""

    def __init__(self, store: StateStore) -> None:
        if not isinstance(store, StateStore):
            _invalid("store")
        self._store = store

    async def initialize(self, value: AdmissionInitialization) -> AtomicAdmissionResult:
        if not isinstance(value, AdmissionInitialization):
            _invalid("initialization")
        namespace = StateNamespace.tenant(
            tenant_id=value.root_summary.tenant_id, domain="delivery",
        )
        scope = StateAccessScope(
            atomic_scope=StateAtomicScope(
                namespace=namespace,
                partition=f"bucket-{value.root_summary.authority_bucket_id}",
            ),
            authority=StateAuthorityKind.DELIVERY_ADMISSION,
            caller="delivery.admission",
            capabilities=frozenset({
                StateCallerCapability.READ, StateCallerCapability.TRANSACT,
                StateCallerCapability.ORDERED_INDEX, StateCallerCapability.APPEND,
            }),
        )
        if not value.deliveries:
            mutations = self._initial_mutations(
                namespace, value, value.root_summary,
                value.shard_summaries, (),
            )
            try:
                result = await self._transact(scope, mutations)
            except NsRuntimeStateStoreConflictError:
                existing = await self._read_dedup(scope, namespace, value.dedup)
                return AtomicAdmissionResult(
                    outcome=AtomicAdmissionOutcome.DUPLICATE,
                    root_summary=None, dedup=existing,
                )
            self._validate_commit(result, mutations)
            return AtomicAdmissionResult(
                outcome=AtomicAdmissionOutcome.CREATED,
                root_summary=value.root_summary, dedup=value.dedup,
            )

        batches = tuple(
            value.deliveries[offset:offset + value.initialization_batch_size]
            for offset in range(0, len(value.deliveries), value.initialization_batch_size)
        )
        created = batches[0]
        current_root, current_shards = self._progress_summaries(
            value, created=created, state_version=1,
        )
        mutations = self._initial_mutations(
            namespace, value, current_root, current_shards, created,
        )
        try:
            result = await self._transact(scope, mutations)
        except NsRuntimeStateStoreConflictError:
            existing = await self._read_dedup(scope, namespace, value.dedup)
            return AtomicAdmissionResult(
                outcome=AtomicAdmissionOutcome.DUPLICATE,
                root_summary=None, dedup=existing,
            )
        self._validate_commit(result, mutations)
        records = self._record_map(result)

        for batch_number, batch in enumerate(batches[1:], start=2):
            next_created = created + batch
            next_root, next_shards = self._progress_summaries(
                value, created=next_created, state_version=batch_number,
            )
            mutations = tuple(
                self._create_mutation(namespace, "delivery",
                                      delivery.delivery_id,
                                      delivery.state_version,
                                      _delivery_dict(delivery))
                for delivery in batch
            ) + self._summary_replacements(
                namespace, records, next_root, next_shards,
            )
            try:
                result = await self._transact(scope, mutations)
            except NsRuntimeStateStoreConflictError:
                return await self._cancel_after_failure(
                    scope=scope, namespace=namespace, value=value,
                    current_root=current_root, current_shards=current_shards,
                    created=created, records=records,
                )
            self._validate_commit(result, mutations)
            records.update(self._record_map(result))
            created = next_created
            current_root, current_shards = next_root, next_shards

        mutations = self._summary_replacements(
            namespace, records, value.root_summary, value.shard_summaries,
        )
        try:
            result = await self._transact(scope, mutations)
        except NsRuntimeStateStoreConflictError:
            return await self._cancel_after_failure(
                scope=scope, namespace=namespace, value=value,
                current_root=current_root, current_shards=current_shards,
                created=created, records=records,
            )
        self._validate_commit(result, mutations)
        return AtomicAdmissionResult(
            outcome=AtomicAdmissionOutcome.CREATED,
            root_summary=value.root_summary,
            dedup=value.dedup,
        )

    def _initial_mutations(
        self, namespace: StateNamespace, value: AdmissionInitialization,
        root: MessageDeliverySummary,
        shards: tuple[MessageDeliverySummary, ...],
        deliveries: tuple[DeliveryRecord, ...],
    ) -> tuple[StateMutation, ...]:
        payload_mutations = (() if value.payload_body_ref is None else (
            self._create_mutation(
                namespace, "payload_body", value.payload_body_ref, 1,
                {
                    "schema_version": "delivery-payload-body-1",
                    "body_ref": value.payload_body_ref,
                    "size_bytes": len(value.payload_body or b""),
                    "digest": "sha256:" + hashlib.sha256(
                        value.payload_body or b""
                    ).hexdigest(),
                    "body_base64": base64.b64encode(
                        value.payload_body or b""
                    ).decode("ascii"),
                },
            ),
        ))
        return (
            self._create_mutation(
                namespace, "dedup", _key_digest(
                    value.dedup.tenant_id, value.dedup.message_id,
                    value.dedup.target_fingerprint,
                ), 1, _dedup_dict(value.dedup), object_id_is_digest=True,
            ),
        ) + payload_mutations + tuple(
            self._create_mutation(
                namespace, "summary", summary.summary_id,
                summary.state_version, _summary_dict(summary),
            )
            for summary in (root,) + shards
        ) + tuple(
            self._create_mutation(
                namespace, "delivery", delivery.delivery_id,
                delivery.state_version, _delivery_dict(delivery),
            )
            for delivery in deliveries
        )

    @staticmethod
    def _create_mutation(
        namespace: StateNamespace, kind: str, identifier: str,
        state_version: int, payload: dict[str, object],
        *, object_id_is_digest: bool = False,
    ) -> StateMutation:
        return StateMutation(
            key=StateKey(
                namespace=namespace, object_type=kind,
                object_id=(identifier if object_id_is_digest
                           else _key_digest(identifier)),
            ),
            assertion=StateAssertion.absent(), kind=StateMutationKind.CREATE,
            document=StateDocument(
                schema_name=f"delivery_{kind}", schema_version=1,
                state_version=state_version,
                payload=json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(),
            ),
        )

    @staticmethod
    def _progress_summaries(
        value: AdmissionInitialization, *, created: tuple[DeliveryRecord, ...],
        state_version: int,
    ) -> tuple[MessageDeliverySummary, tuple[MessageDeliverySummary, ...]]:
        by_shard: dict[int | None, int] = {}
        for delivery in created:
            by_shard[delivery.shard_index] = by_shard.get(delivery.shard_index, 0) + 1

        def progress(summary: MessageDeliverySummary) -> MessageDeliverySummary:
            created_count = (
                len(created) if summary.shard_index is None
                else by_shard.get(summary.shard_index, 0)
            )
            intended = summary.accepted_count
            return dataclasses.replace(
                summary, status=DeliverySummaryStatus.INITIALIZING,
                accepted_count=created_count, prepared_count=created_count,
                not_initialized_count=intended - created_count,
                state_version=state_version,
            )

        return progress(value.root_summary), tuple(
            progress(summary) for summary in value.shard_summaries
        )

    def _summary_replacements(
        self, namespace: StateNamespace,
        records: dict[StateKey, StateRecord],
        root: MessageDeliverySummary,
        shards: tuple[MessageDeliverySummary, ...],
    ) -> tuple[StateMutation, ...]:
        return tuple(
            self._replace_mutation(
                records, StateKey(
                    namespace=namespace, object_type="summary",
                    object_id=_key_digest(summary.summary_id),
                ), summary.state_version, _summary_dict(summary),
            )
            for summary in (root,) + shards
        )

    @staticmethod
    def _replace_mutation(
        records: dict[StateKey, StateRecord], key: StateKey,
        state_version: int, payload: dict[str, object],
    ) -> StateMutation:
        record = records.get(key)
        if record is None:
            raise NsRuntimeStateStoreUnavailableError(details={
                "component": "delivery_admission",
                "operation": "initialize_progress",
                "reason": "commit_record_missing",
            })
        return StateMutation(
            key=key,
            assertion=StateAssertion.matches(
                record.revision,
                state_version=record.document.state_version,
            ),
            kind=StateMutationKind.REPLACE,
            document=StateDocument(
                schema_name=record.document.schema_name,
                schema_version=record.document.schema_version,
                state_version=state_version,
                payload=json.dumps(payload, sort_keys=True,
                                   separators=(",", ":")).encode(),
            ),
        )

    async def _cancel_after_failure(
        self, *, scope: StateAccessScope, namespace: StateNamespace,
        value: AdmissionInitialization, current_root: MessageDeliverySummary,
        current_shards: tuple[MessageDeliverySummary, ...],
        created: tuple[DeliveryRecord, ...],
        records: dict[StateKey, StateRecord],
    ) -> AtomicAdmissionResult:
        cancelled_root, cancelled_shards, cancelled_deliveries = (
            cancel_initializing_graph(
                root=current_root, shards=current_shards,
                created_deliveries=created,
                cancelled_at=value.root_summary.updated_at,
            )
        )
        dedup_values = {
            "tenant_id": value.dedup.tenant_id,
            "message_id": value.dedup.message_id,
            "target_fingerprint": value.dedup.target_fingerprint,
            "summary_id": value.dedup.summary_id,
            "lifecycle": DuplicateLifecycle.CANCELLED,
            "registered_at": value.dedup.registered_at,
            "expires_at": value.dedup.expires_at,
        }
        cancelled_dedup = dataclasses.replace(
            value.dedup, lifecycle=DuplicateLifecycle.CANCELLED,
            evidence_fingerprint=compute_dedup_evidence_fingerprint(
                **dedup_values,
            ),
        )
        dedup_key = StateKey(
            namespace=namespace, object_type="dedup",
            object_id=_key_digest(
                value.dedup.tenant_id, value.dedup.message_id,
                value.dedup.target_fingerprint,
            ),
        )
        mutations = (
            self._replace_mutation(
                records, dedup_key, 2, _dedup_dict(cancelled_dedup),
            ),
        ) + self._summary_replacements(
            namespace, records, cancelled_root, cancelled_shards,
        ) + tuple(
            self._replace_mutation(
                records,
                StateKey(
                    namespace=namespace, object_type="delivery",
                    object_id=_key_digest(delivery.delivery_id),
                ),
                delivery.state_version, _delivery_dict(delivery),
            )
            for delivery in cancelled_deliveries
        )
        result = await self._transact(scope, mutations)
        self._validate_commit(result, mutations)
        return AtomicAdmissionResult(
            outcome=AtomicAdmissionOutcome.CANCELLED_INITIALIZATION,
            root_summary=cancelled_root, dedup=cancelled_dedup,
        )

    async def _transact(
        self, scope: StateAccessScope, mutations: tuple[StateMutation, ...],
    ) -> StateTransactionResult:
        index = StateOrderedIndexKey(
            namespace=scope.namespace, name="delivery.prepared", bucket="delivery",
        )
        index_mutations: list[StateOrderedIndexMutation] = []
        changed_ids: list[str] = []
        root_summary_id: str | None = None
        for mutation in mutations:
            if mutation.key.object_type != "delivery" or mutation.document is None:
                continue
            try:
                payload = json.loads(mutation.document.payload)
                delivery_id = payload["delivery_id"]
                status = DeliveryRecordStatus(payload["status"])
                root_summary_id = payload["root_summary_id"]
                created_at = datetime.fromisoformat(payload["created_at"])
                priority = AdmissionPriority(payload["policy_decision"]["priority"])
            except (KeyError, TypeError, ValueError, json.JSONDecodeError):
                _invalid("transaction.delivery_projection")
            changed_ids.append(delivery_id)
            if status is DeliveryRecordStatus.PREPARED:
                rank = {
                    AdmissionPriority.CRITICAL: 0,
                    AdmissionPriority.HIGH: 1,
                    AdmissionPriority.NORMAL: 2,
                    AdmissionPriority.LOW: 3,
                }[priority]
                score = rank * 10_000_000_000_000.0 + created_at.timestamp()
                index_mutations.append(StateOrderedIndexMutation(
                    index=index, kind=StateOrderedIndexMutationKind.ADD,
                    member=delivery_id, score=score,
                ))
            else:
                index_mutations.append(StateOrderedIndexMutation(
                    index=index, kind=StateOrderedIndexMutationKind.REMOVE,
                    member=delivery_id,
                ))
        logs = ()
        if changed_ids and root_summary_id is not None:
            logs = (StateTransitionLogAppend(
                key=StateKey(
                    namespace=scope.namespace,
                    object_type="delivery_transition_log",
                    object_id=_key_digest(root_summary_id),
                ),
                document=StateDocument(
                    schema_name="delivery_transition_event", schema_version=1,
                    state_version=1,
                    payload=json.dumps({
                        "schema_version": "delivery-transition-event-1",
                        "operation": "admission_initialize",
                        "delivery_ids": changed_ids,
                    }, sort_keys=True, separators=(",", ":")).encode(),
                ),
            ),)
        return await self._store.transact(StateTransaction(
            scope=scope, mutations=mutations,
            ordered_index_mutations=tuple(index_mutations), log_appends=logs,
        ))

    @staticmethod
    def _record_map(result: StateTransactionResult) -> dict[StateKey, StateRecord]:
        return {
            record.key: record for record in result.records
            if isinstance(record, StateRecord)
        }

    async def _read_dedup(
        self, scope: StateAccessScope, namespace: StateNamespace,
        expected: DedupEvidence,
    ) -> DedupEvidence:
        result = await self._store.read(
            scope=scope,
            key=StateKey(
                namespace=namespace, object_type="dedup",
                object_id=_key_digest(expected.tenant_id, expected.message_id,
                                      expected.target_fingerprint),
            ),
            consistency=StateConsistency.LINEARIZABLE,
        )
        if result.record is None:
            raise NsRuntimeStateStoreUnavailableError(details={
                "component": "delivery_admission", "operation": "dedup_read",
                "reason": "conflict_without_authority_record",
            })
        try:
            raw = json.loads(result.record.document.payload)
            evidence = DedupEvidence(
                schema_version=raw["schema_version"], tenant_id=raw["tenant_id"],
                message_id=raw["message_id"],
                target_fingerprint=raw["target_fingerprint"],
                summary_id=raw["summary_id"],
                lifecycle=DuplicateLifecycle(raw["lifecycle"]),
                registered_at=datetime.fromisoformat(raw["registered_at"]),
                expires_at=datetime.fromisoformat(raw["expires_at"]),
                evidence_fingerprint=raw["evidence_fingerprint"],
            )
        except (KeyError, TypeError, ValueError, UnicodeError, json.JSONDecodeError):
            raise NsRuntimeStateStoreUnavailableError(details={
                "component": "delivery_admission", "operation": "dedup_read",
                "reason": "malformed_authority_record",
            }) from None
        if (evidence.tenant_id != expected.tenant_id
                or evidence.message_id != expected.message_id
                or evidence.target_fingerprint != expected.target_fingerprint):
            raise NsRuntimeStateStoreUnavailableError(details={
                "component": "delivery_admission", "operation": "dedup_read",
                "reason": "authority_key_mismatch",
            })
        return evidence

    @staticmethod
    def _validate_commit(
        result: object, mutations: tuple[StateMutation, ...],
    ) -> None:
        if not isinstance(result, StateTransactionResult) or len(result.records) != len(mutations):
            raise NsRuntimeStateStoreUnavailableError(details={
                "component": "delivery_admission", "operation": "initialize",
                "reason": "malformed_commit_result",
            })
        if any(record is None or record.key != mutation.key
               or record.document != mutation.document
               for record, mutation in zip(result.records, mutations)):
            raise NsRuntimeStateStoreUnavailableError(details={
                "component": "delivery_admission", "operation": "initialize",
                "reason": "commit_evidence_mismatch",
            })


def _dedup_dict(value: DedupEvidence) -> dict[str, object]:
    return {
        "schema_version": value.schema_version, "tenant_id": value.tenant_id,
        "message_id": value.message_id,
        "target_fingerprint": value.target_fingerprint,
        "summary_id": value.summary_id, "lifecycle": value.lifecycle.value,
        "registered_at": value.registered_at.isoformat(),
        "expires_at": value.expires_at.isoformat(),
        "evidence_fingerprint": value.evidence_fingerprint,
    }


def _summary_dict(value: MessageDeliverySummary) -> dict[str, object]:
    return summary_to_dict(value)


def _delivery_dict(value: DeliveryRecord) -> dict[str, object]:
    # No business payload, credential, or arbitrary exception text is stored.
    return delivery_to_dict(value)


def _key_digest(*parts: str) -> str:
    import hashlib
    return "sha256:" + hashlib.sha256("\0".join(parts).encode()).hexdigest()


def _invalid(field: str) -> None:
    raise NsValidationError(
        "DR-1 atomic store value is invalid.",
        details={"component": "delivery_admission_store", "field": field},
    )


__all__ = (
    "AdmissionInitialization", "AtomicAdmissionOutcome",
    "AtomicAdmissionResult", "DeliveryAdmissionStore",
    "StateStoreDeliveryAdmissionStore", "UnavailableDeliveryAdmissionStore",
)
