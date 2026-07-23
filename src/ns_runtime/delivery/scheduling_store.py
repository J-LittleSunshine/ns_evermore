# -*- coding: utf-8 -*-
"""P11 atomic local scheduling authority over the P08 StateStore boundary."""

from __future__ import annotations

import dataclasses
import asyncio
import hashlib
import json
from dataclasses import dataclass
from datetime import timedelta

from ns_common.exceptions import (
    NsRuntimeDeliveryLeaseExpiredError,
    NsRuntimeDeliveryStateError,
    NsRuntimeOwnerMismatchError,
    NsRuntimeStateStoreConflictError,
    NsRuntimeStateStoreUnavailableError,
    NsRuntimeStateStoreVersionMismatchError,
    NsValidationError,
)
from ns_common.state_store import (
    StateAccessScope,
    StateAssertion,
    StateAtomicScope,
    StateAuthorityKind,
    StateCallerCapability,
    StateConsistency,
    StateDocument,
    StateKey,
    StateMutation,
    StateMutationKind,
    StateNamespace,
    StateRecord,
    StateRecordReadAssertion,
    StateStore,
    StateTransaction,
    StateTransactionResult,
    StateOrderedIndexCursor, StateOrderedIndexEntry, StateOrderedIndexKey,
    StateOrderedIndexMutation, StateOrderedIndexReadAssertion,
    StateOrderedIndexMutationKind, StateOrderedIndexReadResult,
    StateTransitionLogAppend,
)
from ns_common.time import Clock

from .models import (
    P11_ACTIVATION_SCHEMA_VERSION,
    P11_ATTEMPT_SCHEMA_VERSION,
    P11_OWNER_SCHEMA_VERSION,
    MAX_ACTIVATION_BATCH_SIZE,
    DeliveryActivationEvidence,
    DeliveryAttempt,
    DeliveryAttemptStatus,
    DeliveryOwner,
    DeliveryOwnerRisk,
    DeliveryRecord,
    DeliveryRecordStatus,
    DeliveryWriteFailure,
    MessageDeliverySummary,
)
from .scheduling import (
    ActivationResult,
    ActivationSkipReason,
    ClaimOutcome,
    ClaimResult,
    DeliveryClaim,
    DeliveryResourceCounts,
    DeliverySchedulingPolicy,
    SendingTransition,
)
from .serde import (
    attempt_from_dict,
    attempt_to_dict,
    delivery_from_dict,
    delivery_to_dict,
    summary_from_dict,
    summary_to_dict,
)
from .authority_layout import (
    DeliveryAuthorityLayout,
    StateStoreDeliveryAuthorityRegistry,
    delivery_scope,
)


@dataclass(frozen=True, slots=True)
class _DeliveryAuthority:
    value: DeliveryRecord
    record: StateRecord


@dataclass(frozen=True, slots=True)
class _SummaryAuthority:
    value: MessageDeliverySummary
    record: StateRecord


@dataclass(frozen=True, slots=True)
class _SchedulerCursorAuthority:
    name: str
    index_cursor: StateOrderedIndexCursor | None
    next_bucket: int | None
    record: StateRecord | None


class StateStoreDeliveryScheduler:
    """Single-runtime scheduler; Redis records remain the only state authority."""

    def __init__(
        self, *, store: StateStore, clock: Clock,
        authority_runtime_id: str = "runtime-local",
    ) -> None:
        if not isinstance(store, StateStore):
            _invalid("store")
        if not isinstance(clock, Clock):
            _invalid("clock")
        self._store = store
        self._clock = clock
        self._registry = StateStoreDeliveryAuthorityRegistry(
            store=store, runtime_id=authority_runtime_id,
        )
        self._activation_lock = asyncio.Lock()
        self._claim_lock = asyncio.Lock()

    async def wait_for_renewal(self, *, policy: DeliverySchedulingPolicy) -> None:
        """Wait on the scheduler's injected Clock without exposing it to workers."""

        if not isinstance(policy, DeliverySchedulingPolicy):
            _invalid("wait_for_renewal.policy")
        await self._clock.sleep(policy.renew_interval_seconds)

    async def _bucket_order(
        self,
        *,
        tenant_id: str,
        policy: DeliverySchedulingPolicy,
        operation: str,
    ) -> tuple[int, ...]:
        scope = _scope(
            self._store,
            tenant_id,
            0,
            layout_generation=policy.authority_layout_generation,
        )
        cursor_name = f"{operation}.bucket_rotation"
        authority = await self._read_scheduler_cursor(scope, cursor_name)
        start = authority.next_bucket or 0
        if start >= policy.authority_bucket_count:
            raise NsRuntimeDeliveryStateError(details={
                "component": "delivery_scheduler",
                "operation": operation,
                "reason": "bucket_cursor_layout_mismatch",
            })
        await self._write_scheduler_cursor(
            scope=scope,
            name=cursor_name,
            index_cursor=None,
            next_bucket=(start + 1) % policy.authority_bucket_count,
        )
        return tuple(
            (start + offset) % policy.authority_bucket_count
            for offset in range(policy.authority_bucket_count)
        )

    async def _read_progress_page(
        self,
        *,
        scope: StateAccessScope,
        index: StateOrderedIndexKey,
        cursor_name: str,
        limit: int,
        max_score: float | None = None,
    ) -> StateOrderedIndexReadResult:
        authority = await self._read_scheduler_cursor(scope, cursor_name)
        cursor = authority.index_cursor
        try:
            page = await self._store.read_ordered_index(
                scope=scope,
                index=index,
                limit=limit,
                max_score=max_score,
                start_after=cursor,
            )
        except NsRuntimeStateStoreConflictError:
            if cursor is None:
                raise
            await self._write_scheduler_cursor(
                scope=scope,
                name=cursor_name,
                index_cursor=None,
                next_bucket=None,
            )
            page = await self._store.read_ordered_index(
                scope=scope,
                index=index,
                limit=limit,
                max_score=max_score,
            )
        await self._write_scheduler_cursor(
            scope=scope,
            name=cursor_name,
            index_cursor=page.next_cursor,
            next_bucket=None,
        )
        return page

    async def _reanchor_progress_cursor(
        self,
        *,
        scope: StateAccessScope,
        cursor_name: str,
        page: StateOrderedIndexReadResult,
        removed_members: frozenset[str],
    ) -> None:
        cursor = None
        if page.next_cursor is not None:
            for entry in reversed(page.entries):
                if entry.member not in removed_members:
                    cursor = StateOrderedIndexCursor(
                        member=entry.member,
                        score=entry.score,
                    )
                    break
        await self._write_scheduler_cursor(
            scope=scope,
            name=cursor_name,
            index_cursor=cursor,
            next_bucket=None,
        )

    async def _read_scheduler_cursor(
        self,
        scope: StateAccessScope,
        name: str,
    ) -> _SchedulerCursorAuthority:
        key = _scheduler_cursor_key(scope, name)
        result = await self._store.read(
            scope=scope,
            key=key,
            consistency=StateConsistency.LINEARIZABLE,
        )
        record = result.record
        if record is None:
            legacy = await self._store.read(
                scope=scope,
                key=_legacy_scheduler_cursor_key(scope, name),
                consistency=StateConsistency.LINEARIZABLE,
            )
            if legacy.record is not None:
                raise NsRuntimeStateStoreVersionMismatchError(details={
                    "component": "delivery_scheduler",
                    "operation": "read_scheduler_cursor",
                    "reason": "scheduler_cursor_migration_reset_required",
                    "cursor_name": name,
                })
            return _SchedulerCursorAuthority(
                name=name,
                index_cursor=None,
                next_bucket=None,
                record=None,
            )
        try:
            values = json.loads(record.document.payload)
            if (
                type(values) is not dict
                or set(values) != {
                    "schema_version", "name", "member", "score",
                    "next_bucket", "state_version", "updated_at",
                    "layout_generation", "bucket_id", "operation",
                    "index_identity",
                }
                or values["schema_version"] != "delivery-scheduler-cursor-2"
                or values["name"] != name
                or values["state_version"] != record.document.state_version
            ):
                raise ValueError
            layout_generation, bucket_id, operation, index_identity = (
                _scheduler_cursor_identity(scope, name)
            )
            if (
                values["layout_generation"] != layout_generation
                or values["bucket_id"] != bucket_id
                or values["operation"] != operation
                or values["index_identity"] != index_identity
            ):
                raise ValueError
            member = values["member"]
            score = values["score"]
            if (member is None) is not (score is None):
                raise ValueError
            index_cursor = (
                None
                if member is None
                else StateOrderedIndexCursor(member=member, score=score)
            )
            next_bucket = values["next_bucket"]
            if (
                next_bucket is not None
                and (
                    isinstance(next_bucket, bool)
                    or not isinstance(next_bucket, int)
                    or next_bucket < 0
                )
            ):
                raise ValueError
        except (
            KeyError,
            TypeError,
            ValueError,
            UnicodeError,
            json.JSONDecodeError,
            NsValidationError,
        ):
            _unavailable("read_scheduler_cursor", "malformed_cursor_authority")
        return _SchedulerCursorAuthority(
            name=name,
            index_cursor=index_cursor,
            next_bucket=next_bucket,
            record=record,
        )

    async def _write_scheduler_cursor(
        self,
        *,
        scope: StateAccessScope,
        name: str,
        index_cursor: StateOrderedIndexCursor | None,
        next_bucket: int | None,
    ) -> None:
        for _ in range(3):
            authority = await self._read_scheduler_cursor(scope, name)
            state_version = (
                1
                if authority.record is None
                else authority.record.document.state_version + 1
            )
            document = StateDocument(
                schema_name="delivery_scheduler_cursor",
                schema_version=2,
                state_version=state_version,
                payload=_json({
                    "schema_version": "delivery-scheduler-cursor-2",
                    "name": name,
                    "layout_generation": _scheduler_cursor_identity(
                        scope, name,
                    )[0],
                    "bucket_id": _scheduler_cursor_identity(scope, name)[1],
                    "operation": _scheduler_cursor_identity(scope, name)[2],
                    "index_identity": _scheduler_cursor_identity(
                        scope, name,
                    )[3],
                    "member": (
                        None if index_cursor is None else index_cursor.member
                    ),
                    "score": (
                        None if index_cursor is None else index_cursor.score
                    ),
                    "next_bucket": next_bucket,
                    "state_version": state_version,
                    "updated_at": self._clock.utc_now().isoformat(),
                }),
            )
            mutation = StateMutation(
                key=_scheduler_cursor_key(scope, name),
                assertion=(
                    StateAssertion.absent()
                    if authority.record is None
                    else StateAssertion.matches(
                        authority.record.revision,
                        state_version=authority.record.document.state_version,
                    )
                ),
                kind=(
                    StateMutationKind.CREATE
                    if authority.record is None
                    else StateMutationKind.REPLACE
                ),
                document=document,
            )
            try:
                await self._store.transact(StateTransaction(
                    scope=scope,
                    mutations=(mutation,),
                ))
                return
            except NsRuntimeStateStoreConflictError:
                continue
        raise NsRuntimeStateStoreConflictError(details={
            "component": "delivery_scheduler",
            "operation": "write_scheduler_cursor",
            "reason": "cursor_update_contended",
        })

    async def _repair_ordered_projection(
        self,
        *,
        scope: StateAccessScope,
        index: StateOrderedIndexKey,
        entry: StateOrderedIndexEntry,
        reason: str,
        observed_record: StateRecord | None = None,
        observe_missing_or_malformed: bool = False,
        replacement_score: float | None = None,
        quarantine: bool = False,
    ) -> bool:
        record_key = StateKey(
            namespace=scope.namespace,
            object_type="delivery",
            object_id=_key_digest(entry.member),
        )
        if observe_missing_or_malformed:
            observed = await self._store.read(
                scope=scope,
                key=record_key,
                consistency=StateConsistency.LINEARIZABLE,
            )
            observed_record = observed.record
            if observed_record is not None:
                try:
                    current = _decode_delivery(observed_record)
                except NsRuntimeStateStoreUnavailableError:
                    pass
                else:
                    if current.delivery_id == entry.member:
                        return False
        record_assertion = (
            StateRecordReadAssertion.absent(record_key)
            if observed_record is None
            else StateRecordReadAssertion.present(
                record_key,
                revision=observed_record.revision,
                state_version=observed_record.document.state_version,
            )
        )
        if replacement_score is None:
            index_mutations = [
                _index_remove(index, entry.member),
            ]
        else:
            index_mutations = [
                _index_add(index, entry.member, replacement_score),
            ]
        if quarantine:
            index_mutations.append(_index_add(
                _index(scope, "delivery.scheduler_quarantine"),
                entry.member,
                self._clock.utc_now().timestamp(),
            ))
        event = {
            "schema_version": "delivery-index-repair-event-1",
            "operation": "ordered_index_projection_repaired",
            "index": index.name,
            "member_digest": (
                "sha256:" + hashlib.sha256(entry.member.encode()).hexdigest()
            ),
            "reason": reason,
            "replacement": replacement_score is not None,
            "quarantined": quarantine,
            "occurred_at": self._clock.utc_now().isoformat(),
        }
        try:
            await self._store.transact(StateTransaction(
                scope=scope,
                mutations=(),
                record_assertions=(record_assertion,),
                ordered_index_assertions=(
                    StateOrderedIndexReadAssertion.present(
                        index,
                        entry.member,
                        score=entry.score,
                    ),
                ),
                ordered_index_mutations=tuple(index_mutations),
                log_appends=(StateTransitionLogAppend(
                    key=StateKey(
                        namespace=scope.namespace,
                        object_type="delivery_scheduler_repair_log",
                        object_id=_key_digest(index.name),
                    ),
                    document=StateDocument(
                        schema_name="delivery_index_repair_event",
                        schema_version=1,
                        state_version=1,
                        payload=_json(event),
                    ),
                ),),
            ))
        except NsRuntimeStateStoreConflictError:
            await self._store.read(
                scope=scope,
                key=record_key,
                consistency=StateConsistency.LINEARIZABLE,
            )
            return False
        return True

    async def activate_prepared(
        self,
        *,
        tenant_id: str,
        policy: DeliverySchedulingPolicy,
        global_queued_before: int | None = None,
    ) -> ActivationResult:
        _text(tenant_id, "activate.tenant_id")
        if not isinstance(policy, DeliverySchedulingPolicy):
            _invalid("activate.policy")
        async with self._activation_lock:
            return await self._activate_prepared_locked(
                tenant_id=tenant_id,
                policy=policy,
                global_queued_before=global_queued_before,
            )

    async def _activate_prepared_locked(
        self,
        *,
        tenant_id: str,
        policy: DeliverySchedulingPolicy,
        global_queued_before: int | None,
    ) -> ActivationResult:
        layout = _layout(policy)
        await self._registry.ensure_registered(tenant_id=tenant_id, layout=layout)
        scope = _scope(
            self._store,
            tenant_id, 0, layout_generation=policy.authority_layout_generation,
        )
        now = self._clock.utc_now()
        bucket_order = await self._bucket_order(
            tenant_id=tenant_id,
            policy=policy,
            operation="activation",
        )
        scope, candidate_page = await self._select_activation_page(
            tenant_id=tenant_id,
            bucket_order=bucket_order,
            policy=policy,
            now=now,
        )
        prepared_index = _index(scope, "delivery.prepared")
        counts = await self.resource_counts(
            tenant_id=tenant_id,
            authority_bucket_count=policy.authority_bucket_count,
            authority_layout_generation=policy.authority_layout_generation,
        )
        queued_before = counts.queued
        authoritative_global = await self.runtime_queued_count(policy=policy)
        if global_queued_before is None:
            global_queued_before = authoritative_global
        if (
            isinstance(global_queued_before, bool)
            or not isinstance(global_queued_before, int)
            or global_queued_before != authoritative_global
        ):
            _invalid("activate.global_queued_before")
        target_queued: dict[str, int] = {}
        selected: list[_DeliveryAuthority] = []
        expired: list[_DeliveryAuthority] = []
        reasons: list[ActivationSkipReason] = []
        selected_scores: dict[str, float] = {}
        expired_scores: dict[str, float] = {}
        selected_policy_snapshot: tuple[str, str] | None = None
        selected_batch_limit = policy.activation_batch_size
        repaired_members: set[str] = set()
        for entry in candidate_page.entries:
            try:
                item = await self._read_delivery(scope, entry.member)
            except NsRuntimeStateStoreUnavailableError as error:
                if not _repairable_authority_error(error):
                    raise
                repaired = await self._repair_ordered_projection(
                    scope=scope,
                    index=prepared_index,
                    entry=entry,
                    reason="record_missing_or_malformed",
                    observe_missing_or_malformed=True,
                    quarantine=True,
                )
                if repaired:
                    repaired_members.add(entry.member)
                continue
            value = item.value
            bucket_id = _bucket_id(scope)
            if (
                value.authority_bucket_count != policy.authority_bucket_count
                or value.authority_bucket_id != bucket_id
                or value.authority_layout_version != policy.authority_layout_version
                or value.authority_layout_generation != policy.authority_layout_generation
            ):
                raise NsRuntimeDeliveryStateError(details={
                    "component": "delivery_scheduler",
                    "operation": "activate_prepared",
                    "reason": "authority_bucket_mismatch",
                })
            if value.status is not DeliveryRecordStatus.PREPARED:
                repaired = await self._repair_ordered_projection(
                    scope=scope,
                    index=prepared_index,
                    entry=entry,
                    reason="status_not_prepared",
                    observed_record=item.record,
                )
                if repaired:
                    repaired_members.add(entry.member)
                continue
            if value.policy_decision.expires_at <= now:
                _reason(reasons, ActivationSkipReason.EXPIRED)
                expired.append(item)
                expired_scores[value.delivery_id] = entry.score
                continue
            policy_snapshot = (
                value.policy_decision.config_version,
                value.policy_decision.policy_version,
            )
            if selected_policy_snapshot is not None and policy_snapshot != selected_policy_snapshot:
                _reason(reasons, ActivationSkipReason.BATCH_LIMIT)
                break
            candidate_batch_limit = min(
                policy.activation_batch_size,
                value.policy_decision.activation_batch_size,
            )
            if len(selected) >= candidate_batch_limit:
                _reason(reasons, ActivationSkipReason.BATCH_LIMIT)
                break
            if queued_before + len(selected) >= policy.tenant_queued_high_watermark:
                _reason(reasons, ActivationSkipReason.TENANT_WATERMARK)
                break
            if (
                global_queued_before + len(selected)
                >= policy.global_queued_high_watermark
            ):
                _reason(reasons, ActivationSkipReason.GLOBAL_WATERMARK)
                break
            if value.target_fingerprint not in target_queued:
                target_queued[value.target_fingerprint] = await self._target_queued_count(
                    tenant_id=tenant_id,
                    target_fingerprint=value.target_fingerprint,
                    policy=policy,
                )
            target_count = target_queued[value.target_fingerprint]
            if target_count >= policy.target_queued_high_watermark:
                _reason(reasons, ActivationSkipReason.TARGET_WATERMARK)
                continue
            selected.append(item)
            if selected_policy_snapshot is None:
                selected_policy_snapshot = policy_snapshot
                selected_batch_limit = candidate_batch_limit
            selected_scores[value.delivery_id] = entry.score
            target_queued[value.target_fingerprint] = target_count + 1
        if candidate_page.total_count == 0:
            _reason(reasons, ActivationSkipReason.NO_PREPARED)
        if not selected and not expired:
            if repaired_members:
                await self._reanchor_progress_cursor(
                    scope=scope,
                    cursor_name="activation.prepared",
                    page=candidate_page,
                    removed_members=frozenset(repaired_members),
                )
            return ActivationResult(
                tenant_id=tenant_id,
                candidate_count=candidate_page.total_count,
                activated=(),
                queued_before=queued_before,
                queued_after=queued_before,
                global_queued_before=global_queued_before,
                global_queued_after=global_queued_before,
                skip_reasons=tuple(reasons),
                policy_version=policy.policy_version,
            )

        evidence = None
        if selected:
            decision = selected[0].value.policy_decision
            evidence = DeliveryActivationEvidence(
                schema_version=P11_ACTIVATION_SCHEMA_VERSION,
                config_version=decision.config_version,
                policy_version=decision.policy_version,
                reason="prepared_ready",
                batch_size=selected_batch_limit,
                candidate_count=candidate_page.total_count,
                activated_at=now,
            )
        activated = tuple(
            dataclasses.replace(
                item.value,
                status=DeliveryRecordStatus.QUEUED,
                activation=evidence,
                state_version=item.value.state_version + 1,
                updated_at=now,
            )
            for item in selected
        )
        expired_values = tuple(
            dataclasses.replace(
                item.value,
                status=DeliveryRecordStatus.EXPIRED,
                activation=DeliveryActivationEvidence(
                    schema_version=P11_ACTIVATION_SCHEMA_VERSION,
                    config_version=item.value.policy_decision.config_version,
                    policy_version=item.value.policy_decision.policy_version,
                    reason="expired_before_queue",
                    batch_size=item.value.policy_decision.activation_batch_size,
                    candidate_count=candidate_page.total_count,
                    activated_at=now,
                ),
                last_failure=DeliveryWriteFailure.DELIVERY_EXPIRED,
                state_version=item.value.state_version + 1,
                updated_at=now,
            )
            for item in expired
        )
        per_summary: dict[str, list[int]] = {}
        for value in activated:
            for summary_id in {value.summary_id, value.root_summary_id}:
                delta = per_summary.setdefault(summary_id, [0, 0])
                delta[0] += 1
        for value in expired_values:
            for summary_id in {value.summary_id, value.root_summary_id}:
                delta = per_summary.setdefault(summary_id, [0, 0])
                delta[1] += 1
        changed_summaries: list[tuple[_SummaryAuthority, MessageDeliverySummary]] = []
        for summary_id, (queued_count, expired_count) in per_summary.items():
            authority = await self._read_summary(scope, summary_id)
            changed_summaries.append((
                authority,
                _summary_delta(
                    authority.value,
                    prepared=-(queued_count + expired_count),
                    queued=queued_count,
                    expired=expired_count,
                    now=now,
                ),
            ))
        mutations = tuple(
            _replace_delivery(item.record, value)
            for item, value in zip(selected, activated)
        ) + tuple(
            _replace_delivery(item.record, value)
            for item, value in zip(expired, expired_values)
        ) + tuple(
            _replace_summary(authority.record, value)
            for authority, value in changed_summaries
        )
        index_mutations: list[StateOrderedIndexMutation] = []
        for value in activated:
            index_mutations.extend((
                _index_remove(prepared_index, value.delivery_id),
                _index_add(_index(scope, "delivery.ready"), value.delivery_id,
                           selected_scores[value.delivery_id]),
                _index_add(_target_index(scope, value.target_fingerprint),
                           value.delivery_id, selected_scores[value.delivery_id]),
                _index_add(
                    _runtime_ready_index(scope),
                    value.delivery_id,
                    selected_scores[value.delivery_id],
                ),
            ))
        for value in expired_values:
            index_mutations.extend((
                _index_remove(prepared_index, value.delivery_id),
                _index_add(_index(scope, "delivery.expired"), value.delivery_id,
                           expired_scores[value.delivery_id]),
            ))
        evidence_delivery = activated[0] if activated else expired_values[0]
        result = await self._store.transact(_transition(
            scope=scope, mutations=mutations,
            index_mutations=tuple(index_mutations),
            operation="prepared_activated", delivery=evidence_delivery, now=now,
        ))
        _validate_transaction(result, mutations, "activate")
        await self._reanchor_progress_cursor(
            scope=scope,
            cursor_name="activation.prepared",
            page=candidate_page,
            removed_members=frozenset(
                repaired_members
                | {value.delivery_id for value in activated}
                | {value.delivery_id for value in expired_values}
            ),
        )
        return ActivationResult(
            tenant_id=tenant_id,
            candidate_count=candidate_page.total_count,
            activated=activated,
            queued_before=queued_before,
            queued_after=queued_before + len(activated),
            global_queued_before=global_queued_before,
            global_queued_after=global_queued_before + len(activated),
            skip_reasons=tuple(reasons),
            policy_version=(
                activated[0].policy_decision.policy_version
                if activated else expired_values[0].policy_decision.policy_version
            ),
        )

    async def _inspect_activation_page(
        self, *, scope: StateAccessScope, page: StateOrderedIndexReadResult,
        policy: DeliverySchedulingPolicy, now,
    ) -> tuple[bool, StateOrderedIndexReadResult]:
        """Repair stale prepared projection and identify a live candidate."""

        valid_entries = []
        removed_members: set[str] = set()
        eligible = False
        for entry in page.entries:
            try:
                authority = await self._read_delivery(scope, entry.member)
            except NsRuntimeStateStoreUnavailableError as error:
                if not _repairable_authority_error(error):
                    raise
                repaired = await self._repair_ordered_projection(
                    scope=scope,
                    index=_index(scope, "delivery.prepared"),
                    entry=entry,
                    reason="record_missing_or_malformed",
                    observe_missing_or_malformed=True,
                    quarantine=True,
                )
                if repaired:
                    removed_members.add(entry.member)
                continue
            value = authority.value
            if value.status is not DeliveryRecordStatus.PREPARED:
                repaired = await self._repair_ordered_projection(
                    scope=scope,
                    index=_index(scope, "delivery.prepared"),
                    entry=entry,
                    reason="status_not_prepared",
                    observed_record=authority.record,
                )
                if repaired:
                    removed_members.add(entry.member)
                continue
            if (
                value.authority_bucket_count != policy.authority_bucket_count
                or value.authority_bucket_id != _bucket_id(scope)
                or value.authority_layout_version != policy.authority_layout_version
                or value.authority_layout_generation != policy.authority_layout_generation
            ):
                raise NsRuntimeDeliveryStateError(details={
                    "component": "delivery_scheduler",
                    "operation": "activation_probe",
                    "reason": "authority_layout_mismatch",
                })
            if value.policy_decision.expires_at <= now:
                eligible = True
                valid_entries.append(entry)
                continue
            target_count = await self._target_queued_count(
                tenant_id=value.tenant_id,
                target_fingerprint=value.target_fingerprint,
                policy=policy,
            )
            if target_count < policy.target_queued_high_watermark:
                eligible = True
            valid_entries.append(entry)
        if removed_members:
            await self._reanchor_progress_cursor(
                scope=scope,
                cursor_name="activation.prepared",
                page=page,
                removed_members=frozenset(removed_members),
            )
        filtered_cursor = None
        if page.next_cursor is not None and valid_entries:
            last = valid_entries[-1]
            filtered_cursor = StateOrderedIndexCursor(
                member=last.member,
                score=last.score,
            )
        return eligible, StateOrderedIndexReadResult(
            entries=tuple(valid_entries),
            observed_at=page.observed_at,
            total_count=page.total_count,
            next_cursor=filtered_cursor,
        )

    async def _target_queued_count(
        self, *, tenant_id: str, target_fingerprint: str,
        policy: DeliverySchedulingPolicy,
    ) -> int:
        results = await asyncio.gather(*(
            self._store.read_ordered_index(
                scope=(scope := _scope(
                    self._store,
                    tenant_id,
                    bucket_id,
                    layout_generation=policy.authority_layout_generation,
                )),
                index=_target_index(scope, target_fingerprint),
                limit=1,
            )
            for bucket_id in range(policy.authority_bucket_count)
        ))
        return sum(result.total_count for result in results)

    async def _select_activation_page(
        self, *, tenant_id: str, bucket_order: tuple[int, ...],
        policy: DeliverySchedulingPolicy, now,
    ) -> tuple[StateAccessScope, StateOrderedIndexReadResult]:
        """Use durable per-bucket cursors inside one global candidate budget."""

        remaining = policy.activation_scan_budget
        active_buckets = list(bucket_order)
        fallback: tuple[StateAccessScope, StateOrderedIndexReadResult] | None = None
        while remaining > 0 and active_buckets:
            progressed = False
            for bucket_id in tuple(active_buckets):
                if remaining <= 0:
                    break
                scope = _scope(
                    self._store,
                    tenant_id,
                    bucket_id,
                    layout_generation=policy.authority_layout_generation,
                )
                page = await self._read_progress_page(
                    scope=scope,
                    index=_index(scope, "delivery.prepared"),
                    cursor_name="activation.prepared",
                    limit=min(64, remaining),
                )
                reached_end = page.next_cursor is None
                if page.entries:
                    progressed = True
                    remaining -= len(page.entries)
                eligible, filtered = await self._inspect_activation_page(
                    scope=scope,
                    page=page,
                    policy=policy,
                    now=now,
                )
                if filtered.entries and fallback is None:
                    fallback = (scope, filtered)
                if eligible:
                    return scope, filtered
                if reached_end or not page.entries:
                    active_buckets.remove(bucket_id)
            if not progressed:
                break
        if fallback is not None:
            return fallback
        scope = _scope(
            self._store,
            tenant_id,
            bucket_order[0],
            layout_generation=policy.authority_layout_generation,
        )
        return scope, StateOrderedIndexReadResult(
            entries=(),
            observed_at=now,
            total_count=0,
        )

    async def resource_counts(
        self, *, tenant_id: str, authority_bucket_count: int = 8,
        authority_layout_generation: int = 2,
    ) -> DeliveryResourceCounts:
        """Rebuild P11 resource counts from authoritative delivery records."""

        _text(tenant_id, "resource_counts.tenant_id")
        names = (
            "delivery.prepared", "delivery.ready", "delivery.claimed",
            "delivery.sending", "delivery.ack", "delivery.write_failed",
            "delivery.waiting", "delivery.expired",
            "delivery.payload_rejected", "delivery.write_uncertain",
        )
        requests = []
        for bucket_id in range(authority_bucket_count):
            scope = _scope(
                self._store,
                tenant_id, bucket_id,
                layout_generation=authority_layout_generation,
            )
            for name in names:
                requests.append(self._store.read_ordered_index(
                    scope=scope, index=_index(scope, name), limit=1,
                ))
        results = await asyncio.gather(*requests)
        totals = {name: 0 for name in names}
        for offset, result in enumerate(results):
            totals[names[offset % len(names)]] += result.total_count
        counts = DeliveryResourceCounts(
            tenant_id=tenant_id,
            prepared=totals["delivery.prepared"],
            queued=totals["delivery.ready"] + totals["delivery.claimed"],
            sending=totals["delivery.sending"],
            ack_waiting=totals["delivery.ack"],
            write_failed=totals["delivery.write_failed"],
            waiting=totals["delivery.waiting"],
            expired=totals["delivery.expired"],
            payload_rejected=totals["delivery.payload_rejected"],
            write_uncertain=totals["delivery.write_uncertain"],
        )
        return counts

    async def runtime_queued_count(self, *, policy: DeliverySchedulingPolicy) -> int:
        """Bounded runtime-global queued count rebuilt from registered authority."""

        if not isinstance(policy, DeliverySchedulingPolicy):
            _invalid("runtime_queued.policy")
        tenants = await self._registry.registered_tenants(layout=_layout(policy))
        counts = await asyncio.gather(*(
            self.resource_counts(
                tenant_id=tenant_id,
                authority_bucket_count=policy.authority_bucket_count,
                authority_layout_generation=policy.authority_layout_generation,
            )
            for tenant_id in tenants
        ))
        return sum(value.queued for value in counts)

    async def claim_next(
        self,
        *,
        tenant_id: str,
        runtime_id: str,
        worker_id: str,
        claim_token: str,
        policy: DeliverySchedulingPolicy,
    ) -> ClaimResult:
        for value, field in (
            (tenant_id, "tenant_id"), (runtime_id, "runtime_id"),
            (worker_id, "worker_id"), (claim_token, "claim_token"),
        ):
            _text(value, f"claim.{field}")
        if not isinstance(policy, DeliverySchedulingPolicy):
            _invalid("claim.policy")
        async with self._claim_lock:
            return await self._claim_next_locked(
                tenant_id=tenant_id,
                runtime_id=runtime_id,
                worker_id=worker_id,
                claim_token=claim_token,
                policy=policy,
            )

    async def _claim_next_locked(
        self,
        *,
        tenant_id: str,
        runtime_id: str,
        worker_id: str,
        claim_token: str,
        policy: DeliverySchedulingPolicy,
    ) -> ClaimResult:
        await self._registry.ensure_registered(tenant_id=tenant_id, layout=_layout(policy))
        now = self._clock.utc_now()
        bucket_order = await self._bucket_order(
            tenant_id=tenant_id,
            policy=policy,
            operation="claim",
        )
        remaining = policy.activation_scan_budget
        contended = False
        for bucket_id in bucket_order:
            if remaining <= 0:
                break
            scope = _scope(
                self._store,
                tenant_id, bucket_id,
                layout_generation=policy.authority_layout_generation,
            )
            recovered, consumed = await self._recover_expired_for_claim(
                scope=scope, runtime_id=runtime_id, worker_id=worker_id,
                claim_token=claim_token, policy=policy, now=now,
                budget=remaining,
            )
            remaining -= consumed
            if recovered is not None:
                return recovered
            while remaining > 0:
                ready = await self._read_progress_page(
                    scope=scope,
                    index=_index(scope, "delivery.ready"),
                    cursor_name="claim.ready",
                    limit=min(16, remaining),
                )
                if not ready.entries:
                    break
                remaining -= len(ready.entries)
                result, was_contended = await self._claim_ready_in_scope(
                    scope=scope, ready=ready, tenant_id=tenant_id,
                    runtime_id=runtime_id, worker_id=worker_id,
                    claim_token=claim_token, policy=policy, now=now,
                )
                contended = contended or was_contended
                if result is not None:
                    return result
                if ready.next_cursor is None:
                    break
        return ClaimResult(
            outcome=(ClaimOutcome.CONTENDED if contended else ClaimOutcome.EMPTY),
            claim=None, delivery=None,
        )

    async def _claim_ready_in_scope(
        self, *, scope: StateAccessScope, ready: StateOrderedIndexReadResult,
        tenant_id: str, runtime_id: str, worker_id: str, claim_token: str,
        policy: DeliverySchedulingPolicy, now,
    ) -> tuple[ClaimResult | None, bool]:
        contended = False
        for entry in ready.entries:
            try:
                authority = await self._read_delivery(scope, entry.member)
            except NsRuntimeStateStoreUnavailableError as error:
                if not _repairable_authority_error(error):
                    raise
                await self._repair_ordered_projection(
                    scope=scope,
                    index=_index(scope, "delivery.ready"),
                    entry=entry,
                    reason="record_missing_or_malformed",
                    observe_missing_or_malformed=True,
                    quarantine=True,
                )
                continue
            bucket_id = _bucket_id(scope)
            if (
                authority.value.authority_bucket_count
                != policy.authority_bucket_count
                or authority.value.authority_bucket_id != bucket_id
                or authority.value.authority_layout_version != policy.authority_layout_version
                or authority.value.authority_layout_generation != policy.authority_layout_generation
            ):
                await self._repair_ordered_projection(
                    scope=scope,
                    index=_index(scope, "delivery.ready"),
                    entry=entry,
                    reason="authority_layout_mismatch",
                    observed_record=authority.record,
                    quarantine=True,
                )
                continue
            if authority.value.status is not DeliveryRecordStatus.QUEUED or authority.value.owner is not None:
                await self._repair_ordered_projection(
                    scope=scope,
                    index=_index(scope, "delivery.ready"),
                    entry=entry,
                    reason=(
                        "status_not_queued"
                        if authority.value.status is not DeliveryRecordStatus.QUEUED
                        else "queued_owner_present"
                    ),
                    observed_record=authority.record,
                )
                continue
            fencing = authority.value.last_fencing + 1
            owner_epoch = authority.value.owner_epoch + 1
            owner = DeliveryOwner(
                schema_version=P11_OWNER_SCHEMA_VERSION,
                runtime_id=runtime_id, worker_id=worker_id,
                claim_token=claim_token, claimed_at=now,
                lease_expires_at=now + timedelta(seconds=policy.lease_ttl_seconds),
                renew_failures=0, risk=DeliveryOwnerRisk.HEALTHY,
                fencing=fencing, owner_epoch=owner_epoch,
            )
            claimed = dataclasses.replace(
                authority.value, owner=owner, last_fencing=fencing,
                owner_epoch=owner_epoch,
                state_version=authority.value.state_version + 1, updated_at=now,
            )
            indexes = (
                _index_remove(_index(scope, "delivery.ready"), claimed.delivery_id),
                _index_add(_index(scope, "delivery.claimed"), claimed.delivery_id, entry.score),
                _index_add(_index(scope, "delivery.lease"), claimed.delivery_id,
                           owner.lease_expires_at.timestamp()),
            )
            try:
                result = await self._store.transact(_transition(
                    scope=scope, mutations=(_replace_delivery(authority.record, claimed),),
                    index_mutations=indexes, operation="delivery_claimed",
                    delivery=claimed, now=now,
                ))
            except NsRuntimeStateStoreConflictError:
                contended = True
                continue
            _validate_transaction(result, (_replace_delivery(authority.record, claimed),), "claim")
            claim = DeliveryClaim(
                tenant_id=tenant_id, delivery_id=claimed.delivery_id,
                runtime_id=runtime_id, worker_id=worker_id,
                claim_token=claim_token, fencing=fencing,
                owner_epoch=owner_epoch,
                authority_bucket_count=claimed.authority_bucket_count,
                authority_bucket_id=claimed.authority_bucket_id,
                authority_layout_version=claimed.authority_layout_version,
                authority_layout_generation=claimed.authority_layout_generation,
            )
            return ClaimResult(outcome=ClaimOutcome.CLAIMED, claim=claim, delivery=claimed), contended
        return None, contended

    async def renew_owner(
        self,
        *,
        claim: DeliveryClaim,
        policy: DeliverySchedulingPolicy,
    ) -> DeliveryRecord:
        if not isinstance(claim, DeliveryClaim):
            _invalid("renew.claim")
        if not isinstance(policy, DeliverySchedulingPolicy):
            _invalid("renew.policy")
        scope = _claim_scope(self._store, claim)
        authority = await self._read_delivery(scope, claim.delivery_id)
        owner = _require_owner(authority.value, claim, self._clock.utc_now(), allow_risk=True)
        now = self._clock.utc_now()
        next_owner = dataclasses.replace(
            owner, lease_expires_at=now + timedelta(seconds=policy.lease_ttl_seconds),
            renew_failures=0, risk=DeliveryOwnerRisk.HEALTHY,
            risk_since=None, protection_until=None,
        )
        updated = dataclasses.replace(
            authority.value,
            owner=next_owner,
            state_version=authority.value.state_version + 1,
            updated_at=now,
        )
        mutation = _replace_delivery(authority.record, updated)
        result = await self._store.transact(_transition(
            scope=scope, mutations=(mutation,),
            index_mutations=(_index_add(
                _index(scope, "delivery.lease"), updated.delivery_id,
                next_owner.lease_expires_at.timestamp(),
            ),), operation="owner_renewed", delivery=updated, now=now,
        ))
        _validate_transaction(result, (mutation,), "renew")
        return updated

    async def mark_owner_at_risk(
        self,
        *,
        claim: DeliveryClaim,
        policy: DeliverySchedulingPolicy,
    ) -> DeliveryRecord:
        """Persist a renewal failure when authority is reachable again."""

        if not isinstance(claim, DeliveryClaim):
            _invalid("owner_risk.claim")
        if not isinstance(policy, DeliverySchedulingPolicy):
            _invalid("owner_risk.policy")
        scope = _claim_scope(self._store, claim)
        authority = await self._read_delivery(scope, claim.delivery_id)
        now = self._clock.utc_now()
        owner = _require_owner(authority.value, claim, now, allow_risk=True)
        risk_since = owner.risk_since or now
        risky_owner = dataclasses.replace(
            owner,
            renew_failures=owner.renew_failures + 1,
            risk=DeliveryOwnerRisk.AT_RISK,
            risk_since=risk_since,
            protection_until=max(
                owner.protection_until or risk_since,
                now + timedelta(seconds=policy.owner_risk_window_seconds),
            ),
        )
        updated = dataclasses.replace(
            authority.value,
            owner=risky_owner,
            state_version=authority.value.state_version + 1,
            updated_at=now,
        )
        mutation = _replace_delivery(authority.record, updated)
        result = await self._store.transact(_transition(
            scope=scope,
            mutations=(mutation,),
            index_mutations=(),
            operation="owner_at_risk",
            delivery=updated,
            now=now,
        ))
        _validate_transaction(result, (mutation,), "mark_owner_at_risk")
        return updated

    async def release_claim(self, *, claim: DeliveryClaim) -> DeliveryRecord:
        if not isinstance(claim, DeliveryClaim):
            _invalid("release.claim")
        scope = _claim_scope(self._store, claim)
        authority = await self._read_delivery(scope, claim.delivery_id)
        _require_owner(authority.value, claim, self._clock.utc_now(), allow_risk=True)
        if authority.value.status is not DeliveryRecordStatus.QUEUED:
            raise NsRuntimeDeliveryStateError(details={
                "component": "delivery_scheduler", "operation": "release_claim",
                "reason": "queued_required",
            })
        updated = dataclasses.replace(
            authority.value,
            owner=None,
            state_version=authority.value.state_version + 1,
            updated_at=self._clock.utc_now(),
        )
        mutation = _replace_delivery(authority.record, updated)
        result = await self._store.transact(_transition(
            scope=scope, mutations=(mutation,), index_mutations=(
                _index_remove(_index(scope, "delivery.claimed"), updated.delivery_id),
                _index_remove(_index(scope, "delivery.lease"), updated.delivery_id),
                _index_add(_index(scope, "delivery.ready"), updated.delivery_id,
                           updated.activation.activated_at.timestamp()),
            ), operation="claim_released", delivery=updated,
            now=self._clock.utc_now(),
        ))
        _validate_transaction(result, (mutation,), "release_claim")
        return updated

    async def fail_precheck(
        self, *, claim: DeliveryClaim, failure: DeliveryWriteFailure,
    ) -> DeliveryRecord:
        if not isinstance(claim, DeliveryClaim) or not isinstance(failure, DeliveryWriteFailure):
            _invalid("precheck")
        scope = _claim_scope(self._store, claim)
        authority = await self._read_delivery(scope, claim.delivery_id)
        now = self._clock.utc_now()
        _require_owner(authority.value, claim, now, allow_risk=True)
        if authority.value.status is not DeliveryRecordStatus.QUEUED:
            raise NsRuntimeDeliveryStateError(details={
                "component": "delivery_scheduler", "operation": "fail_precheck",
                "reason": "queued_required",
            })
        status = {
            DeliveryWriteFailure.DELIVERY_EXPIRED: DeliveryRecordStatus.EXPIRED,
            DeliveryWriteFailure.PAYLOAD_INVALID: DeliveryRecordStatus.PAYLOAD_REJECTED,
            DeliveryWriteFailure.TARGET_DISCONNECTED: DeliveryRecordStatus.TARGET_WAITING,
            DeliveryWriteFailure.TARGET_IDENTITY_MISMATCH: DeliveryRecordStatus.PAYLOAD_REJECTED,
            DeliveryWriteFailure.OWNER_AT_RISK: DeliveryRecordStatus.TARGET_WAITING,
        }.get(failure, DeliveryRecordStatus.PAYLOAD_REJECTED)
        updated = dataclasses.replace(
            authority.value, status=status, owner=None, last_failure=failure,
            state_version=authority.value.state_version + 1, updated_at=now,
        )
        summary_delta = {
            DeliveryRecordStatus.TARGET_WAITING: {"waiting": 1},
            DeliveryRecordStatus.EXPIRED: {"expired": 1},
            DeliveryRecordStatus.PAYLOAD_REJECTED: {"payload_rejected": 1},
        }[status]
        summary_mutations = await self._summary_mutations(
            scope, authority.value, queued=-1, now=now, **summary_delta,
        )
        mutations = (_replace_delivery(authority.record, updated),) + summary_mutations
        result = await self._store.transact(_transition(
            scope=scope, mutations=mutations, index_mutations=(
                _index_remove(_index(scope, "delivery.claimed"), updated.delivery_id),
                _index_remove(_index(scope, "delivery.lease"), updated.delivery_id),
                _index_remove(_target_index(scope, updated.target_fingerprint), updated.delivery_id),
                _index_remove(_runtime_ready_index(scope), updated.delivery_id),
                _index_add(_index(scope, {
                    DeliveryRecordStatus.TARGET_WAITING: "delivery.waiting",
                    DeliveryRecordStatus.EXPIRED: "delivery.expired",
                    DeliveryRecordStatus.PAYLOAD_REJECTED: "delivery.payload_rejected",
                }[status]), updated.delivery_id, now.timestamp()),
            ), operation="precheck_failed", delivery=updated, now=now,
        ))
        _validate_transaction(result, mutations, "fail_precheck")
        return updated

    async def _recover_expired_for_claim(
        self, *, scope: StateAccessScope, runtime_id: str, worker_id: str,
        claim_token: str, policy: DeliverySchedulingPolicy, now, budget: int,
    ) -> tuple[ClaimResult | None, int]:
        consumed = 0
        while consumed < budget:
            due = await self._read_progress_page(
                scope=scope,
                index=_index(scope, "delivery.lease"),
                cursor_name="claim.lease",
                limit=min(16, budget - consumed),
                max_score=now.timestamp(),
            )
            if not due.entries:
                break
            consumed += len(due.entries)
            for entry in due.entries:
                recovered = await self._recover_due_entry(
                    scope=scope,
                    entry=entry,
                    runtime_id=runtime_id,
                    worker_id=worker_id,
                    claim_token=claim_token,
                    policy=policy,
                    now=now,
                )
                if recovered is not None:
                    return recovered, consumed
            if due.next_cursor is None:
                break
        return None, consumed

    async def _recover_due_entry(
        self, *, scope: StateAccessScope, entry, runtime_id: str,
        worker_id: str, claim_token: str, policy: DeliverySchedulingPolicy, now,
    ) -> ClaimResult | None:
        lease_index = _index(scope, "delivery.lease")
        try:
            authority = await self._read_delivery(scope, entry.member)
        except NsRuntimeStateStoreUnavailableError as error:
            if not _repairable_authority_error(error):
                raise
            await self._repair_ordered_projection(
                scope=scope,
                index=lease_index,
                entry=entry,
                reason="record_missing_or_malformed",
                observe_missing_or_malformed=True,
                quarantine=True,
            )
            return None
        if (
            authority.value.authority_bucket_count != policy.authority_bucket_count
            or authority.value.authority_bucket_id != _bucket_id(scope)
            or authority.value.authority_layout_version != policy.authority_layout_version
            or authority.value.authority_layout_generation != policy.authority_layout_generation
        ):
            await self._repair_ordered_projection(
                scope=scope,
                index=lease_index,
                entry=entry,
                reason="authority_layout_mismatch",
                observed_record=authority.record,
                quarantine=True,
            )
            return None
        old = authority.value.owner
        if old is None:
            await self._repair_ordered_projection(
                scope=scope,
                index=lease_index,
                entry=entry,
                reason="owner_missing",
                observed_record=authority.record,
            )
            return None
        if old.lease_expires_at > now:
            await self._repair_ordered_projection(
                scope=scope,
                index=lease_index,
                entry=entry,
                reason="lease_score_stale",
                observed_record=authority.record,
                replacement_score=old.lease_expires_at.timestamp(),
            )
            return None
        if old.runtime_id != runtime_id:
            await self._repair_ordered_projection(
                scope=scope,
                index=lease_index,
                entry=entry,
                reason="foreign_runtime_owner",
                observed_record=authority.record,
                quarantine=True,
            )
            return None
        if authority.value.status not in {
            DeliveryRecordStatus.QUEUED,
            DeliveryRecordStatus.SENDING,
            DeliveryRecordStatus.ACK_WAITING,
        }:
            await self._repair_ordered_projection(
                scope=scope,
                index=lease_index,
                entry=entry,
                reason="status_not_lease_managed",
                observed_record=authority.record,
            )
            return None
        if authority.value.status is DeliveryRecordStatus.QUEUED:
            owner = DeliveryOwner(
                schema_version=P11_OWNER_SCHEMA_VERSION,
                runtime_id=runtime_id, worker_id=worker_id,
                claim_token=claim_token, claimed_at=now,
                lease_expires_at=now + timedelta(seconds=policy.lease_ttl_seconds),
                renew_failures=0, risk=DeliveryOwnerRisk.HEALTHY,
                fencing=authority.value.last_fencing + 1,
                owner_epoch=authority.value.owner_epoch + 1,
            )
            updated = dataclasses.replace(
                authority.value, owner=owner, last_fencing=owner.fencing,
                owner_epoch=owner.owner_epoch,
                state_version=authority.value.state_version + 1, updated_at=now,
            )
            mutation = _replace_delivery(authority.record, updated)
            try:
                result = await self._store.transact(_transition(
                    scope=scope, mutations=(mutation,), index_mutations=(
                        _index_add(lease_index, updated.delivery_id,
                                   owner.lease_expires_at.timestamp()),
                    ), operation="owner_recovered", delivery=updated, now=now,
                ))
            except NsRuntimeStateStoreConflictError:
                return None
            _validate_transaction(result, (mutation,), "recover_owner")
            claim = DeliveryClaim(
                tenant_id=updated.tenant_id, delivery_id=updated.delivery_id,
                runtime_id=runtime_id, worker_id=worker_id,
                claim_token=claim_token, fencing=owner.fencing,
                owner_epoch=owner.owner_epoch,
                authority_bucket_count=updated.authority_bucket_count,
                authority_bucket_id=updated.authority_bucket_id,
                authority_layout_version=updated.authority_layout_version,
                authority_layout_generation=updated.authority_layout_generation,
            )
            return ClaimResult(
                outcome=ClaimOutcome.CLAIMED,
                claim=claim,
                delivery=updated,
            )
        if authority.value.status is DeliveryRecordStatus.SENDING:
            try:
                attempt_value, attempt_record = await self._read_attempt(
                    scope, authority.value.current_attempt_id,
                )
            except NsRuntimeStateStoreUnavailableError as error:
                if not _repairable_authority_error(error):
                    raise
                await self._repair_ordered_projection(
                    scope=scope,
                    index=lease_index,
                    entry=entry,
                    reason="sending_attempt_missing_or_malformed",
                    observed_record=authority.record,
                    quarantine=True,
                )
                return None
            uncertain = dataclasses.replace(
                authority.value, status=DeliveryRecordStatus.WRITE_UNCERTAIN,
                owner=None, ack_deadline=None,
                last_failure=DeliveryWriteFailure.AUTHORITY_CONFLICT_AFTER_WRITE,
                state_version=authority.value.state_version + 1, updated_at=now,
            )
            uncertain_attempt = dataclasses.replace(
                attempt_value, status=DeliveryAttemptStatus.WRITE_UNCERTAIN,
                completed_at=now,
                failure=DeliveryWriteFailure.AUTHORITY_CONFLICT_AFTER_WRITE,
            )
            summaries = await self._summary_mutations(
                scope, authority.value, sending=-1, write_uncertain=1, now=now,
            )
            mutations = (
                _replace_delivery(authority.record, uncertain),
                _replace_attempt(attempt_record, uncertain_attempt),
            ) + summaries
            try:
                result = await self._store.transact(_transition(
                    scope=scope, mutations=mutations, index_mutations=(
                        _index_remove(lease_index, uncertain.delivery_id),
                        _index_remove(_index(scope, "delivery.sending"),
                                      uncertain.delivery_id),
                        _index_add(_index(scope, "delivery.write_uncertain"),
                                   uncertain.delivery_id, now.timestamp()),
                    ), operation="write_uncertain", delivery=uncertain, now=now,
                ))
            except NsRuntimeStateStoreConflictError:
                return None
            _validate_transaction(result, mutations, "recover_sending")
            return None
        owner = dataclasses.replace(
            old, worker_id=worker_id, claim_token=claim_token,
            claimed_at=now,
            lease_expires_at=now + timedelta(seconds=policy.lease_ttl_seconds),
            fencing=authority.value.last_fencing + 1,
            owner_epoch=authority.value.owner_epoch + 1,
            renew_failures=0,
            risk=DeliveryOwnerRisk.HEALTHY, risk_since=None,
            protection_until=None,
        )
        updated = dataclasses.replace(
            authority.value, owner=owner, last_fencing=owner.fencing,
            owner_epoch=owner.owner_epoch,
            state_version=authority.value.state_version + 1, updated_at=now,
        )
        mutation = _replace_delivery(authority.record, updated)
        try:
            result = await self._store.transact(_transition(
                scope=scope, mutations=(mutation,), index_mutations=(
                    _index_add(lease_index, updated.delivery_id,
                               owner.lease_expires_at.timestamp()),
                ), operation="ack_owner_recovered", delivery=updated, now=now,
            ))
        except NsRuntimeStateStoreConflictError:
            return None
        _validate_transaction(result, (mutation,), "recover_ack")
        return None

    async def start_sending(
        self,
        *,
        claim: DeliveryClaim,
        attempt_id: str,
        policy: DeliverySchedulingPolicy,
    ) -> SendingTransition:
        if not isinstance(claim, DeliveryClaim):
            _invalid("start.claim")
        _text(attempt_id, "start.attempt_id")
        if not isinstance(policy, DeliverySchedulingPolicy):
            _invalid("start.policy")
        scope = _claim_scope(self._store, claim)
        authority = await self._read_delivery(scope, claim.delivery_id)
        now = self._clock.utc_now()
        owner = _require_owner(authority.value, claim, now, allow_risk=False)
        value = authority.value
        if value.status is not DeliveryRecordStatus.QUEUED:
            raise NsRuntimeDeliveryStateError(details={
                "component": "delivery_scheduler", "operation": "start_sending",
                "reason": "queued_required",
            })
        if value.activation is None:
            raise NsRuntimeDeliveryStateError(details={
                "component": "delivery_scheduler", "operation": "start_sending",
                "reason": "activation_required",
            })
        if value.policy_decision.expires_at <= now:
            raise NsRuntimeDeliveryStateError(details={
                "component": "delivery_scheduler", "operation": "start_sending",
                "reason": "expired",
            })
        deadline = now + timedelta(seconds=value.policy_decision.ack_timeout_seconds)
        attempt = DeliveryAttempt(
            schema_version=P11_ATTEMPT_SCHEMA_VERSION,
            attempt_id=attempt_id,
            delivery_id=value.delivery_id,
            tenant_id=value.tenant_id,
            attempt_number=value.attempt_count + 1,
            owner_runtime_id=owner.runtime_id,
            owner_worker_id=owner.worker_id,
            owner_claim_token=owner.claim_token,
            owner_fencing=owner.fencing,
            owner_epoch=owner.owner_epoch,
            config_version=value.policy_decision.config_version,
            policy_version=value.policy_decision.policy_version,
            target_fingerprint=value.target_fingerprint,
            status=DeliveryAttemptStatus.WRITING,
            started_at=now,
            ack_deadline=deadline,
        )
        sending = dataclasses.replace(
            value,
            status=DeliveryRecordStatus.SENDING,
            current_attempt_id=attempt_id,
            attempt_count=attempt.attempt_number,
            ack_deadline=deadline,
            state_version=value.state_version + 1,
            updated_at=now,
        )
        summary_mutations = await self._summary_mutations(
            scope, value, queued=-1, sending=1, now=now,
        )
        mutations = (
            _replace_delivery(authority.record, sending),
            _create_attempt(scope.namespace, attempt),
        ) + summary_mutations
        indexes = (
            _index_remove(_index(scope, "delivery.claimed"), value.delivery_id),
            _index_remove(_target_index(scope, value.target_fingerprint), value.delivery_id),
            _index_remove(_runtime_ready_index(scope), value.delivery_id),
            _index_add(_index(scope, "delivery.sending"), value.delivery_id, now.timestamp()),
        )
        result = await self._store.transact(_transition(
            scope=scope, mutations=mutations, index_mutations=indexes,
            operation="sending_started", delivery=sending, now=now,
        ))
        _validate_transaction(result, mutations, "start_sending")
        return SendingTransition(delivery=sending, attempt=attempt)

    async def complete_write_success(
        self,
        *,
        claim: DeliveryClaim,
        expected_state_version: int | None = None,
    ) -> DeliveryRecord:
        if expected_state_version is not None and (
            isinstance(expected_state_version, bool)
            or not isinstance(expected_state_version, int)
            or expected_state_version <= 0
        ):
            _invalid("complete.expected_state_version")
        return await self._complete_write(
            claim=claim,
            failure=None,
            expected_state_version=expected_state_version,
        )

    async def complete_write_failure(
        self,
        *,
        claim: DeliveryClaim,
        failure: DeliveryWriteFailure,
    ) -> DeliveryRecord:
        if not isinstance(failure, DeliveryWriteFailure):
            _invalid("complete.failure")
        return await self._complete_write(
            claim=claim, failure=failure, expected_state_version=None,
        )

    async def mark_write_uncertain(
        self,
        *,
        claim: DeliveryClaim,
        failure: DeliveryWriteFailure = (
            DeliveryWriteFailure.AUTHORITY_CONFLICT_AFTER_WRITE
        ),
    ) -> DeliveryRecord:
        if (
            not isinstance(claim, DeliveryClaim)
            or failure not in {
                DeliveryWriteFailure.TRANSPORT_WRITE_FAILED,
                DeliveryWriteFailure.TRANSPORT_WRITE_TIMEOUT,
                DeliveryWriteFailure.SHUTDOWN_INTERRUPTED,
                DeliveryWriteFailure.AUTHORITY_CONFLICT_AFTER_WRITE,
            }
        ):
            _invalid("uncertain.claim")
        scope = _claim_scope(self._store, claim)
        authority = await self._read_delivery(scope, claim.delivery_id)
        now = self._clock.utc_now()
        _require_owner(authority.value, claim, now, allow_risk=True)
        value = authority.value
        if value.status is not DeliveryRecordStatus.SENDING or value.current_attempt_id is None:
            raise NsRuntimeDeliveryStateError(details={
                "component": "delivery_scheduler", "operation": "mark_write_uncertain",
                "reason": "sending_required",
            })
        attempt, attempt_record = await self._read_attempt(scope, value.current_attempt_id)
        uncertain = dataclasses.replace(
            value, status=DeliveryRecordStatus.WRITE_UNCERTAIN, owner=None,
            ack_deadline=None,
            last_failure=failure,
            state_version=value.state_version + 1, updated_at=now,
        )
        uncertain_attempt = dataclasses.replace(
            attempt, status=DeliveryAttemptStatus.WRITE_UNCERTAIN,
            completed_at=now,
            failure=failure,
        )
        summaries = await self._summary_mutations(
            scope, value, sending=-1, write_uncertain=1, now=now,
        )
        mutations = (_replace_delivery(authority.record, uncertain),
                     _replace_attempt(attempt_record, uncertain_attempt)) + summaries
        result = await self._store.transact(_transition(
            scope=scope, mutations=mutations, index_mutations=(
                _index_remove(_index(scope, "delivery.lease"), value.delivery_id),
                _index_remove(_index(scope, "delivery.sending"), value.delivery_id),
                _index_add(_index(scope, "delivery.write_uncertain"), value.delivery_id, now.timestamp()),
            ), operation="write_uncertain", delivery=uncertain, now=now,
        ))
        _validate_transaction(result, mutations, "mark_write_uncertain")
        return uncertain

    async def reconcile_write_completion(
        self, *, claim: DeliveryClaim,
    ) -> DeliveryRecord:
        """Resolve every typed completion anomaly after transport accepted bytes."""
        if not isinstance(claim, DeliveryClaim):
            _invalid("reconcile.claim")
        scope = _claim_scope(self._store, claim)
        authority = await self._read_delivery(scope, claim.delivery_id)
        value = authority.value
        if value.current_attempt_id is None:
            raise NsRuntimeDeliveryStateError(details={
                "component": "delivery_scheduler",
                "operation": "reconcile_write_completion",
                "reason": "attempt_required",
            })
        attempt, attempt_record = await self._read_attempt(
            scope,
            value.current_attempt_id,
        )
        if not _attempt_matches_claim(attempt, value, claim):
            raise NsRuntimeDeliveryStateError(details={
                "component": "delivery_scheduler",
                "operation": "reconcile_write_completion",
                "reason": "committed_attempt_mismatch",
            })
        if value.status is DeliveryRecordStatus.ACK_WAITING:
            if attempt.status is not DeliveryAttemptStatus.WRITE_SUCCEEDED:
                raise NsRuntimeDeliveryStateError(details={
                    "component": "delivery_scheduler",
                    "operation": "reconcile_write_completion",
                    "reason": "committed_attempt_mismatch",
                })
            return value
        if value.status is DeliveryRecordStatus.SENDING:
            if attempt.status is not DeliveryAttemptStatus.WRITING:
                raise NsRuntimeDeliveryStateError(details={
                    "component": "delivery_scheduler",
                    "operation": "reconcile_write_completion",
                    "reason": "sending_attempt_mismatch",
                })
            return await self._reconcile_sending_as_uncertain(
                scope=scope,
                authority=authority,
                attempt=attempt,
                attempt_record=attempt_record,
            )
        raise NsRuntimeDeliveryStateError(details={
            "component": "delivery_scheduler",
            "operation": "reconcile_write_completion",
            "reason": "completion_reconcile_conflict",
            "status": value.status.value,
        })

    async def _reconcile_sending_as_uncertain(
        self,
        *,
        scope: StateAccessScope,
        authority: _DeliveryAuthority,
        attempt: DeliveryAttempt,
        attempt_record: StateRecord,
    ) -> DeliveryRecord:
        """CAS an attempt-bound SENDING record without requiring a live owner."""

        now = self._clock.utc_now()
        value = authority.value
        uncertain = dataclasses.replace(
            value,
            status=DeliveryRecordStatus.WRITE_UNCERTAIN,
            owner=None,
            ack_deadline=None,
            last_failure=DeliveryWriteFailure.AUTHORITY_CONFLICT_AFTER_WRITE,
            state_version=value.state_version + 1,
            updated_at=now,
        )
        uncertain_attempt = dataclasses.replace(
            attempt,
            status=DeliveryAttemptStatus.WRITE_UNCERTAIN,
            completed_at=now,
            failure=DeliveryWriteFailure.AUTHORITY_CONFLICT_AFTER_WRITE,
        )
        summaries = await self._summary_mutations(
            scope,
            value,
            sending=-1,
            write_uncertain=1,
            now=now,
        )
        mutations = (
            _replace_delivery(authority.record, uncertain),
            _replace_attempt(attempt_record, uncertain_attempt),
        ) + summaries
        result = await self._store.transact(_transition(
            scope=scope,
            mutations=mutations,
            index_mutations=(
                _index_remove(_index(scope, "delivery.lease"), value.delivery_id),
                _index_remove(_index(scope, "delivery.sending"), value.delivery_id),
                _index_add(
                    _index(scope, "delivery.write_uncertain"),
                    value.delivery_id,
                    now.timestamp(),
                ),
            ),
            operation="write_uncertain",
            delivery=uncertain,
            now=now,
        ))
        _validate_transaction(result, mutations, "reconcile_write_uncertain")
        return uncertain

    async def load_claimed(self, *, claim: DeliveryClaim) -> DeliveryRecord:
        if not isinstance(claim, DeliveryClaim):
            _invalid("load.claim")
        authority = await self._read_delivery(
            _claim_scope(self._store, claim),
            claim.delivery_id,
        )
        _require_owner(authority.value, claim, self._clock.utc_now(), allow_risk=True)
        return authority.value

    async def _complete_write(
        self,
        *,
        claim: DeliveryClaim,
        failure: DeliveryWriteFailure | None,
        expected_state_version: int | None,
    ) -> DeliveryRecord:
        if not isinstance(claim, DeliveryClaim):
            _invalid("complete.claim")
        scope = _claim_scope(self._store, claim)
        authority = await self._read_delivery(scope, claim.delivery_id)
        if (
            expected_state_version is not None
            and authority.value.state_version != expected_state_version
        ):
            raise NsRuntimeStateStoreConflictError(details={
                "component": "delivery_scheduler",
                "operation": "complete_write",
                "reason": "post_write_authority_revision_changed",
            })
        now = self._clock.utc_now()
        owner = _require_owner(authority.value, claim, now, allow_risk=True)
        if (
            owner.risk is DeliveryOwnerRisk.AT_RISK
            and (
                owner.protection_until is None
                or owner.protection_until <= now
            )
        ):
            raise NsRuntimeDeliveryStateError(details={
                "component": "delivery_scheduler", "operation": "complete_write",
                "reason": "owner_risk_window_closed",
            })
        value = authority.value
        if (
            value.status is not DeliveryRecordStatus.SENDING
            or value.current_attempt_id is None
        ):
            raise NsRuntimeDeliveryStateError(details={
                "component": "delivery_scheduler", "operation": "complete_write",
                "reason": "sending_required",
            })
        attempt_authority = await self._read_attempt(
            scope,
            value.current_attempt_id,
        )
        attempt = attempt_authority[0]
        if (
            attempt.status is not DeliveryAttemptStatus.WRITING
            or attempt.delivery_id != value.delivery_id
            or attempt.owner_claim_token != claim.claim_token
            or attempt.owner_fencing != claim.fencing
            or attempt.owner_epoch != claim.owner_epoch
            or attempt.attempt_number != value.attempt_count
        ):
            raise NsRuntimeDeliveryStateError(details={
                "component": "delivery_scheduler", "operation": "complete_write",
                "reason": "attempt_mismatch",
            })
        if failure is None:
            updated = dataclasses.replace(
                value,
                status=DeliveryRecordStatus.ACK_WAITING,
                state_version=value.state_version + 1,
                updated_at=now,
            )
            completed_attempt = dataclasses.replace(
                attempt,
                status=DeliveryAttemptStatus.WRITE_SUCCEEDED,
                completed_at=now,
            )
            summary_mutations = await self._summary_mutations(
                scope, value, sending=-1, ack_waiting=1, now=now,
            )
            index_mutations = (
                _index_remove(_index(scope, "delivery.sending"), value.delivery_id),
                _index_add(_index(scope, "delivery.ack"), value.delivery_id,
                           value.ack_deadline.timestamp()),
                _index_add(_index(scope, "delivery.lease"), value.delivery_id,
                           owner.lease_expires_at.timestamp()),
            )
        else:
            updated = dataclasses.replace(
                value,
                status=DeliveryRecordStatus.WRITE_FAILED,
                owner=None,
                ack_deadline=None,
                last_failure=failure,
                state_version=value.state_version + 1,
                updated_at=now,
            )
            completed_attempt = dataclasses.replace(
                attempt,
                status=DeliveryAttemptStatus.WRITE_FAILED,
                completed_at=now,
                failure=failure,
            )
            summary_mutations = await self._summary_mutations(
                scope, value, sending=-1, write_failed=1, now=now,
            )
            index_mutations = (
                _index_remove(_index(scope, "delivery.sending"), value.delivery_id),
                _index_remove(_index(scope, "delivery.lease"), value.delivery_id),
                _index_add(_index(scope, "delivery.write_failed"), value.delivery_id, now.timestamp()),
            )
        attempt_record = attempt_authority[1]
        mutations = (
            _replace_delivery(authority.record, updated),
            _replace_attempt(attempt_record, completed_attempt),
        ) + summary_mutations
        result = await self._store.transact(_transition(
            scope=scope, mutations=mutations, index_mutations=index_mutations,
            operation=("write_succeeded" if failure is None else "write_failed"),
            delivery=updated, now=now,
        ))
        _validate_transaction(result, mutations, "complete_write")
        return updated

    async def _read_delivery(
        self,
        scope: StateAccessScope,
        delivery_id: str,
    ) -> _DeliveryAuthority:
        record = await _read_record(self._store, scope, "delivery", delivery_id)
        value = _decode_delivery(record)
        if value.delivery_id != delivery_id:
            _unavailable("read_delivery", "identifier_mismatch")
        return _DeliveryAuthority(value=value, record=record)

    async def _read_attempt(
        self,
        scope: StateAccessScope,
        attempt_id: str,
    ) -> tuple[DeliveryAttempt, StateRecord]:
        record = await _read_record(self._store, scope, "attempt", attempt_id)
        try:
            value = attempt_from_dict(json.loads(record.document.payload))
        except (ValueError, UnicodeError, json.JSONDecodeError, NsValidationError):
            _unavailable("read_attempt", "malformed_authority_record")
        if value.attempt_id != attempt_id:
            _unavailable("read_attempt", "identifier_mismatch")
        return value, record

    async def _read_summary(
        self, scope: StateAccessScope, summary_id: str,
    ) -> _SummaryAuthority:
        record = await _read_record(self._store, scope, "summary", summary_id)
        value = _decode_summary(record)
        if value.summary_id != summary_id:
            _unavailable("read_summary", "identifier_mismatch")
        return _SummaryAuthority(value=value, record=record)

    async def _summary_mutations(
        self, scope: StateAccessScope, delivery: DeliveryRecord, *,
        prepared: int = 0, queued: int = 0, sending: int = 0,
        ack_waiting: int = 0, write_failed: int = 0, waiting: int = 0,
        expired: int = 0, payload_rejected: int = 0,
        write_uncertain: int = 0, now,
    ) -> tuple[StateMutation, ...]:
        identifiers = (delivery.root_summary_id,) if (
            delivery.summary_id == delivery.root_summary_id
        ) else (delivery.root_summary_id, delivery.summary_id)
        values: list[StateMutation] = []
        for identifier in identifiers:
            authority = await self._read_summary(scope, identifier)
            updated = _summary_delta(
                authority.value, prepared=prepared, queued=queued,
                sending=sending, ack_waiting=ack_waiting,
                write_failed=write_failed, waiting=waiting, expired=expired,
                payload_rejected=payload_rejected,
                write_uncertain=write_uncertain, now=now,
            )
            values.append(_replace_summary(authority.record, updated))
        return tuple(values)

    async def _read_bound_summaries(
        self,
        scope: StateAccessScope,
        delivery: DeliveryRecord,
    ) -> tuple[_SummaryAuthority, _SummaryAuthority]:
        root_record = await _read_record(
            self._store, scope, "summary", delivery.root_summary_id,
        )
        shard_record = (root_record if delivery.summary_id == delivery.root_summary_id
                        else await _read_record(
                            self._store, scope, "summary", delivery.summary_id,
                        ))
        root = _SummaryAuthority(value=_decode_summary(root_record), record=root_record)
        shard = _SummaryAuthority(value=_decode_summary(shard_record), record=shard_record)
        if (
            root.value.summary_id != delivery.root_summary_id
            or shard.value.summary_id != delivery.summary_id
            or shard.value.root_summary_id != root.value.summary_id
        ):
            _unavailable("read_summaries", "authority_chain_mismatch")
        return root, shard


async def _read_record(
    store: StateStore,
    scope: StateAccessScope,
    object_type: str,
    identifier: str,
) -> StateRecord:
    result = await store.read(
        scope=scope,
        key=StateKey(
            namespace=scope.namespace,
            object_type=object_type,
            object_id=_key_digest(identifier),
        ),
        consistency=StateConsistency.LINEARIZABLE,
    )
    if result.record is None:
        _unavailable("read", "authority_record_missing")
    return result.record


def _scope(
    store: StateStore,
    tenant_id: str, bucket_id: int, *, layout_generation: int = 2,
) -> StateAccessScope:
    return delivery_scope(
        store, tenant_id, bucket_id, layout_generation=layout_generation,
        caller="delivery.scheduling",
    )


def _claim_scope(
    store: StateStore,
    claim: DeliveryClaim,
) -> StateAccessScope:
    return _scope(
        store,
        claim.tenant_id,
        claim.authority_bucket_id,
        layout_generation=claim.authority_layout_generation,
    )


def _layout(policy: DeliverySchedulingPolicy) -> DeliveryAuthorityLayout:
    return DeliveryAuthorityLayout(
        version=policy.authority_layout_version,
        generation=policy.authority_layout_generation,
        bucket_count=policy.authority_bucket_count,
    )


def _bucket_id(scope: StateAccessScope) -> int:
    partition = scope.atomic_scope.partition
    marker = "-bucket-"
    if not partition.startswith("layout-") or marker not in partition:
        raise NsRuntimeDeliveryStateError(details={
            "component": "delivery_scheduler",
            "operation": "bucket_id",
            "reason": "authority_layout_partition_invalid",
        })
    try:
        return int(partition.rsplit(marker, 1)[1])
    except ValueError:
        raise NsRuntimeDeliveryStateError(details={
            "component": "delivery_scheduler",
            "operation": "bucket_id",
            "reason": "authority_layout_partition_invalid",
        }) from None


def _replace_delivery(record: StateRecord, value: DeliveryRecord) -> StateMutation:
    return _replace(record, value.state_version, delivery_to_dict(value))


def _replace_summary(
    record: StateRecord,
    value: MessageDeliverySummary,
) -> StateMutation:
    return _replace(record, value.state_version, summary_to_dict(value))


def _replace_attempt(record: StateRecord, value: DeliveryAttempt) -> StateMutation:
    return _replace(record, record.document.state_version + 1, attempt_to_dict(value))


def _replace(
    record: StateRecord,
    state_version: int,
    payload: dict[str, object],
) -> StateMutation:
    return StateMutation(
        key=record.key,
        assertion=StateAssertion.matches(
            record.revision,
            state_version=record.document.state_version,
        ),
        kind=StateMutationKind.REPLACE,
        document=StateDocument(
            schema_name=record.document.schema_name,
            schema_version=record.document.schema_version,
            state_version=state_version,
            payload=_json(payload),
        ),
    )


def _create_attempt(namespace: StateNamespace, value: DeliveryAttempt) -> StateMutation:
    return StateMutation(
        key=StateKey(
            namespace=namespace,
            object_type="attempt",
            object_id=_key_digest(value.attempt_id),
        ),
        assertion=StateAssertion.absent(),
        kind=StateMutationKind.CREATE,
        document=StateDocument(
            schema_name="delivery_attempt",
            schema_version=1,
            state_version=1,
            payload=_json(attempt_to_dict(value)),
        ),
    )


def _summary_delta(
    value: MessageDeliverySummary,
    *,
    now,
    prepared: int = 0,
    queued: int = 0,
    sending: int = 0,
    ack_waiting: int = 0,
    write_failed: int = 0,
    waiting: int = 0,
    expired: int = 0,
    payload_rejected: int = 0,
    write_uncertain: int = 0,
) -> MessageDeliverySummary:
    return dataclasses.replace(
        value,
        prepared_count=value.prepared_count + prepared,
        queued_count=value.queued_count + queued,
        sending_count=value.sending_count + sending,
        ack_waiting_count=value.ack_waiting_count + ack_waiting,
        write_failed_count=value.write_failed_count + write_failed,
        waiting_count=value.waiting_count + waiting,
        expired_count=value.expired_count + expired,
        payload_rejected_count=value.payload_rejected_count + payload_rejected,
        write_uncertain_count=value.write_uncertain_count + write_uncertain,
        active_count=value.active_count + sending,
        inflight_count=value.inflight_count + ack_waiting,
        state_version=value.state_version + 1,
        updated_at=now,
    )


def _require_owner(
    value: DeliveryRecord,
    claim: DeliveryClaim,
    now,
    *,
    allow_risk: bool,
) -> DeliveryOwner:
    owner = value.owner
    if (
        not isinstance(owner, DeliveryOwner)
        or owner.runtime_id != claim.runtime_id
        or owner.worker_id != claim.worker_id
        or owner.claim_token != claim.claim_token
        or owner.fencing != claim.fencing
        or owner.owner_epoch != claim.owner_epoch
        or value.last_fencing != claim.fencing
        or value.owner_epoch != claim.owner_epoch
        or value.authority_bucket_count != claim.authority_bucket_count
        or value.authority_bucket_id != claim.authority_bucket_id
        or value.authority_layout_version != claim.authority_layout_version
        or value.authority_layout_generation != claim.authority_layout_generation
    ):
        raise NsRuntimeOwnerMismatchError(details={
            "component": "delivery_scheduler", "reason": "claim_mismatch",
        })
    if owner.lease_expires_at <= now:
        raise NsRuntimeDeliveryLeaseExpiredError(details={
            "component": "delivery_scheduler", "reason": "lease_expired",
        })
    if not allow_risk and owner.risk is DeliveryOwnerRisk.AT_RISK:
        raise NsRuntimeDeliveryStateError(details={
            "component": "delivery_scheduler", "reason": "owner_at_risk",
        })
    return owner


def _attempt_matches_claim(
    attempt: DeliveryAttempt,
    delivery: DeliveryRecord,
    claim: DeliveryClaim,
) -> bool:
    return (
        type(attempt) is DeliveryAttempt
        and attempt.delivery_id == delivery.delivery_id == claim.delivery_id
        and attempt.attempt_id == delivery.current_attempt_id
        and attempt.attempt_number == delivery.attempt_count
        and attempt.owner_claim_token == claim.claim_token
        and attempt.owner_fencing == claim.fencing
        and attempt.owner_epoch == claim.owner_epoch
    )


def _decode_delivery(record: StateRecord) -> DeliveryRecord:
    try:
        value = delivery_from_dict(json.loads(record.document.payload))
    except (ValueError, UnicodeError, json.JSONDecodeError, NsValidationError):
        _unavailable("decode_delivery", "malformed_authority_record")
    if value.state_version != record.document.state_version:
        _unavailable("decode_delivery", "state_version_mismatch")
    return value


def _decode_summary(record: StateRecord) -> MessageDeliverySummary:
    try:
        value = summary_from_dict(json.loads(record.document.payload))
    except (ValueError, UnicodeError, json.JSONDecodeError, NsValidationError):
        _unavailable("decode_summary", "malformed_authority_record")
    if value.state_version != record.document.state_version:
        _unavailable("decode_summary", "state_version_mismatch")
    return value


def _validate_transaction(
    result: object,
    mutations: tuple[StateMutation, ...],
    operation: str,
) -> None:
    if not isinstance(result, StateTransactionResult) or len(result.records) != len(mutations):
        _unavailable(operation, "malformed_commit_result")
    if any(
        record is None
        or record.key != mutation.key
        or record.document != mutation.document
        for record, mutation in zip(result.records, mutations)
    ):
        _unavailable(operation, "commit_evidence_mismatch")


def _priority(value: DeliveryRecord) -> int:
    return {
        "low": 0,
        "normal": 1,
        "high": 2,
        "critical": 3,
    }[value.policy_decision.priority.value]


def _index(scope: StateAccessScope, name: str) -> StateOrderedIndexKey:
    return StateOrderedIndexKey(
        namespace=scope.namespace, name=name, bucket="delivery",
    )


def _scheduler_cursor_key(
    scope: StateAccessScope,
    name: str,
) -> StateKey:
    layout_generation, bucket_id, operation, index_identity = (
        _scheduler_cursor_identity(scope, name)
    )
    return StateKey(
        namespace=scope.namespace,
        object_type="delivery_scheduler_cursor",
        object_id=_key_digest(
            "scheduler-cursor-v2",
            str(layout_generation),
            str(bucket_id),
            operation,
            index_identity,
        ),
    )


def _legacy_scheduler_cursor_key(
    scope: StateAccessScope,
    name: str,
) -> StateKey:
    return StateKey(
        namespace=scope.namespace,
        object_type="delivery_scheduler_cursor",
        object_id=_key_digest("scheduler-cursor:" + name),
    )


def _scheduler_cursor_identity(
    scope: StateAccessScope,
    name: str,
) -> tuple[int, int, str, str]:
    if type(name) is not str or "." not in name:
        _invalid("scheduler_cursor.name")
    operation, index_identity = name.split(".", 1)
    if not operation or not index_identity:
        _invalid("scheduler_cursor.name")
    partition = scope.atomic_scope.partition
    marker = "-bucket-"
    if not partition.startswith("layout-") or marker not in partition:
        _invalid("scheduler_cursor.scope")
    generation_text = partition[len("layout-"):partition.index(marker)]
    try:
        generation = int(generation_text)
    except ValueError:
        _invalid("scheduler_cursor.scope")
    if generation < 1:
        _invalid("scheduler_cursor.scope")
    return generation, _bucket_id(scope), operation, index_identity


def _target_index(
    scope: StateAccessScope, target_fingerprint: str,
) -> StateOrderedIndexKey:
    return _index(scope, "delivery.target." + target_fingerprint.removeprefix("sha256:"))


def _runtime_ready_index(scope: StateAccessScope) -> StateOrderedIndexKey:
    return _index(scope, "delivery.runtime.ready")


def _index_add(
    index: StateOrderedIndexKey, member: str, score: float,
) -> StateOrderedIndexMutation:
    return StateOrderedIndexMutation(
        index=index, kind=StateOrderedIndexMutationKind.ADD,
        member=member, score=score,
    )


def _index_remove(
    index: StateOrderedIndexKey, member: str,
) -> StateOrderedIndexMutation:
    return StateOrderedIndexMutation(
        index=index, kind=StateOrderedIndexMutationKind.REMOVE, member=member,
    )


def _transition(
    *, scope: StateAccessScope, mutations: tuple[StateMutation, ...],
    index_mutations: tuple[StateOrderedIndexMutation, ...], operation: str,
    delivery: DeliveryRecord, now,
) -> StateTransaction:
    event = {
        "schema_version": "delivery-transition-event-1",
        "operation": operation,
        "delivery_id": delivery.delivery_id,
        "status": delivery.status.value,
        "state_version": delivery.state_version,
        "fencing": (None if delivery.owner is None else delivery.owner.fencing),
        "occurred_at": now.isoformat(),
    }
    return StateTransaction(
        scope=scope, mutations=mutations,
        ordered_index_mutations=index_mutations,
        log_appends=(StateTransitionLogAppend(
            key=StateKey(
                namespace=scope.namespace,
                object_type="delivery_transition_log",
                object_id=_key_digest(delivery.root_summary_id),
            ),
            document=StateDocument(
                schema_name="delivery_transition_event", schema_version=1,
                state_version=1, payload=_json(event),
            ),
        ),),
    )


def _reason(values: list[ActivationSkipReason], value: ActivationSkipReason) -> None:
    if value not in values:
        values.append(value)


def _json(value: dict[str, object]) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")


def _key_digest(*parts: str) -> str:
    return "sha256:" + hashlib.sha256("\0".join(parts).encode("utf-8")).hexdigest()


def _text(value: object, field: str) -> None:
    if type(value) is not str or not value:
        _invalid(field)


def _invalid(field: str):
    raise NsValidationError(
        "P11 scheduling store value is invalid.",
        details={"component": "delivery_scheduler", "field": field},
    )


def _unavailable(operation: str, reason: str):
    raise NsRuntimeStateStoreUnavailableError(details={
        "component": "delivery_scheduler",
        "operation": operation,
        "reason": reason,
    })


def _repairable_authority_error(
    error: NsRuntimeStateStoreUnavailableError,
) -> bool:
    """Only projection/record divergence may trigger an index repair write."""

    return error.details.get("reason") in {
        "authority_record_missing",
        "malformed_authority_record",
        "state_version_mismatch",
        "identifier_mismatch",
    }


__all__ = ("StateStoreDeliveryScheduler",)
