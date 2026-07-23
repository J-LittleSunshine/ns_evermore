# -*- coding: utf-8 -*-
"""P10 admission orchestration. It creates prepared state and never sends."""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import timedelta
from typing import Callable

from ns_common.exceptions import (
    NsRuntimeIamTimeoutError, NsRuntimeIamUnavailableError,
    NsRuntimeStateStoreError, NsRuntimeStateStoreIndeterminateWriteError,
    NsValidationError,
)
from ns_common.iam import (
    IamTargetContext, PayloadRefValidationRequest, PayloadRefValidationResult,
)
from ns_common.time import Clock

from .models import (
    ADMISSION_RESPONSE_VERSION, DEDUP_EVIDENCE_VERSION,
    DR1_SCHEMA_VERSION, PAYLOAD_EVIDENCE_VERSION,
    AdmissionOutcome, AdmissionTrace, DedupEvidence, DeliveryRecord,
    DeliveryRecordStatus, DeliverySummaryStatus, DuplicateLifecycle,
    InlinePayload, MessageDeliverySummary, PayloadDependencyDisposition,
    PayloadEvidence, PayloadKind, PayloadReference, RejectionReason,
    TargetRejection, compute_binding_fingerprint,
    compute_dedup_evidence_fingerprint, compute_payload_evidence_fingerprint,
    compute_target_fingerprint, compute_envelope_authority_fingerprint,
    DeliveryEnvelopeAuthority,
)
from .policy import (
    AdmissionPolicy, AdmissionPolicyConfig, AdmissionRequest,
    validate_policy_decision,
)
from .response import (
    AdmissionCommitState, AdmissionResult, DeliveryAcceptedResponse, DeliveryDuplicateResponse,
    DeliveryRejectedResponse,
)
from .store import (
    AdmissionInitialization, AtomicAdmissionOutcome, AtomicAdmissionResult,
    DeliveryAdmissionStore,
)


class PayloadRefClient(ABC):
    @abstractmethod
    async def validate_payload_ref(
        self, request: "BoundPayloadRefValidationRequest",
    ) -> "BoundPayloadRefValidationResult":
        raise NotImplementedError


@dataclass(frozen=True, kw_only=True)
class BoundPayloadRefValidationRequest:
    iam_request: PayloadRefValidationRequest
    request_binding_fingerprint: str
    target_binding_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.iam_request, PayloadRefValidationRequest):
            _invalid("payload_ref_bound.request")
        if not _full_digest(self.request_binding_fingerprint):
            _invalid("payload_ref_bound.request_fingerprint")
        if not _full_digest(self.target_binding_fingerprint):
            _invalid("payload_ref_bound.target_fingerprint")

    def __getattr__(self, name: str):
        return getattr(self.iam_request, name)


@dataclass(frozen=True, slots=True, kw_only=True)
class BoundPayloadRefValidationResult:
    result: PayloadRefValidationResult
    request_binding_fingerprint: str
    target_binding_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.result, PayloadRefValidationResult):
            _invalid("payload_ref_bound.result")
        if not _full_digest(self.request_binding_fingerprint):
            _invalid("payload_ref_bound.result_request_fingerprint")
        if not _full_digest(self.target_binding_fingerprint):
            _invalid("payload_ref_bound.result_target_fingerprint")


class IamPayloadRefClient(PayloadRefClient):
    """Typed P10 adapter around the explicit P06 production IAM client."""

    def __init__(self, iam_client: object) -> None:
        from ns_runtime.iam import IamClient
        if not isinstance(iam_client, IamClient):
            _invalid("iam_payload_ref_client.iam_client")
        self._iam = iam_client

    async def validate_payload_ref(
        self, request: BoundPayloadRefValidationRequest,
    ) -> BoundPayloadRefValidationResult:
        if not isinstance(request, BoundPayloadRefValidationRequest):
            _invalid("iam_payload_ref_client.request")
        result = await self._iam.validate_payload_ref(request.iam_request)
        if not isinstance(result, PayloadRefValidationResult):
            _invalid("iam_payload_ref_client.result")
        return BoundPayloadRefValidationResult(
            result=result,
            request_binding_fingerprint=request.request_binding_fingerprint,
            target_binding_fingerprint=request.target_binding_fingerprint,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class AdmissionServiceLimits:
    """Compatibility view; authoritative values live in AdmissionPolicyConfig."""
    shard_bucket_size: int | None = None
    initialization_batch_size: int | None = None

    def __post_init__(self) -> None:
        if self.shard_bucket_size is not None:
            _invalid("limits.shard_bucket_size")
        if self.initialization_batch_size is not None:
            _invalid("limits.initialization_batch_size")


_CONTRACT_TEST_ADMISSION_AUTHORITY = object()


class DeliveryAdmissionService:
    def __init__(
        self, *, policy: AdmissionPolicy, policy_config: AdmissionPolicyConfig,
        store: DeliveryAdmissionStore, payload_ref_client: PayloadRefClient,
        clock: Clock, identifier_factory: Callable[[str, int], str],
        limits: AdmissionServiceLimits = AdmissionServiceLimits(),
        _authority: object | None = None,
    ) -> None:
        if not isinstance(policy, AdmissionPolicy):
            _invalid("service.policy")
        if not isinstance(policy_config, AdmissionPolicyConfig):
            _invalid("service.policy_config")
        if not isinstance(store, DeliveryAdmissionStore):
            _invalid("service.store")
        if not isinstance(payload_ref_client, PayloadRefClient):
            _invalid("service.payload_ref_client")
        if not isinstance(clock, Clock):
            _invalid("service.clock")
        if not callable(identifier_factory):
            _invalid("service.identifier_factory")
        if not isinstance(limits, AdmissionServiceLimits):
            _invalid("service.limits")
        self._policy = policy
        self._config = policy_config
        self._store = store
        self._payload_refs = payload_ref_client
        self._clock = clock
        self._ids = identifier_factory
        self._limits = limits
        self._accept_contract_test_authority = (
            _authority is _CONTRACT_TEST_ADMISSION_AUTHORITY
        )
        if _authority not in {None, _CONTRACT_TEST_ADMISSION_AUTHORITY}:
            _invalid("service.authority")

    @classmethod
    def for_contract_tests(cls, **values: object) -> "DeliveryAdmissionService":
        return cls(
            **values,  # type: ignore[arg-type]
            _authority=_CONTRACT_TEST_ADMISSION_AUTHORITY,
        )

    async def admit(
        self, request: AdmissionRequest, *, trace: AdmissionTrace,
    ) -> AdmissionResult:
        if not isinstance(request, AdmissionRequest):
            _invalid("admit.request")
        if not isinstance(trace, AdmissionTrace):
            _invalid("admit.trace")
        # Revalidate the RP-1 constructor graph by using its typed properties;
        # no dict/wire/JSON path and no Router dependency exists here.
        plan = request.plan
        evidence = plan.authorization_evidence
        if not (
            evidence.is_contract_test_authority()
            if self._accept_contract_test_authority
            else evidence.is_production_authority()
        ):
            _invalid("admit.authorization_authority")
        if compute_target_fingerprint(plan) != compute_target_fingerprint(request.plan):
            _invalid("admit.plan")
        now = self._clock.utc_now()
        inline_raw = (
            request.inline_descriptor.canonical_bytes
            if request.inline_descriptor is not None else None
        )
        decision = validate_policy_decision(
            self._policy.decide(request, now=now, config=self._config),
            request=request, config=self._config, now=now,
        )
        bindings = plan.selected_bindings
        accepted: list[tuple[int, object]] = []
        rejections: list[TargetRejection] = []
        payload_evidence: PayloadEvidence | None = None

        if not decision.accepted:
            reason = decision.rejection_reason or RejectionReason.POLICY_REJECTED
            rejections = [TargetRejection(
                target_fingerprint=compute_binding_fingerprint(binding), reason=reason,
            ) for binding in bindings]
        elif isinstance(request.payload, InlinePayload):
            descriptor = request.inline_descriptor
            if descriptor is None or descriptor.rejection_reason is not None:
                return await self._commit_all_rejected(
                    request=request, decision=decision, trace=trace, now=now,
                    reason=(
                        RejectionReason.INLINE_TYPE_INVALID if descriptor is None
                        else descriptor.rejection_reason
                    ),
                    payload_evidence=None,
                )
            if descriptor.observed_depth > decision.max_json_depth:
                return await self._commit_all_rejected(
                    request=request, decision=decision, trace=trace, now=now,
                    reason=RejectionReason.INLINE_TOO_DEEP,
                    payload_evidence=None,
                )
            raw = descriptor.canonical_bytes
            assert raw is not None
            limit = min(
                decision.max_inline_bytes,
                request.payload.application_limit_bytes,
                request.payload.transport_limit_bytes,
            )
            if len(raw) > limit:
                return await self._commit_all_rejected(
                    request=request, decision=decision, trace=trace, now=now,
                    reason=RejectionReason.INLINE_TOO_LARGE,
                    payload_evidence=None,
                )
            digest = descriptor.digest
            body_ref = self._id("payload_body", 0)
            request_binding = decision.request_fingerprint
            target_binding = compute_target_fingerprint(plan)
            payload_evidence = PayloadEvidence(
                schema_version=PAYLOAD_EVIDENCE_VERSION,
                kind=PayloadKind.INLINE, media_type=request.payload.media_type,
                size_bytes=len(raw), digest=digest, checksum=digest,
                body_ref=body_ref,
                request_binding_fingerprint=request_binding,
                target_binding_fingerprint=target_binding,
                evidence_fingerprint=compute_payload_evidence_fingerprint(
                    kind=PayloadKind.INLINE,
                    media_type=request.payload.media_type, size_bytes=len(raw),
                    digest=digest, checksum=digest,
                    body_ref=body_ref,
                    request_binding_fingerprint=request_binding,
                    target_binding_fingerprint=target_binding,
                ),
            )
            accepted = list(enumerate(bindings))
        else:
            ref_result = await self._validate_payload_reference(
                request=request, decision=decision, trace=trace,
            )
            if isinstance(ref_result, AdmissionResult):
                return ref_result
            accepted, rejections, payload_evidence = ref_result

        return await self._commit(
            request=request, decision=decision, trace=trace, now=now,
            accepted=accepted, rejections=rejections,
            payload_evidence=payload_evidence,
            payload_body=inline_raw,
        )

    async def _validate_payload_reference(self, *, request, decision, trace):
        payload = request.payload
        assert isinstance(payload, PayloadReference)
        accepted: list[tuple[int, object]] = []
        rejections: list[TargetRejection] = []
        valid_results: list[PayloadRefValidationResult] = []
        for index, binding in enumerate(request.plan.selected_bindings):
            iam_contract = PayloadRefValidationRequest(
                object_id=payload.object_id, version=payload.version,
                checksum=payload.checksum, tenant_id=request.tenant_id,
                owner_identity=payload.owner_identity,
                source_identity=request.source_identity,
                target=IamTargetContext(
                    kind="connection", tenant_id=binding.tenant_id,
                    reference=binding.connection_id,
                ),
                callback_message_type=payload.callback_message_type,
            )
            fingerprint = compute_binding_fingerprint(binding)
            contract = BoundPayloadRefValidationRequest(
                iam_request=iam_contract,
                request_binding_fingerprint=decision.request_fingerprint,
                target_binding_fingerprint=fingerprint,
            )
            try:
                result = await self._payload_refs.validate_payload_ref(contract)
            except (NsRuntimeIamTimeoutError, NsRuntimeIamUnavailableError, TimeoutError):
                return self._dependency_result(
                    request=request, decision=decision,
                    now=self._clock.utc_now(), reason=RejectionReason.PAYLOAD_REF_UNAVAILABLE,
                    trace=trace,
                )
            except Exception:
                return self._dependency_result(
                    request=request, decision=decision,
                    now=self._clock.utc_now(), reason=RejectionReason.PAYLOAD_REF_UNAVAILABLE,
                    trace=trace,
                )
            if not isinstance(result, BoundPayloadRefValidationResult):
                _invalid("payload_ref.result")
            if (result.request_binding_fingerprint != decision.request_fingerprint
                    or result.target_binding_fingerprint != fingerprint):
                _invalid("payload_ref.result_binding")
            result = result.result
            if result.valid:
                if (result.object_id != payload.object_id
                        or result.version != payload.version
                        or result.checksum != payload.checksum
                        or result.size_bytes is None):
                    _invalid("payload_ref.result_authority")
                if result.tenant_id != request.tenant_id:
                    rejections.append(TargetRejection(
                        target_fingerprint=fingerprint,
                        reason=RejectionReason.PAYLOAD_REF_TENANT_MISMATCH,
                    ))
                    continue
                if (result.expires_at <= self._clock.utc_now()
                        or result.expires_at < decision.expires_at):
                    rejections.append(TargetRejection(
                        target_fingerprint=fingerprint,
                        reason=RejectionReason.PAYLOAD_REF_INVALID,
                    ))
                    continue
                accepted.append((index, binding))
                valid_results.append(result)
            else:
                reason = _payload_ref_reason(result.reason, result.revoked)
                rejections.append(TargetRejection(
                    target_fingerprint=fingerprint, reason=reason,
                ))
        evidence = None
        if valid_results:
            first = valid_results[0]
            if any((item.object_id, item.version, item.checksum, item.tenant_id,
                    item.size_bytes) != (first.object_id, first.version,
                    first.checksum, first.tenant_id, first.size_bytes)
                   for item in valid_results):
                _invalid("payload_ref.inconsistent_integrity")
            digest = payload.checksum if _full_digest(payload.checksum) else (
                "sha256:" + hashlib.sha256(
                    f"{payload.object_id}\0{payload.version}\0{payload.checksum}".encode()
                ).hexdigest()
            )
            validated_at = self._clock.utc_now()
            expires_at = min(item.expires_at for item in valid_results)
            evidence = PayloadEvidence(
                schema_version=PAYLOAD_EVIDENCE_VERSION,
                kind=PayloadKind.REFERENCE,
                media_type="application/octet-stream",
                size_bytes=first.size_bytes or 0, digest=digest,
                checksum=payload.checksum, object_id=payload.object_id,
                object_version=payload.version, tenant_id=request.tenant_id,
                validated_at=validated_at, expires_at=expires_at,
                request_binding_fingerprint=decision.request_fingerprint,
                target_binding_fingerprint=compute_target_fingerprint(request.plan),
                evidence_fingerprint=compute_payload_evidence_fingerprint(
                    kind=PayloadKind.REFERENCE,
                    media_type="application/octet-stream",
                    size_bytes=first.size_bytes or 0, digest=digest,
                    checksum=payload.checksum, object_id=payload.object_id,
                    object_version=payload.version,
                    tenant_id=request.tenant_id,
                    validated_at=validated_at, expires_at=expires_at,
                    request_binding_fingerprint=decision.request_fingerprint,
                    target_binding_fingerprint=compute_target_fingerprint(request.plan),
                ),
            )
        return accepted, rejections, evidence

    def _dependency_result(self, *, request, decision, now, reason, trace):
        disposition = decision.payload_dependency_disposition
        outcome = {
            PayloadDependencyDisposition.REJECT: AdmissionOutcome.REJECTED,
            PayloadDependencyDisposition.WAIT_REQUIRED: AdmissionOutcome.WAIT_REQUIRED,
            PayloadDependencyDisposition.DEAD_LETTER_REQUIRED: AdmissionOutcome.DEAD_LETTER_REQUIRED,
            PayloadDependencyDisposition.DEPENDENCY_UNAVAILABLE: AdmissionOutcome.UNAVAILABLE,
        }[disposition]
        return AdmissionResult(
            outcome=outcome, commit_state=AdmissionCommitState.NOT_COMMITTED,
            response=DeliveryRejectedResponse(
                schema_version=ADMISSION_RESPONSE_VERSION,
                message_id=request.message_id, summary_id=None,
                rejected_at=now, reason=reason, disposition=disposition,
                trace=trace,
            ),
        )

    async def _commit_all_rejected(
        self, *, request, decision, trace, now, reason, payload_evidence,
    ) -> AdmissionResult:
        return await self._commit(
            request=request, decision=decision, trace=trace, now=now,
            accepted=[], rejections=[TargetRejection(
                target_fingerprint=compute_binding_fingerprint(binding),
                reason=reason,
            ) for binding in request.plan.selected_bindings],
            payload_evidence=payload_evidence,
        )

    async def _commit(
        self, *, request, decision, trace, now,
        accepted, rejections, payload_evidence, payload_body=None,
    ) -> AdmissionResult:
        initialization = self._build_initialization(
            request=request, decision=decision, now=now,
            accepted=accepted, rejections=rejections,
            payload_evidence=payload_evidence,
            payload_body=(payload_body if payload_evidence is not None
                          and payload_evidence.body_ref is not None else None),
            trace=trace,
        )
        try:
            result = await self._store.initialize(initialization)
        except NsRuntimeStateStoreIndeterminateWriteError:
            commit_state = AdmissionCommitState.INDETERMINATE
        except NsRuntimeStateStoreError:
            commit_state = AdmissionCommitState.NOT_COMMITTED
        else:
            commit_state = None
        if commit_state is not None:
            return AdmissionResult(
                outcome=AdmissionOutcome.UNAVAILABLE, commit_state=commit_state,
                response=DeliveryRejectedResponse(
                    schema_version=ADMISSION_RESPONSE_VERSION,
                    message_id=request.message_id, summary_id=None,
                    rejected_at=self._clock.utc_now(),
                    reason=RejectionReason.INITIALIZATION_FAILED,
                    disposition=PayloadDependencyDisposition.DEPENDENCY_UNAVAILABLE, trace=trace,
                ),
            )
        if not isinstance(result, AtomicAdmissionResult):
            _invalid("store.result")
        if (result.dedup.tenant_id != initialization.dedup.tenant_id
                or result.dedup.message_id != initialization.dedup.message_id
                or result.dedup.target_fingerprint != initialization.dedup.target_fingerprint):
            _invalid("store.result_authority")
        if result.outcome is AtomicAdmissionOutcome.DUPLICATE:
            return AdmissionResult(
                outcome=AdmissionOutcome.DUPLICATE,
                commit_state=AdmissionCommitState.COMMITTED,
                response=DeliveryDuplicateResponse(
                    schema_version=ADMISSION_RESPONSE_VERSION,
                    message_id=request.message_id, summary_id=result.dedup.summary_id,
                    observed_at=self._clock.utc_now(), lifecycle=result.dedup.lifecycle,
                    status_query_hint=f"delivery.summary:{result.dedup.summary_id}",
                    trace=trace,
                ),
            )
        if result.outcome is AtomicAdmissionOutcome.CANCELLED_INITIALIZATION:
            if (result.root_summary is None
                    or result.root_summary.status
                    is not DeliverySummaryStatus.CANCELLED
                    or result.dedup.lifecycle is not DuplicateLifecycle.CANCELLED):
                _invalid("store.cancelled_initialization")
            return AdmissionResult(
                outcome=AdmissionOutcome.REJECTED,
                commit_state=AdmissionCommitState.COMMITTED,
                response=DeliveryRejectedResponse(
                    schema_version=ADMISSION_RESPONSE_VERSION,
                    message_id=request.message_id,
                    summary_id=result.root_summary.summary_id,
                    rejected_at=self._clock.utc_now(),
                    reason=RejectionReason.INITIALIZATION_FAILED,
                    disposition=PayloadDependencyDisposition.REJECT,
                    trace=trace,
                ),
            )
        if (result.root_summary != initialization.root_summary
                or result.dedup != initialization.dedup):
            _invalid("store.created_evidence")
        root = initialization.root_summary
        if root.status is DeliverySummaryStatus.FAILED:
            reason = (root.rejection_evidence[0].reason
                      if root.rejection_evidence else RejectionReason.NO_TARGET_ACCEPTED)
            return AdmissionResult(
                outcome=AdmissionOutcome.REJECTED,
                commit_state=AdmissionCommitState.COMMITTED,
                response=DeliveryRejectedResponse(
                    schema_version=ADMISSION_RESPONSE_VERSION,
                    message_id=request.message_id, summary_id=root.summary_id,
                    rejected_at=now, reason=reason,
                    disposition=PayloadDependencyDisposition.REJECT, trace=trace,
                ),
            )
        return AdmissionResult(
            outcome=AdmissionOutcome.ACCEPTED,
            commit_state=AdmissionCommitState.COMMITTED,
            response=DeliveryAcceptedResponse(
                schema_version=ADMISSION_RESPONSE_VERSION,
                message_id=request.message_id, summary_id=root.summary_id,
                accepted_at=now,
                status_query_hint=f"delivery.summary:{root.summary_id}",
                trace=trace,
            ),
        )

    def _build_initialization(
        self, *, request, decision, now, accepted, rejections, payload_evidence,
        payload_body=None, trace,
    ) -> AdmissionInitialization:
        plan = request.plan
        total = len(plan.selected_bindings)
        accepted_count = len(accepted)
        rejected_count = len(rejections)
        if accepted_count + rejected_count != total:
            _invalid("initialization.target_partition")
        if accepted_count and payload_evidence is None:
            _invalid("initialization.payload_evidence")
        summary_id = self._id("summary", 0)
        target_fingerprint = compute_target_fingerprint(plan)
        authority_bucket_id = int.from_bytes(
            hashlib.sha256(request.message_id.encode("utf-8")).digest()[:8], "big",
        ) % decision.authority_bucket_count
        status = _summary_status(total, accepted_count, rejected_count)
        threshold = decision.fanout_shard_threshold
        bucket_size = decision.shard_bucket_size
        shard_count = 0 if total <= threshold else (
            total + bucket_size - 1
        ) // bucket_size
        final_state_version = (
            1 if accepted_count == 0
            else ((accepted_count + decision.initialization_batch_size - 1)
                  // decision.initialization_batch_size) + 1
        )
        common = dict(
            schema_version=DR1_SCHEMA_VERSION, root_summary_id=summary_id,
            shard_count=shard_count, message_id=request.message_id,
            tenant_id=request.tenant_id, plan_id=plan.plan_id,
            plan_version=plan.plan_version,
            plan_decision_fingerprint=plan.decision_fingerprint,
            target_fingerprint=target_fingerprint,
            authority_bucket_count=decision.authority_bucket_count,
            authority_bucket_id=authority_bucket_id,
            authority_layout_version=decision.authority_layout_version,
            authority_layout_generation=decision.authority_layout_generation,
            payload_evidence=payload_evidence, policy_decision=decision,
            state_version=final_state_version, created_at=now, updated_at=now,
            active_count=0, inflight_count=0, cancelled_count=0,
            not_initialized_count=0,
        )
        root = MessageDeliverySummary(
            summary_id=summary_id, shard_index=None, status=status,
            total_count=total, accepted_count=accepted_count,
            rejected_count=rejected_count, prepared_count=accepted_count,
            rejection_evidence=tuple(rejections), **common,
        )
        accepted_by_index = {index: binding for index, binding in accepted}
        rejection_by_fingerprint = {item.target_fingerprint: item for item in rejections}
        shards = []
        deliveries = []
        for shard_index in range(shard_count):
            start = shard_index * bucket_size
            end = min(total, start + bucket_size)
            shard_bindings = plan.selected_bindings[start:end]
            shard_accepted = sum(index in accepted_by_index for index in range(start, end))
            shard_rejections = tuple(
                rejection_by_fingerprint[compute_binding_fingerprint(binding)]
                for binding in shard_bindings
                if compute_binding_fingerprint(binding) in rejection_by_fingerprint
            )
            shards.append(MessageDeliverySummary(
                summary_id=self._id("shard", shard_index),
                shard_index=shard_index,
                status=_summary_status(len(shard_bindings), shard_accepted,
                                       len(shard_rejections)),
                total_count=len(shard_bindings), accepted_count=shard_accepted,
                rejected_count=len(shard_rejections),
                prepared_count=shard_accepted,
                rejection_evidence=shard_rejections, **common,
            ))
        shard_ids = {value.shard_index: value.summary_id for value in shards}
        for index, binding in accepted:
            shard_index = None if shard_count == 0 else index // bucket_size
            deliveries.append(DeliveryRecord(
                schema_version=DR1_SCHEMA_VERSION,
                delivery_id=self._id("delivery", index),
                summary_id=(summary_id if shard_index is None else shard_ids[shard_index]), root_summary_id=summary_id,
                shard_index=shard_index, message_id=request.message_id,
                tenant_id=request.tenant_id, plan_id=plan.plan_id,
                plan_version=plan.plan_version,
                plan_decision_fingerprint=plan.decision_fingerprint,
                target_fingerprint=compute_binding_fingerprint(binding),
                target_set_fingerprint=target_fingerprint,
                target_index=index, binding=binding,
                authority_bucket_count=decision.authority_bucket_count,
                authority_bucket_id=authority_bucket_id,
                authority_layout_version=decision.authority_layout_version,
                authority_layout_generation=decision.authority_layout_generation,
                status=DeliveryRecordStatus.PREPARED,
                payload_evidence=payload_evidence, policy_decision=decision,
                envelope_authority=request.envelope_authority,
                envelope_authority_fingerprint=compute_envelope_authority_fingerprint(
                    request.envelope_authority
                ),
                state_version=1, created_at=now, updated_at=now,
            ))
        dedup_expires = now + timedelta(seconds=decision.dedup_ttl_seconds)
        dedup_values = dict(
            tenant_id=request.tenant_id, message_id=request.message_id,
            target_fingerprint=target_fingerprint, summary_id=summary_id,
            lifecycle=DuplicateLifecycle.IN_PROGRESS,
            registered_at=now, expires_at=dedup_expires,
        )
        dedup = DedupEvidence(
            schema_version=DEDUP_EVIDENCE_VERSION,
            evidence_fingerprint=compute_dedup_evidence_fingerprint(**dedup_values),
            **dedup_values,
        )
        return AdmissionInitialization(
            plan=plan, root_summary=root, shard_summaries=tuple(shards),
            deliveries=tuple(deliveries), dedup=dedup,
            initialization_batch_size=decision.initialization_batch_size,
            payload_body_ref=(payload_evidence.body_ref if payload_evidence is not None else None),
            payload_body=payload_body,
        )

    def _id(self, kind: str, index: int) -> str:
        value = self._ids(kind, index)
        if not isinstance(value, str) or not value:
            _invalid("identifier_factory.result")
        return value


def _summary_status(total, accepted, rejected):
    if accepted == 0:
        return DeliverySummaryStatus.FAILED
    return DeliverySummaryStatus.PENDING


def _payload_ref_reason(reason: str, revoked: bool) -> RejectionReason:
    normalized = reason.lower() if isinstance(reason, str) else ""
    if "tenant" in normalized:
        return RejectionReason.PAYLOAD_REF_TENANT_MISMATCH
    if revoked or "unauthor" in normalized or "permission" in normalized:
        return RejectionReason.PAYLOAD_REF_UNAUTHORIZED
    return RejectionReason.PAYLOAD_REF_INVALID


def _full_digest(value: str) -> bool:
    import re
    return re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None


def _invalid(field: str) -> None:
    raise NsValidationError(
        "P10 delivery admission value is invalid.",
        details={"component": "delivery_admission", "field": field},
    )


__all__ = (
    "AdmissionServiceLimits", "BoundPayloadRefValidationRequest",
    "BoundPayloadRefValidationResult", "DeliveryAdmissionService", "IamPayloadRefClient",
    "PayloadRefClient",
)
