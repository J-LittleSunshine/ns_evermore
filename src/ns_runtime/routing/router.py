# -*- coding: utf-8 -*-
"""Deterministic local Router over exactly one P05 index snapshot."""

from __future__ import annotations

import asyncio
import re
from dataclasses import replace

from ns_common.config import NsRuntimeRoutingConfig
from ns_common.exceptions import NsValidationError
from ns_common.identifiers import IdentifierFactory, NsIdentifierKind
from ns_common.time import Clock
from ns_runtime.connection.index import LocalConnectionIndex

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
    RoutingFailureOutcome,
    RoutingFailureReason,
    RoutingFailureReport,
    RoutingIdentityReference,
    RoutingRequest,
    RoutingScorerIdentity,
    RoutingStrategy,
    SelectedRoutingBinding,
    compute_fallback_candidate_score,
    compute_routing_decision_fingerprint,
    derive_candidate_filter_reason,
    safe_target_reference,
    select_candidates_from_evidence,
)


RP1_SCHEMA_VERSION = "rp-1"
FALLBACK_SCORER_SOURCE = "runtime_fallback"
FALLBACK_SCORER_VERSION = "fallback.v1"
FALLBACK_SCORER_IDENTITY = RoutingScorerIdentity.fallback()
_CONTRACT_TEST_ROUTER_AUTHORITY = object()


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
        _authority: object | None = None,
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
        self._accept_contract_test_authority = (
            _authority is _CONTRACT_TEST_ROUTER_AUTHORITY
        )
        if _authority not in {None, _CONTRACT_TEST_ROUTER_AUTHORITY}:
            _invalid("authority")
        if not isinstance(self._consistency, RoutingConsistencyPolicy):
            _invalid("consistency_policy")
        if not isinstance(self._recorder, RoutingPlanRecorder):
            _invalid("plan_recorder")
        if not isinstance(self._strong, StrongRoutingPlanAuthority):
            _invalid("strong_authority")

    @classmethod
    def for_contract_tests(cls, **values: object) -> "LocalRouter":
        """Explicit non-production router for sealed contract-test evidence."""

        return cls(
            **values,  # type: ignore[arg-type]
            _authority=_CONTRACT_TEST_ROUTER_AUTHORITY,
        )

    async def route(
        self,
        request: RoutingRequest,
        *,
        previous: PreviousRoutingPlanContext | None = None,
    ) -> RoutingDecision:
        if not isinstance(request, RoutingRequest):
            _invalid("request")
        evidence = request.authorization_evidence
        if not (
            evidence.is_contract_test_authority()
            if self._accept_contract_test_authority
            else evidence.is_production_authority()
        ):
            _invalid("request.authorization_authority")
        if previous is not None and not isinstance(
            previous,
            PreviousRoutingPlanContext,
        ):
            _invalid("previous")
        if previous is not None:
            if previous.message_reference != request.message_reference:
                return self._failure(
                    request,
                    RoutingFailureReason.PREVIOUS_MESSAGE_MISMATCH,
                )
            if (
                isinstance(previous.plan_version, bool)
                or not isinstance(previous.plan_version, int)
                or previous.plan_version < 1
            ):
                return self._failure(
                    request,
                    RoutingFailureReason.PREVIOUS_PLAN_VERSION_INVALID,
                )
            if not self._ids.is_valid(
                previous.plan_id,
                expected_kind=NsIdentifierKind.PLAN_ID,
            ):
                return self._failure(
                    request,
                    RoutingFailureReason.PREVIOUS_PLAN_ID_INVALID,
                )
            if re.fullmatch(r"sha256:[0-9a-f]{64}", previous.decision_fingerprint) is None:
                return self._failure(
                    request,
                    RoutingFailureReason.PREVIOUS_FINGERPRINT_INVALID,
                )
            if not previous.has_valid_integrity():
                return self._failure(
                    request,
                    RoutingFailureReason.PREVIOUS_FINGERPRINT_MISMATCH,
                )

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
                RoutingFailureReason.REMOTE_RUNTIME_REQUIRED,
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
                RoutingFailureReason.CANDIDATE_LIMIT_EXCEEDED,
                sequence=snapshot.mutation_sequence,
            )

        evidence: list[CandidateEvidence] = []
        eligible: list[CandidateEvidence] = []
        for connection_id in sorted(intended):
            entry = snapshot.by_connection_id.get(connection_id)
            if entry is None:
                continue
            context = entry.session_context
            rebind_eligible = (
                previous is None
                or request.effective_strategy is RoutingStrategy.BROADCAST
                or self._rebind_allowed(request, context, previous)
            )
            candidate = CandidateEvidence(
                runtime_id=self._runtime_id,
                connection_id=context.connection_id,
                session_id=context.session_id,
                connection_epoch=context.connection_epoch,
                identity_reference=RoutingIdentityReference(value=context.identity),
                tenant_id=context.tenant_id,
                component_type=context.component_type,
                capabilities=context.capabilities,
                required_capabilities=frozenset(target.capabilities or ()),
                connection_state=entry.state,
                active_target_eligible=entry.active_target_eligible,
                routing_eligibility=entry.routing_eligibility,
                rebind_eligible=rebind_eligible,
                filter_reason=CandidateFilterReason.ELIGIBLE,
            )
            reason = derive_candidate_filter_reason(
                target=request.target,
                effective_tenant_id=request.effective_tenant_id,
                candidate=candidate,
            )
            candidate = replace(
                candidate,
                filter_reason=reason or CandidateFilterReason.ELIGIBLE,
            )
            evidence.append(candidate)
            if reason is None:
                score = compute_fallback_candidate_score(
                    target=request.target,
                    scoring_decision=request.scoring_decision,
                    candidate=candidate,
                )
                eligible.append(replace(candidate, score=score))

        filtered = tuple(
            candidate
            for candidate in evidence
            if candidate.filter_reason is not CandidateFilterReason.ELIGIBLE
        )
        if len(evidence) + len(filtered) > self._config.max_plan_evidence_count:
            return self._failure(
                request,
                RoutingFailureReason.PLAN_EVIDENCE_LIMIT_EXCEEDED,
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

        selected_evidence = select_candidates_from_evidence(
            strategy=request.effective_strategy,
            parameters=request.strategy_parameters,
            candidates=tuple(eligible),
        )
        if selected_evidence is None:
            return self._failure(
                request,
                RoutingFailureReason.NO_CANDIDATE,
                sequence=snapshot.mutation_sequence,
            )
        if len(selected_evidence) > self._config.max_selected_target_count:
            return self._failure(
                request,
                RoutingFailureReason.SELECTED_TARGET_LIMIT_EXCEEDED,
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
                binding_rebind_policy=request.effective_rebind_policy,
            )
            for candidate in selected_evidence
        )
        fingerprint = compute_routing_decision_fingerprint(
            target=request.target,
            policy_decision=request.policy_decision,
            authorization_evidence=request.authorization_evidence,
            scorer_identity=FALLBACK_SCORER_IDENTITY,
            candidates=final_evidence,
            selected_bindings=bindings,
            index_mutation_sequence=snapshot.mutation_sequence,
            previous_decision_fingerprint=(
                None if previous is None else previous.decision_fingerprint
            ),
            used_stale_route=False,
        )
        plan = ResolvedRoutingPlan(
            schema_version=RP1_SCHEMA_VERSION,
            plan_id=self._ids.generate(NsIdentifierKind.PLAN_ID),
            plan_version=1 if previous is None else previous.plan_version + 1,
            previous_plan_id=None if previous is None else previous.plan_id,
            previous_decision_fingerprint=(
                None if previous is None else previous.decision_fingerprint
            ),
            previous_message_reference=(
                None if previous is None else previous.message_reference
            ),
            message_reference=request.message_reference,
            decision_fingerprint=fingerprint,
            original_target=target,
            candidates=final_evidence,
            filtered_evidence=filtered,
            selected_bindings=bindings,
            policy_decision=request.policy_decision,
            authorization_evidence=request.authorization_evidence,
            requested_strategy=request.requested_intent.requested_strategy,
            effective_strategy=request.effective_strategy,
            requested_strategy_parameters=(
                request.requested_intent.requested_strategy_parameters
            ),
            effective_strategy_parameters=request.strategy_parameters,
            requested_rebind_policy=(
                request.requested_intent.requested_rebind_policy
            ),
            effective_rebind_policy=request.effective_rebind_policy,
            requested_policy_evidence=(
                f"strategy={request.requested_intent.requested_strategy.value};"
                f"rebind={target.rebind_policy or 'unspecified'}"
            ),
            effective_policy_evidence=(
                f"strategy={request.effective_strategy.value};"
                f"rebind={request.effective_rebind_policy.value}"
            ),
            security_override_evidence=(
                request.policy_decision.security_override_evidence
            ),
            config_version=request.config_version,
            policy_version=request.policy_version,
            scorer_identity=FALLBACK_SCORER_IDENTITY,
            scorer_input_reference=(
                request.scoring_decision.scorer_input_reference
            ),
            scorer_input_version=request.scoring_decision.scorer_input_version,
            iam_decision_reference=request.iam_decision_reference,
            iam_decision_version=request.iam_decision_version,
            authorized_target_reference=(
                request.authorization_evidence.authorized_target_reference
            ),
            effective_permission_snapshot_ref=(
                request.authorization_evidence.effective_permission_snapshot_ref
            ),
            effective_permission_snapshot_version=(
                request.authorization_evidence.effective_permission_snapshot_version
            ),
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
                    RoutingFailureReason.STRONG_PLAN_AUTHORITY_UNAVAILABLE,
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

    def _failure_reason_from_filtered(self, filtered):
        reasons = {value.filter_reason for value in filtered}
        if CandidateFilterReason.DRAINING in reasons:
            return RoutingFailureReason.DRAINING_TARGET
        if CandidateFilterReason.RECONNECT_GRACE in reasons:
            return RoutingFailureReason.RECONNECT_GRACE_TARGET
        if CandidateFilterReason.AUTHORITY_SUSPENDED in reasons:
            return RoutingFailureReason.AUTHORITY_SUSPENDED
        if CandidateFilterReason.SESSION_EXPIRY_SUSPENDED in reasons:
            return RoutingFailureReason.SESSION_EXPIRY_SUSPENDED
        if CandidateFilterReason.EPOCH_STALE in reasons:
            return RoutingFailureReason.STALE_CONNECTION_EPOCH
        if CandidateFilterReason.CAPABILITY_MISMATCH in reasons:
            return RoutingFailureReason.CAPABILITY_MISMATCH
        return RoutingFailureReason.NO_CANDIDATE

    def _failure(self, request, reason, *, sequence=None, strong=False):
        if reason in {
            RoutingFailureReason.TARGET_REQUIRED,
            RoutingFailureReason.STRATEGY_NOT_PERMITTED,
            RoutingFailureReason.REBIND_NOT_PERMITTED,
            RoutingFailureReason.PREVIOUS_MESSAGE_MISMATCH,
            RoutingFailureReason.PREVIOUS_PLAN_ID_INVALID,
            RoutingFailureReason.PREVIOUS_PLAN_VERSION_INVALID,
            RoutingFailureReason.PREVIOUS_FINGERPRINT_INVALID,
            RoutingFailureReason.PREVIOUS_FINGERPRINT_MISMATCH,
        }:
            action = LaterActionSuggestion.SUBMIT_CORRECTED_TARGET
        elif reason in {
            RoutingFailureReason.TARGET_NOT_FOUND,
            RoutingFailureReason.TENANT_DENIED,
        }:
            action = LaterActionSuggestion.DO_NOT_RETRY_UNCHANGED
        elif reason is RoutingFailureReason.STRONG_PLAN_AUTHORITY_UNAVAILABLE:
            action = LaterActionSuggestion.REROUTE_AFTER_AUTHORITY_REFRESH
        else:
            action = LaterActionSuggestion.REROUTE_AFTER_TOPOLOGY_CHANGE
        hint = (
            ResolutionHint.AUTHORITY_RECOVERY_REQUIRED
            if strong or reason is RoutingFailureReason.STRONG_PLAN_AUTHORITY_UNAVAILABLE
            else ResolutionHint.REMOTE_RUNTIME_REQUIRED
            if reason is RoutingFailureReason.REMOTE_RUNTIME_REQUIRED
            else ResolutionHint.LOCAL
        )
        return RoutingFailureReport(
            outcome=(
                RoutingFailureOutcome.REJECTED
                if reason in {
                    RoutingFailureReason.TARGET_REQUIRED,
                    RoutingFailureReason.STRATEGY_NOT_PERMITTED,
                    RoutingFailureReason.REBIND_NOT_PERMITTED,
                    RoutingFailureReason.AUTHORIZATION_EVIDENCE_MISMATCH,
                    RoutingFailureReason.PREVIOUS_MESSAGE_MISMATCH,
                    RoutingFailureReason.PREVIOUS_PLAN_ID_INVALID,
                    RoutingFailureReason.PREVIOUS_PLAN_VERSION_INVALID,
                    RoutingFailureReason.PREVIOUS_FINGERPRINT_INVALID,
                    RoutingFailureReason.PREVIOUS_FINGERPRINT_MISMATCH,
                    RoutingFailureReason.TARGET_NOT_FOUND,
                    RoutingFailureReason.TENANT_DENIED,
                }
                else RoutingFailureOutcome.UNAVAILABLE
            ),
            reason=reason,
            original_target_safe_reference=safe_target_reference(request.target),
            safe_message_reference=request.message_reference,
            config_version=request.config_version,
            policy_version=request.policy_version,
            index_mutation_sequence=sequence,
            resolution_hint=hint,
            later_action=action,
            occurred_at=self._clock.utc_now(),
        )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Local Router dependency is invalid.",
        details={"component": "routing", "field": field_name},
    )


__all__ = (
    "FALLBACK_SCORER_SOURCE",
    "FALLBACK_SCORER_VERSION",
    "FALLBACK_SCORER_IDENTITY",
    "LocalRouter",
    "RP1_SCHEMA_VERSION",
)
