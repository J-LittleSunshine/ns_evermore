# -*- coding: utf-8 -*-
"""P11 atomic local scheduling authority over the P08 StateStore boundary."""

from __future__ import annotations

import dataclasses
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
    StateStore,
    StateTransaction,
    StateTransactionResult,
)
from ns_common.time import Clock

from .models import (
    P11_ACTIVATION_SCHEMA_VERSION,
    P11_ATTEMPT_SCHEMA_VERSION,
    P11_OWNER_SCHEMA_VERSION,
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


@dataclass(frozen=True, slots=True)
class _DeliveryAuthority:
    value: DeliveryRecord
    record: StateRecord


@dataclass(frozen=True, slots=True)
class _SummaryAuthority:
    value: MessageDeliverySummary
    record: StateRecord


class StateStoreDeliveryScheduler:
    """Single-runtime scheduler; Redis records remain the only state authority."""

    def __init__(self, *, store: StateStore, clock: Clock) -> None:
        if not isinstance(store, StateStore):
            _invalid("store")
        if not isinstance(clock, Clock):
            _invalid("clock")
        self._store = store
        self._clock = clock

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
        scope = _scope(tenant_id)
        deliveries = await self._scan_deliveries(scope)
        candidates = tuple(
            item for item in deliveries
            if item.value.status is DeliveryRecordStatus.PREPARED
        )
        queued = tuple(
            item for item in deliveries
            if item.value.status is DeliveryRecordStatus.QUEUED
        )
        queued_before = len(queued)
        if global_queued_before is None:
            global_queued_before = queued_before
        if (
            isinstance(global_queued_before, bool)
            or not isinstance(global_queued_before, int)
            or global_queued_before < queued_before
        ):
            _invalid("activate.global_queued_before")
        target_queued: dict[str, int] = {}
        for item in queued:
            target_queued[item.value.target_fingerprint] = (
                target_queued.get(item.value.target_fingerprint, 0) + 1
            )
        selected: list[_DeliveryAuthority] = []
        reasons: list[ActivationSkipReason] = []
        now = self._clock.utc_now()
        ordered = sorted(
            candidates,
            key=lambda item: (
                -_priority(item.value),
                item.value.created_at,
                item.value.target_index,
                item.value.delivery_id,
            ),
        )
        for item in ordered:
            value = item.value
            if value.policy_decision.expires_at <= now:
                _reason(reasons, ActivationSkipReason.EXPIRED)
                continue
            if len(selected) >= policy.activation_batch_size:
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
            target_count = target_queued.get(value.target_fingerprint, 0)
            if target_count >= policy.target_queued_high_watermark:
                _reason(reasons, ActivationSkipReason.TARGET_WATERMARK)
                continue
            selected.append(item)
            target_queued[value.target_fingerprint] = target_count + 1
        if not candidates:
            _reason(reasons, ActivationSkipReason.NO_PREPARED)
        if not selected:
            return ActivationResult(
                tenant_id=tenant_id,
                candidate_count=len(candidates),
                activated=(),
                queued_before=queued_before,
                queued_after=queued_before,
                global_queued_before=global_queued_before,
                global_queued_after=global_queued_before,
                skip_reasons=tuple(reasons),
                policy_version=policy.policy_version,
            )

        summaries = await self._scan_summaries(scope)
        summary_map = {item.value.summary_id: item for item in summaries}
        evidence = DeliveryActivationEvidence(
            schema_version=P11_ACTIVATION_SCHEMA_VERSION,
            config_version=policy.config_version,
            policy_version=policy.policy_version,
            reason="prepared_ready",
            batch_size=policy.activation_batch_size,
            candidate_count=len(candidates),
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
        per_summary: dict[str, int] = {}
        per_root: dict[str, int] = {}
        for value in activated:
            per_summary[value.summary_id] = per_summary.get(value.summary_id, 0) + 1
            per_root[value.root_summary_id] = per_root.get(value.root_summary_id, 0) + 1
        changed_summaries: list[tuple[_SummaryAuthority, MessageDeliverySummary]] = []
        for summary_id, count in {**per_summary, **per_root}.items():
            authority = summary_map.get(summary_id)
            if authority is None:
                _unavailable("activate", "summary_missing")
            changed_summaries.append((
                authority,
                _summary_delta(
                    authority.value,
                    prepared=-count,
                    queued=count,
                    now=now,
                ),
            ))
        mutations = tuple(
            _replace_delivery(item.record, value)
            for item, value in zip(selected, activated)
        ) + tuple(
            _replace_summary(authority.record, value)
            for authority, value in changed_summaries
        )
        result = await self._store.transact(StateTransaction(
            scope=scope,
            mutations=mutations,
        ))
        _validate_transaction(result, mutations, "activate")
        return ActivationResult(
            tenant_id=tenant_id,
            candidate_count=len(candidates),
            activated=activated,
            queued_before=queued_before,
            queued_after=queued_before + len(activated),
            global_queued_before=global_queued_before,
            global_queued_after=global_queued_before + len(activated),
            skip_reasons=tuple(reasons),
            policy_version=policy.policy_version,
        )

    async def resource_counts(self, *, tenant_id: str) -> DeliveryResourceCounts:
        """Rebuild P11 resource counts from authoritative delivery records."""

        _text(tenant_id, "resource_counts.tenant_id")
        values = tuple(
            item.value for item in await self._scan_deliveries(_scope(tenant_id))
        )
        counts = DeliveryResourceCounts(
            tenant_id=tenant_id,
            prepared=sum(value.status is DeliveryRecordStatus.PREPARED for value in values),
            queued=sum(value.status is DeliveryRecordStatus.QUEUED for value in values),
            sending=sum(value.status is DeliveryRecordStatus.SENDING for value in values),
            ack_waiting=sum(
                value.status is DeliveryRecordStatus.ACK_WAITING for value in values
            ),
            write_failed=sum(
                value.status is DeliveryRecordStatus.WRITE_FAILED for value in values
            ),
        )
        roots = tuple(
            item.value for item in await self._scan_summaries(_scope(tenant_id))
            if item.value.shard_index is None
        )
        persisted = (
            sum(value.prepared_count for value in roots),
            sum(value.queued_count for value in roots),
            sum(value.sending_count for value in roots),
            sum(value.ack_waiting_count for value in roots),
            sum(value.write_failed_count for value in roots),
        )
        observed = (
            counts.prepared, counts.queued, counts.sending,
            counts.ack_waiting, counts.write_failed,
        )
        if persisted != observed:
            _unavailable("resource_counts", "summary_delivery_count_mismatch")
        return counts

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
        scope = _scope(tenant_id)
        candidates = sorted(
            (
                item for item in await self._scan_deliveries(scope)
                if item.value.status is DeliveryRecordStatus.QUEUED
                and item.value.owner is None
            ),
            key=lambda item: (
                -_priority(item.value), item.value.activation.activated_at,  # type: ignore[union-attr]
                item.value.delivery_id,
            ),
        )
        if not candidates:
            return ClaimResult(outcome=ClaimOutcome.EMPTY, claim=None, delivery=None)
        authority = candidates[0]
        now = self._clock.utc_now()
        owner = DeliveryOwner(
            schema_version=P11_OWNER_SCHEMA_VERSION,
            runtime_id=runtime_id,
            worker_id=worker_id,
            claim_token=claim_token,
            claimed_at=now,
            lease_expires_at=now + timedelta(seconds=policy.lease_ttl_seconds),
            renew_failures=0,
            risk=DeliveryOwnerRisk.HEALTHY,
        )
        claimed = dataclasses.replace(
            authority.value,
            owner=owner,
            state_version=authority.value.state_version + 1,
            updated_at=now,
        )
        try:
            record = await self._store.compare_and_set(
                scope=scope,
                mutation=_replace_delivery(authority.record, claimed),
            )
        except NsRuntimeStateStoreConflictError:
            return ClaimResult(outcome=ClaimOutcome.CONTENDED, claim=None, delivery=None)
        if record is None or record.document.payload != _json(delivery_to_dict(claimed)):
            _unavailable("claim", "commit_evidence_mismatch")
        claim = DeliveryClaim(
            tenant_id=tenant_id,
            delivery_id=claimed.delivery_id,
            runtime_id=runtime_id,
            worker_id=worker_id,
            claim_token=claim_token,
        )
        return ClaimResult(
            outcome=ClaimOutcome.CLAIMED,
            claim=claim,
            delivery=claimed,
        )

    async def renew_owner(
        self,
        *,
        claim: DeliveryClaim,
        policy: DeliverySchedulingPolicy,
        renewal_succeeded: bool,
    ) -> DeliveryRecord:
        if not isinstance(claim, DeliveryClaim):
            _invalid("renew.claim")
        if not isinstance(policy, DeliverySchedulingPolicy):
            _invalid("renew.policy")
        if type(renewal_succeeded) is not bool:
            _invalid("renew.renewal_succeeded")
        scope = _scope(claim.tenant_id)
        authority = await self._read_delivery(scope, claim.delivery_id)
        owner = _require_owner(authority.value, claim, self._clock.utc_now(), allow_risk=True)
        now = self._clock.utc_now()
        if renewal_succeeded:
            next_owner = dataclasses.replace(
                owner,
                lease_expires_at=now + timedelta(seconds=policy.lease_ttl_seconds),
                renew_failures=0,
                risk=DeliveryOwnerRisk.HEALTHY,
                risk_since=None,
                protection_until=None,
            )
        else:
            failures = owner.renew_failures + 1
            if failures > policy.max_renew_failures:
                next_owner = dataclasses.replace(
                    owner,
                    renew_failures=failures,
                    risk=DeliveryOwnerRisk.AT_RISK,
                    risk_since=now,
                    protection_until=now + timedelta(
                        seconds=policy.owner_risk_window_seconds,
                    ),
                )
            else:
                next_owner = dataclasses.replace(owner, renew_failures=failures)
        updated = dataclasses.replace(
            authority.value,
            owner=next_owner,
            state_version=authority.value.state_version + 1,
            updated_at=now,
        )
        record = await self._store.compare_and_set(
            scope=scope,
            mutation=_replace_delivery(authority.record, updated),
        )
        if record is None:
            _unavailable("renew", "commit_record_missing")
        return updated

    async def release_claim(self, *, claim: DeliveryClaim) -> DeliveryRecord:
        if not isinstance(claim, DeliveryClaim):
            _invalid("release.claim")
        scope = _scope(claim.tenant_id)
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
        record = await self._store.compare_and_set(
            scope=scope,
            mutation=_replace_delivery(authority.record, updated),
        )
        if record is None:
            _unavailable("release_claim", "commit_record_missing")
        return updated

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
        scope = _scope(claim.tenant_id)
        authority = await self._read_delivery(scope, claim.delivery_id)
        now = self._clock.utc_now()
        owner = _require_owner(authority.value, claim, now, allow_risk=False)
        value = authority.value
        if value.status is not DeliveryRecordStatus.QUEUED:
            raise NsRuntimeDeliveryStateError(details={
                "component": "delivery_scheduler", "operation": "start_sending",
                "reason": "queued_required",
            })
        if (
            value.policy_decision.config_version != policy.config_version
            or value.policy_decision.policy_version != policy.policy_version
            or value.activation is None
            or value.activation.config_version != policy.config_version
            or value.activation.policy_version != policy.policy_version
        ):
            raise NsRuntimeDeliveryStateError(details={
                "component": "delivery_scheduler", "operation": "start_sending",
                "reason": "policy_version_mismatch",
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
        root, shard = await self._read_bound_summaries(scope, value)
        next_root = _summary_delta(root.value, queued=-1, sending=1, now=now)
        next_shard = _summary_delta(shard.value, queued=-1, sending=1, now=now)
        mutations = (
            _replace_delivery(authority.record, sending),
            _create_attempt(scope.namespace, attempt),
            _replace_summary(root.record, next_root),
            _replace_summary(shard.record, next_shard),
        )
        result = await self._store.transact(StateTransaction(scope=scope, mutations=mutations))
        _validate_transaction(result, mutations, "start_sending")
        return SendingTransition(delivery=sending, attempt=attempt)

    async def complete_write_success(
        self,
        *,
        claim: DeliveryClaim,
    ) -> DeliveryRecord:
        return await self._complete_write(claim=claim, failure=None)

    async def complete_write_failure(
        self,
        *,
        claim: DeliveryClaim,
        failure: DeliveryWriteFailure,
    ) -> DeliveryRecord:
        if not isinstance(failure, DeliveryWriteFailure):
            _invalid("complete.failure")
        return await self._complete_write(claim=claim, failure=failure)

    async def load_claimed(self, *, claim: DeliveryClaim) -> DeliveryRecord:
        if not isinstance(claim, DeliveryClaim):
            _invalid("load.claim")
        authority = await self._read_delivery(_scope(claim.tenant_id), claim.delivery_id)
        _require_owner(authority.value, claim, self._clock.utc_now(), allow_risk=True)
        return authority.value

    async def _complete_write(
        self,
        *,
        claim: DeliveryClaim,
        failure: DeliveryWriteFailure | None,
    ) -> DeliveryRecord:
        if not isinstance(claim, DeliveryClaim):
            _invalid("complete.claim")
        scope = _scope(claim.tenant_id)
        authority = await self._read_delivery(scope, claim.delivery_id)
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
            or attempt.attempt_number != value.attempt_count
        ):
            raise NsRuntimeDeliveryStateError(details={
                "component": "delivery_scheduler", "operation": "complete_write",
                "reason": "attempt_mismatch",
            })
        root, shard = await self._read_bound_summaries(scope, value)
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
            next_root = _summary_delta(
                root.value, sending=-1, ack_waiting=1, now=now,
            )
            next_shard = _summary_delta(
                shard.value, sending=-1, ack_waiting=1, now=now,
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
            next_root = _summary_delta(
                root.value, sending=-1, write_failed=1, now=now,
            )
            next_shard = _summary_delta(
                shard.value, sending=-1, write_failed=1, now=now,
            )
        attempt_record = attempt_authority[1]
        mutations = (
            _replace_delivery(authority.record, updated),
            _replace_attempt(attempt_record, completed_attempt),
            _replace_summary(root.record, next_root),
            _replace_summary(shard.record, next_shard),
        )
        result = await self._store.transact(StateTransaction(scope=scope, mutations=mutations))
        _validate_transaction(result, mutations, "complete_write")
        return updated

    async def _scan_deliveries(
        self,
        scope: StateAccessScope,
    ) -> tuple[_DeliveryAuthority, ...]:
        records = await self._scan(scope, "delivery")
        return tuple(
            _DeliveryAuthority(value=_decode_delivery(record), record=record)
            for record in records
        )

    async def _scan_summaries(
        self,
        scope: StateAccessScope,
    ) -> tuple[_SummaryAuthority, ...]:
        records = await self._scan(scope, "summary")
        return tuple(
            _SummaryAuthority(value=_decode_summary(record), record=record)
            for record in records
        )

    async def _scan(
        self,
        scope: StateAccessScope,
        object_type: str,
    ) -> tuple[StateRecord, ...]:
        cursor = None
        values: list[StateRecord] = []
        while True:
            result = await self._store.scan(
                scope=scope,
                object_type=object_type,
                cursor=cursor,
                limit=1000,
            )
            values.extend(result.records)
            cursor = result.next_cursor
            if cursor is None:
                return tuple(values)

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

    async def _read_bound_summaries(
        self,
        scope: StateAccessScope,
        delivery: DeliveryRecord,
    ) -> tuple[_SummaryAuthority, _SummaryAuthority]:
        root_record = await _read_record(
            self._store, scope, "summary", delivery.root_summary_id,
        )
        shard_record = await _read_record(
            self._store, scope, "summary", delivery.summary_id,
        )
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


def _scope(tenant_id: str) -> StateAccessScope:
    namespace = StateNamespace.tenant(tenant_id=tenant_id, domain="delivery")
    return StateAccessScope(
        atomic_scope=StateAtomicScope(namespace=namespace, partition="scheduling"),
        authority=StateAuthorityKind.DELIVERY_ADMISSION,
        caller="delivery.scheduling",
        capabilities=frozenset({
            StateCallerCapability.READ,
            StateCallerCapability.SCAN,
            StateCallerCapability.COMPARE_AND_SET,
            StateCallerCapability.TRANSACT,
        }),
    )


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
) -> MessageDeliverySummary:
    return dataclasses.replace(
        value,
        prepared_count=value.prepared_count + prepared,
        queued_count=value.queued_count + queued,
        sending_count=value.sending_count + sending,
        ack_waiting_count=value.ack_waiting_count + ack_waiting,
        write_failed_count=value.write_failed_count + write_failed,
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


__all__ = ("StateStoreDeliveryScheduler",)
