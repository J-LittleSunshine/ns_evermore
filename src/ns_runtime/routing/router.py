# -*- coding: utf-8 -*-
"""Deterministic local Router over exactly one P05 index snapshot."""

from __future__ import annotations

import asyncio
import hashlib
import json
from dataclasses import replace

from ns_common.config import NsRuntimeRoutingConfig
from ns_common.exceptions import NsValidationError
from ns_common.identifiers import IdentifierFactory, NsIdentifierKind
from ns_common.time import Clock
from ns_runtime.connection.index import (
    ConnectionRoutingEligibility,
    LocalConnectionIndex,
)
from ns_runtime.connection.state import (
    LogicalConnectionState,
)

from .authority import (
    LocalRoutingConsistencyPolicy,
    NoopRoutingPlanRecorder,
    RoutingConsistencyPolicy,
    RoutingConsistencyRequirement,
    RoutingPlanRecorder,
    StrongRoutingPlanAuthority,
    UnavailableStrongRoutingPlanAuthority,
)
from .models import (
    CandidateEvidence,
    CandidateFilterReason,
    LaterActionSuggestion,
    PreviousRoutingPlanContext,
    RebindPolicy,
    ResolvedRoutingPlan,
    ResolutionHint,
    RoutingDecision,
    RoutingFailureReason,
    RoutingFailureReport,
    RoutingIdentityReference,
    RoutingRequest,
    RoutingStrategy,
    SelectedRoutingBinding,
    StrategyParameters,
)


RP1_SCHEMA_VERSION = "rp-1"
FALLBACK_SCORER_SOURCE = "runtime_fallback"
FALLBACK_SCORER_VERSION = "fallback.v1"


class LocalRouter:
    """P09 decision owner; it has no transport, Delivery, or StateStore slot."""

    def __init__(
        self,
        *,
        connection_index: LocalConnectionIndex,
        clock: Clock,
        identifier_factory: IdentifierFactory,
        runtime_id: str,
        config: NsRuntimeRoutingConfig,
        consistency_policy: RoutingConsistencyPolicy | None = None,
        plan_recorder: RoutingPlanRecorder | None = None,
        strong_authority: StrongRoutingPlanAuthority | None = None,
    ) -> None:
        if not isinstance(connection_index, LocalConnectionIndex):
            _invalid("connection_index")
        if not isinstance(clock, Clock):
            _invalid("clock")
        if not isinstance(identifier_factory, IdentifierFactory):
            _invalid("identifier_factory")
        if not isinstance(runtime_id, str) or not runtime_id:
            _invalid("runtime_id")
        if not isinstance(config, NsRuntimeRoutingConfig):
            _invalid("config")
        for name in (
            "max_candidate_count",
            "max_selected_target_count",
            "max_plan_evidence_count",
        ):
            value = getattr(config, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                _invalid(f"config.{name}")
        self._index = connection_index
        self._clock = clock
        self._ids = identifier_factory
        self._runtime_id = runtime_id
        self._config = config
        self._consistency = consistency_policy or LocalRoutingConsistencyPolicy()
        self._recorder = plan_recorder or NoopRoutingPlanRecorder()
        self._strong = strong_authority or UnavailableStrongRoutingPlanAuthority()
        if not isinstance(self._consistency, RoutingConsistencyPolicy):
            _invalid("consistency_policy")
        if not isinstance(self._recorder, RoutingPlanRecorder):
            _invalid("plan_recorder")
        if not isinstance(self._strong, StrongRoutingPlanAuthority):
            _invalid("strong_authority")

    async def route(
        self,
        request: RoutingRequest,
        *,
        previous: PreviousRoutingPlanContext | None = None,
    ) -> RoutingDecision:
        if not isinstance(request, RoutingRequest):
            _invalid("request")
        if previous is not None and not isinstance(
            previous,
            PreviousRoutingPlanContext,
        ):
            _invalid("previous")

        target_tenant = request.target.tenant_id
        if (
            target_tenant is not None
            and target_tenant != request.effective_tenant_id
            and not request.cross_tenant_authorized
        ):
            return self._failure(request, RoutingFailureReason.TENANT_DENIED)

        try:
            # RP-1 requires one and only one index read for a decision.
            snapshot = await self._index.snapshot()
        except asyncio.CancelledError:
            raise
        except Exception:
            return self._failure(request, RoutingFailureReason.INDEX_UNAVAILABLE)

        target = request.target
        if target.kind == "runtime" and target.runtime_id != self._runtime_id:
            return self._failure(
                request,
                RoutingFailureReason.REMOTE_RUNTIME,
                sequence=snapshot.mutation_sequence,
            )

        intended = self._expand_primary(request, snapshot)
        if intended is None:
            return self._failure(
                request,
                RoutingFailureReason.TARGET_NOT_FOUND,
                sequence=snapshot.mutation_sequence,
            )
        if len(intended) > self._config.max_candidate_count:
            return self._failure(
                request,
                RoutingFailureReason.LIMIT_EXCEEDED,
                sequence=snapshot.mutation_sequence,
            )

        evidence: list[CandidateEvidence] = []
        eligible: list[CandidateEvidence] = []
        for connection_id in sorted(intended):
            entry = snapshot.by_connection_id.get(connection_id)
            if entry is None:
                continue
            context = entry.session_context
            reason = self._filter_reason(
                request,
                entry=entry,
                previous=previous,
            )
            candidate = CandidateEvidence(
                connection_id=context.connection_id,
                session_id=context.session_id,
                connection_epoch=context.connection_epoch,
                identity_reference=RoutingIdentityReference(value=context.identity),
                tenant_id=context.tenant_id,
                component_type=context.component_type,
                capabilities=context.capabilities,
                filter_reason=reason or CandidateFilterReason.ELIGIBLE,
            )
            evidence.append(candidate)
            if reason is None:
                score = self._score(request, candidate)
                eligible.append(replace(candidate, score=score))

        filtered = tuple(
            candidate
            for candidate in evidence
            if candidate.filter_reason is not CandidateFilterReason.ELIGIBLE
        )
        if len(evidence) + len(filtered) > self._config.max_plan_evidence_count:
            return self._failure(
                request,
                RoutingFailureReason.LIMIT_EXCEEDED,
                sequence=snapshot.mutation_sequence,
            )
        if (
            request.effective_strategy is RoutingStrategy.ALL_REQUIRED
            and filtered
        ):
            return self._failure(
                request,
                self._failure_reason_from_filtered(filtered),
                sequence=snapshot.mutation_sequence,
            )
        if not eligible:
            if target.kind == "connection" and evidence and all(
                item.filter_reason is CandidateFilterReason.TENANT_MISMATCH
                for item in evidence
            ):
                reason = RoutingFailureReason.TENANT_DENIED
            else:
                reason = self._failure_reason_from_filtered(filtered)
            return self._failure(
                request,
                reason,
                sequence=snapshot.mutation_sequence,
            )

        eligible.sort(key=lambda value: value.score or ())
        selected_evidence = self._select(request, eligible)
        if selected_evidence is None:
            return self._failure(
                request,
                RoutingFailureReason.NO_CANDIDATE,
                sequence=snapshot.mutation_sequence,
            )
        if len(selected_evidence) > self._config.max_selected_target_count:
            return self._failure(
                request,
                RoutingFailureReason.LIMIT_EXCEEDED,
                sequence=snapshot.mutation_sequence,
            )
        selected_ids = {candidate.connection_id for candidate in selected_evidence}
        scored_by_connection = {
            candidate.connection_id: candidate
            for candidate in eligible
        }
        final_evidence = tuple(
            replace(
                scored_by_connection.get(candidate.connection_id, candidate),
                filter_reason=(
                    CandidateFilterReason.SELECTED
                    if candidate.connection_id in selected_ids
                    else candidate.filter_reason
                ),
            )
            for candidate in evidence
        )
        bindings = tuple(
            SelectedRoutingBinding(
                runtime_id=self._runtime_id,
                connection_id=candidate.connection_id,
                session_id=candidate.session_id,
                connection_epoch=candidate.connection_epoch,
                tenant_id=candidate.tenant_id,
                identity_reference=candidate.identity_reference,
                required_capabilities=frozenset(target.capabilities or ()),
                component_type=candidate.component_type,
            )
            for candidate in selected_evidence
        )
        fingerprint = self._fingerprint(
            request,
            sequence=snapshot.mutation_sequence,
            evidence=final_evidence,
            selected=bindings,
            previous=previous,
        )
        plan = ResolvedRoutingPlan(
            schema_version=RP1_SCHEMA_VERSION,
            plan_id=self._ids.generate(NsIdentifierKind.PLAN_ID),
            plan_version=1 if previous is None else previous.plan_version + 1,
            previous_plan_id=None if previous is None else previous.plan_id,
            message_reference=request.message_reference,
            decision_fingerprint=fingerprint,
            original_target=target,
            candidates=final_evidence,
            filtered_evidence=filtered,
            selected_bindings=bindings,
            strategy=request.effective_strategy,
            strategy_parameters=StrategyParameters(
                fanout_count=target.fanout_count,
                required_count=target.required_count,
                subset_size=target.subset_size,
            ),
            effective_rebind_policy=request.effective_rebind_policy,
            requested_policy_evidence=(
                target.rebind_policy or "default"
            ),
            effective_policy_evidence=request.effective_rebind_policy.value,
            config_version=request.config_version,
            policy_version=request.policy_version,
            scorer_source=FALLBACK_SCORER_SOURCE,
            scorer_version=FALLBACK_SCORER_VERSION,
            iam_decision_reference=request.iam_decision_reference,
            iam_decision_version=request.iam_decision_version,
            index_mutation_sequence=snapshot.mutation_sequence,
            local_hit=True,
            used_stale_route=False,
            created_at=self._clock.utc_now(),
        )

        requirement = self._consistency.requirement_for(request)
        if requirement is RoutingConsistencyRequirement.STRONG_REQUIRED:
            try:
                await self._strong.commit(plan)
            except asyncio.CancelledError:
                raise
            except Exception:
                return self._failure(
                    request,
                    RoutingFailureReason.AUTHORITY_UNAVAILABLE,
                    sequence=snapshot.mutation_sequence,
                    strong=True,
                )
        try:
            await self._recorder.record(plan.safe_projection())
        except asyncio.CancelledError:
            raise
        except Exception:
            # The ordinary recorder owns diagnostic retention only; the plan
            # remains the authoritative return value for this local decision.
            pass
        return plan

    def _expand_primary(self, request, snapshot) -> frozenset[str] | None:
        target = request.target
        if target.kind == "connection":
            assert target.connection_id is not None
            if target.connection_id not in snapshot.by_connection_id:
                return None
            return frozenset({target.connection_id})
        if target.kind == "identity":
            assert target.identity is not None
            return snapshot.by_identity.get(target.identity, frozenset())
        if target.kind == "tenant":
            assert target.tenant_id is not None
            return snapshot.by_tenant.get(target.tenant_id, frozenset())
        if target.kind == "capability":
            capabilities = tuple(target.capabilities or ())
            if not capabilities:
                return frozenset()
            sets = [snapshot.by_capability.get(value, frozenset()) for value in capabilities]
            return frozenset.intersection(*sets) if sets else frozenset()
        if target.kind == "component_type":
            assert target.component_type is not None
            return snapshot.by_component_type.get(target.component_type, frozenset())
        if target.kind == "runtime":
            return frozenset(snapshot.by_connection_id)
        if target.kind == "broadcast":
            assert target.tenant_id is not None
            return snapshot.by_tenant.get(target.tenant_id, frozenset())
        return frozenset()

    def _filter_reason(self, request, *, entry, previous):
        target = request.target
        context = entry.session_context
        if context.tenant_id != request.effective_tenant_id and not request.cross_tenant_authorized:
            return CandidateFilterReason.TENANT_MISMATCH
        if target.tenant_id is not None and context.tenant_id != target.tenant_id:
            return CandidateFilterReason.TENANT_MISMATCH
        if target.component_type is not None and context.component_type != target.component_type:
            return CandidateFilterReason.COMPONENT_MISMATCH
        required = frozenset(target.capabilities or ())
        if not required.issubset(context.capabilities):
            return CandidateFilterReason.CAPABILITY_MISMATCH
        if previous is not None and not self._rebind_allowed(request, context, previous):
            return CandidateFilterReason.REBIND_FORBIDDEN
        if entry.state is LogicalConnectionState.DRAINING:
            return CandidateFilterReason.DRAINING
        if entry.state is not LogicalConnectionState.ACTIVE:
            return CandidateFilterReason.NOT_ACTIVE
        eligibility = entry.routing_eligibility
        if eligibility is ConnectionRoutingEligibility.RECONNECT_GRACE:
            return CandidateFilterReason.RECONNECT_GRACE
        if eligibility is ConnectionRoutingEligibility.AUTHORITY_SUSPENDED:
            return CandidateFilterReason.AUTHORITY_SUSPENDED
        if eligibility is ConnectionRoutingEligibility.SESSION_EXPIRY_SUSPENDED:
            return CandidateFilterReason.SESSION_EXPIRY_SUSPENDED
        if eligibility is not ConnectionRoutingEligibility.ELIGIBLE or not entry.active_target_eligible:
            return CandidateFilterReason.NOT_ELIGIBLE
        if (
            target.connection_epoch is not None
            and target.connection_epoch != context.connection_epoch
        ):
            return CandidateFilterReason.EPOCH_STALE
        return None

    def _rebind_allowed(self, request, context, previous) -> bool:
        policy = request.effective_rebind_policy
        old = previous.selected_bindings
        if policy in {
            RebindPolicy.FIXED_CONNECTION,
            RebindPolicy.NO_REBIND_FOR_CONTROL,
        }:
            return any(
                item.connection_id == context.connection_id
                and item.session_id == context.session_id
                and item.connection_epoch == context.connection_epoch
                for item in old
            )
        if policy is RebindPolicy.SAME_IDENTITY:
            return any(
                item.identity_reference.value == context.identity for item in old
            )
        if policy is RebindPolicy.SAME_CAPABILITY:
            return all(
                item.required_capabilities.issubset(context.capabilities)
                for item in old
            )
        if policy is RebindPolicy.SAME_TENANT:
            return any(item.tenant_id == context.tenant_id for item in old)
        return False

    def _score(self, request, candidate):
        target = request.target
        exactness = 0 if target.kind == "connection" else 1
        affinity = 0 if candidate.connection_id in request.trusted_affinity_connection_ids else 1
        weights = dict(request.runtime_policy_static_weights)
        static_weight = -weights.get(candidate.connection_id, 0)
        required = frozenset(target.capabilities or ())
        capability_surplus = len(candidate.capabilities - required)
        tie_break = "|".join((
            self._runtime_id,
            candidate.tenant_id,
            candidate.component_type,
            candidate.identity_reference.value,
            candidate.connection_id,
            candidate.session_id,
            str(candidate.connection_epoch),
        ))
        return (exactness, affinity, static_weight, capability_surplus, tie_break)

    def _select(self, request, eligible):
        strategy = request.effective_strategy
        target = request.target
        if strategy is RoutingStrategy.SINGLE:
            return tuple(eligible[:1])
        if strategy in {
            RoutingStrategy.ALL,
            RoutingStrategy.BROADCAST,
            RoutingStrategy.ALL_REQUIRED,
        }:
            return tuple(eligible)
        if strategy is RoutingStrategy.QUORUM:
            assert target.fanout_count is not None
            if len(eligible) < target.fanout_count:
                return None
            return tuple(eligible[:target.fanout_count])
        if strategy is RoutingStrategy.WEIGHTED_SUBSET:
            assert target.subset_size is not None
            if len(eligible) < target.subset_size:
                return None
            return tuple(eligible[:target.subset_size])
        return None

    def _fingerprint(self, request, *, sequence, evidence, selected, previous):
        target = request.target
        payload = {
            "target": {
                name: getattr(target, name)
                for name in (
                    "kind", "connection_id", "connection_epoch", "identity",
                    "tenant_id", "capabilities", "component_type", "runtime_id",
                    "scope", "multi_connection_policy", "rebind_policy",
                    "fanout_count", "required_count", "subset_size",
                )
            },
            "effective_tenant": request.effective_tenant_id,
            "strategy": request.effective_strategy.value,
            "rebind": request.effective_rebind_policy.value,
            "config_version": request.config_version,
            "policy_version": request.policy_version,
            "iam_version": request.iam_decision_version,
            "index_sequence": sequence,
            "scorer": [FALLBACK_SCORER_SOURCE, FALLBACK_SCORER_VERSION],
            "previous": None if previous is None else [previous.plan_id, previous.plan_version],
            "evidence": [
                [
                    item.connection_id, item.session_id, item.connection_epoch,
                    item.tenant_id, item.identity_reference.value,
                    item.component_type, sorted(item.capabilities),
                    item.filter_reason.value, item.score,
                ]
                for item in evidence
            ],
            "selected": [
                [item.connection_id, item.session_id, item.connection_epoch]
                for item in selected
            ],
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def _failure_reason_from_filtered(self, filtered):
        reasons = {value.filter_reason for value in filtered}
        if CandidateFilterReason.DRAINING in reasons:
            return RoutingFailureReason.DRAINING
        if CandidateFilterReason.RECONNECT_GRACE in reasons:
            return RoutingFailureReason.RECONNECT_GRACE
        if CandidateFilterReason.AUTHORITY_SUSPENDED in reasons:
            return RoutingFailureReason.AUTHORITY_SUSPENDED
        if CandidateFilterReason.SESSION_EXPIRY_SUSPENDED in reasons:
            return RoutingFailureReason.SESSION_EXPIRY_SUSPENDED
        if CandidateFilterReason.EPOCH_STALE in reasons:
            return RoutingFailureReason.EPOCH_STALE
        return RoutingFailureReason.NO_CANDIDATE

    def _failure(self, request, reason, *, sequence=None, strong=False):
        if reason is RoutingFailureReason.POLICY_REJECTED:
            action = LaterActionSuggestion.SUBMIT_CORRECTED_TARGET
        elif reason in {
            RoutingFailureReason.TARGET_NOT_FOUND,
            RoutingFailureReason.TENANT_DENIED,
        }:
            action = LaterActionSuggestion.DO_NOT_RETRY_UNCHANGED
        elif reason is RoutingFailureReason.AUTHORITY_UNAVAILABLE:
            action = LaterActionSuggestion.REROUTE_AFTER_AUTHORITY_REFRESH
        else:
            action = LaterActionSuggestion.REROUTE_AFTER_TOPOLOGY_CHANGE
        hint = (
            ResolutionHint.STRONG_AUTHORITY_REQUIRED
            if strong or reason is RoutingFailureReason.AUTHORITY_UNAVAILABLE
            else ResolutionHint.REMOTE_UNAVAILABLE
            if reason is RoutingFailureReason.REMOTE_RUNTIME
            else ResolutionHint.LOCAL_INDEX
        )
        return RoutingFailureReport(
            reason=reason,
            resolution_hint=hint,
            later_action=action,
            safe_message_reference=request.message_reference,
            index_mutation_sequence=sequence,
        )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Local Router dependency is invalid.",
        details={"component": "routing", "field": field_name},
    )


__all__ = (
    "FALLBACK_SCORER_SOURCE",
    "FALLBACK_SCORER_VERSION",
    "LocalRouter",
    "RP1_SCHEMA_VERSION",
)
