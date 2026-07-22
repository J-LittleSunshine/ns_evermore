# -*- coding: utf-8 -*-
"""Immutable RP-1 request, policy, evidence, decision, and projection contracts."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from ns_common.exceptions import (
    NsRuntimeIamDeniedError,
    NsRuntimeRouteRejectedError,
    NsRuntimeRouteUnavailableError,
    NsRuntimeTargetNotFoundError,
    NsValidationError,
)
from ns_runtime.processor.contracts import AuthorizationDecisionEvidence
from ns_runtime.protocol import TargetGroup


_SAFE_REFERENCE = re.compile(r"sha256:[0-9a-f]{16}")
_DECISION_FINGERPRINT = re.compile(r"sha256:[0-9a-f]{64}")
_PLAN_ID = re.compile(r"plan_[0-9a-f]{32}")


class RoutingStrategy(str, Enum):
    SINGLE = "single"
    ALL = "all"
    BROADCAST = "broadcast"
    QUORUM = "quorum"
    ALL_REQUIRED = "all_required"
    WEIGHTED_SUBSET = "weighted_subset"


class RebindPolicy(str, Enum):
    FIXED_CONNECTION = "fixed_connection"
    SAME_IDENTITY = "same_identity"
    SAME_CAPABILITY = "same_capability"
    SAME_TENANT = "same_tenant"
    NO_REBIND_FOR_CONTROL = "no_rebind_for_control"


class RoutingFailureOutcome(str, Enum):
    REJECTED = "rejected"
    UNAVAILABLE = "unavailable"


class RoutingFailureReason(str, Enum):
    TARGET_REQUIRED = "target_required"
    STRATEGY_NOT_PERMITTED = "strategy_not_permitted"
    REBIND_NOT_PERMITTED = "rebind_not_permitted"
    AUTHORIZATION_EVIDENCE_MISMATCH = "authorization_evidence_mismatch"
    PREVIOUS_MESSAGE_MISMATCH = "previous_message_mismatch"
    PREVIOUS_PLAN_ID_INVALID = "previous_plan_id_invalid"
    PREVIOUS_PLAN_VERSION_INVALID = "previous_plan_version_invalid"
    PREVIOUS_FINGERPRINT_INVALID = "previous_fingerprint_invalid"
    PREVIOUS_FINGERPRINT_MISMATCH = "previous_fingerprint_mismatch"
    TARGET_NOT_FOUND = "target_not_found"
    TENANT_DENIED = "tenant_denied"
    CANDIDATE_LIMIT_EXCEEDED = "candidate_limit_exceeded"
    SELECTED_TARGET_LIMIT_EXCEEDED = "selected_target_limit_exceeded"
    PLAN_EVIDENCE_LIMIT_EXCEEDED = "plan_evidence_limit_exceeded"
    NO_CANDIDATE = "no_candidate"
    CAPABILITY_MISMATCH = "capability_mismatch"
    STALE_CONNECTION_EPOCH = "stale_connection_epoch"
    DRAINING_TARGET = "draining_target"
    RECONNECT_GRACE_TARGET = "reconnect_grace_target"
    AUTHORITY_SUSPENDED = "authority_suspended"
    SESSION_EXPIRY_SUSPENDED = "session_expiry_suspended"
    STRONG_PLAN_AUTHORITY_UNAVAILABLE = "strong_plan_authority_unavailable"
    REMOTE_RUNTIME_REQUIRED = "remote_runtime_required"
    INDEX_UNAVAILABLE = "index_unavailable"


class CandidateFilterReason(str, Enum):
    ELIGIBLE = "eligible"
    SELECTED = "selected"
    TENANT_MISMATCH = "tenant_mismatch"
    COMPONENT_MISMATCH = "component_mismatch"
    CAPABILITY_MISMATCH = "capability_mismatch"
    RUNTIME_MISMATCH = "runtime_mismatch"
    NOT_ACTIVE = "not_active"
    NOT_ELIGIBLE = "not_eligible"
    DRAINING = "draining"
    RECONNECT_GRACE = "reconnect_grace"
    AUTHORITY_SUSPENDED = "authority_suspended"
    SESSION_EXPIRY_SUSPENDED = "session_expiry_suspended"
    EPOCH_STALE = "epoch_stale"
    REBIND_FORBIDDEN = "rebind_forbidden"


class ResolutionHint(str, Enum):
    LOCAL = "local"
    MASTER_QUERY_REQUIRED = "master_query_required"
    REMOTE_RUNTIME_REQUIRED = "remote_runtime_required"
    AUTHORITY_RECOVERY_REQUIRED = "authority_recovery_required"


class LaterActionSuggestion(str, Enum):
    DO_NOT_RETRY_UNCHANGED = "do_not_retry_unchanged"
    REROUTE_AFTER_TOPOLOGY_CHANGE = "reroute_after_topology_change"
    REROUTE_AFTER_AUTHORITY_REFRESH = "reroute_after_authority_refresh"
    SUBMIT_CORRECTED_TARGET = "submit_corrected_target"


@dataclass(frozen=True, slots=True, kw_only=True)
class RoutingIdentityReference:
    value: str = field(repr=False)

    def __post_init__(self) -> None:
        _nonempty(self.value, "identity_reference.value")

    @property
    def safe_digest(self) -> str:
        return _digest(self.value)


@dataclass(frozen=True, slots=True, kw_only=True)
class StrategyParameters:
    strategy: RoutingStrategy
    fanout_count: int | None = None
    required_count: int | None = None
    subset_size: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.strategy, RoutingStrategy):
            _invalid("strategy_parameters.strategy")
        for name in ("fanout_count", "required_count", "subset_size"):
            value = getattr(self, name)
            if value is not None and (
                isinstance(value, bool) or not isinstance(value, int) or value < 1
            ):
                _invalid(f"strategy_parameters.{name}")
        if self.strategy is RoutingStrategy.QUORUM:
            if self.fanout_count is None or self.required_count is None:
                _invalid("strategy_parameters.quorum_counts")
            if self.subset_size is not None or self.required_count > self.fanout_count:
                _invalid("strategy_parameters.quorum_shape")
        elif self.strategy is RoutingStrategy.WEIGHTED_SUBSET:
            if self.subset_size is None:
                _invalid("strategy_parameters.subset_size")
            if self.fanout_count is not None or self.required_count is not None:
                _invalid("strategy_parameters.weighted_subset_shape")
        elif any(
            value is not None
            for value in (self.fanout_count, self.required_count, self.subset_size)
        ):
            _invalid("strategy_parameters.counts_forbidden")


@dataclass(frozen=True, slots=True, kw_only=True)
class RequestedRoutingIntent:
    normalized_target: TargetGroup = field(repr=False)
    requested_strategy: RoutingStrategy
    requested_rebind_policy: RebindPolicy | None
    requested_strategy_parameters: StrategyParameters

    def __post_init__(self) -> None:
        if not isinstance(self.normalized_target, TargetGroup):
            _invalid("routing_intent.normalized_target")
        if not isinstance(self.requested_strategy, RoutingStrategy):
            _invalid("routing_intent.requested_strategy")
        if self.requested_rebind_policy is not None and not isinstance(
            self.requested_rebind_policy,
            RebindPolicy,
        ):
            _invalid("routing_intent.requested_rebind_policy")
        if (
            not isinstance(self.requested_strategy_parameters, StrategyParameters)
            or self.requested_strategy_parameters.strategy is not self.requested_strategy
        ):
            _invalid("routing_intent.requested_strategy_parameters")

    @classmethod
    def from_target(cls, target: TargetGroup) -> "RequestedRoutingIntent":
        if not isinstance(target, TargetGroup):
            _invalid("routing_intent.normalized_target")
        strategy = RoutingStrategy(target.multi_connection_policy or "single")
        return cls(
            normalized_target=target,
            requested_strategy=strategy,
            requested_rebind_policy=(
                None if target.rebind_policy is None else RebindPolicy(target.rebind_policy)
            ),
            requested_strategy_parameters=StrategyParameters(
                strategy=strategy,
                fanout_count=target.fanout_count,
                required_count=target.required_count,
                subset_size=target.subset_size,
            ),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class RoutingScoringDecision:
    scorer_input_version: str
    scorer_input_reference: str
    trusted_affinity_connection_ids: tuple[str, ...] = field(
        default=(),
        repr=False,
    )
    runtime_policy_static_weights: tuple[tuple[str, int], ...] = field(
        default=(),
        repr=False,
    )

    def __post_init__(self) -> None:
        _nonempty(self.scorer_input_version, "scoring_decision.version")
        if _DECISION_FINGERPRINT.fullmatch(self.scorer_input_reference) is None:
            _invalid("scoring_decision.reference")
        _unique_strings(
            self.trusted_affinity_connection_ids,
            "scoring_decision.trusted_affinity_connection_ids",
        )
        if self.trusted_affinity_connection_ids != tuple(
            sorted(self.trusted_affinity_connection_ids),
        ):
            _invalid("scoring_decision.affinity_order")
        if not isinstance(self.runtime_policy_static_weights, tuple) or any(
            not isinstance(item, tuple) or len(item) != 2
            for item in self.runtime_policy_static_weights
        ):
            _invalid("scoring_decision.static_weights")
        seen: set[str] = set()
        for connection_id, weight in self.runtime_policy_static_weights:
            _nonempty(connection_id, "scoring_decision.static_weight.connection_id")
            if connection_id in seen:
                _invalid("scoring_decision.static_weight.duplicate")
            if isinstance(weight, bool) or not isinstance(weight, int):
                _invalid("scoring_decision.static_weight.value")
            seen.add(connection_id)
        if self.runtime_policy_static_weights != tuple(
            sorted(self.runtime_policy_static_weights),
        ):
            _invalid("scoring_decision.static_weight_order")
        if self.scorer_input_reference != _scoring_input_reference(
            version=self.scorer_input_version,
            affinity=self.trusted_affinity_connection_ids,
            weights=self.runtime_policy_static_weights,
        ):
            _invalid("scoring_decision.reference_mismatch")

    @classmethod
    def from_inputs(
        cls,
        *,
        scorer_input_version: str,
        trusted_affinity_connection_ids: tuple[str, ...] = (),
        runtime_policy_static_weights: tuple[tuple[str, int], ...] = (),
    ) -> "RoutingScoringDecision":
        affinity = tuple(sorted(trusted_affinity_connection_ids))
        weights = tuple(sorted(runtime_policy_static_weights))
        return cls(
            scorer_input_version=scorer_input_version,
            scorer_input_reference=_scoring_input_reference(
                version=scorer_input_version,
                affinity=affinity,
                weights=weights,
            ),
            trusted_affinity_connection_ids=affinity,
            runtime_policy_static_weights=weights,
        )

    @classmethod
    def empty(cls) -> "RoutingScoringDecision":
        return cls.from_inputs(scorer_input_version="routing-scoring.v1")


@dataclass(frozen=True, slots=True, kw_only=True)
class RoutingPolicyDecision:
    accepted: bool
    requested_strategy: RoutingStrategy
    effective_strategy: RoutingStrategy | None
    requested_rebind_policy: RebindPolicy | None
    effective_rebind_policy: RebindPolicy | None
    requested_strategy_parameters: StrategyParameters
    effective_strategy_parameters: StrategyParameters | None
    rejection_reason: RoutingFailureReason | None
    config_version: str
    policy_version: str
    security_override_evidence: str
    security_sensitive: bool
    scoring_decision: RoutingScoringDecision

    def __post_init__(self) -> None:
        if type(self.accepted) is not bool:
            _invalid("routing_policy_decision.accepted")
        if type(self.security_sensitive) is not bool:
            _invalid("routing_policy_decision.security_sensitive")
        if not isinstance(self.scoring_decision, RoutingScoringDecision):
            _invalid("routing_policy_decision.scoring_decision")
        if not isinstance(self.requested_strategy, RoutingStrategy):
            _invalid("routing_policy_decision.requested_strategy")
        if self.requested_rebind_policy is not None and not isinstance(
            self.requested_rebind_policy, RebindPolicy,
        ):
            _invalid("routing_policy_decision.requested_rebind_policy")
        if (
            not isinstance(self.requested_strategy_parameters, StrategyParameters)
            or self.requested_strategy_parameters.strategy is not self.requested_strategy
        ):
            _invalid("routing_policy_decision.requested_parameters")
        for name in ("config_version", "policy_version", "security_override_evidence"):
            _nonempty(getattr(self, name), f"routing_policy_decision.{name}")
        if self.accepted:
            if (
                not isinstance(self.effective_strategy, RoutingStrategy)
                or not isinstance(self.effective_rebind_policy, RebindPolicy)
                or not isinstance(self.effective_strategy_parameters, StrategyParameters)
                or self.rejection_reason is not None
            ):
                _invalid("routing_policy_decision.accepted_shape")
            if self.effective_strategy_parameters.strategy is not self.effective_strategy:
                _invalid("routing_policy_decision.effective_parameters")
            if self.effective_strategy is not self.requested_strategy:
                _invalid("routing_policy_decision.strategy_expansion")
            _validate_no_parameter_expansion(
                self.requested_strategy_parameters,
                self.effective_strategy_parameters,
            )
            allowed_effective_rebind = {
                RebindPolicy.FIXED_CONNECTION,
                RebindPolicy.NO_REBIND_FOR_CONTROL,
            }
            if self.requested_rebind_policy is not None:
                allowed_effective_rebind.add(self.requested_rebind_policy)
            if self.effective_rebind_policy not in allowed_effective_rebind:
                _invalid("routing_policy_decision.rebind_expansion")
            if (
                self.requested_strategy is RoutingStrategy.BROADCAST
                and self.effective_rebind_policy is not RebindPolicy.FIXED_CONNECTION
            ):
                _invalid("routing_policy_decision.broadcast_rebind")
            if (
                self.security_sensitive
                and self.effective_rebind_policy
                is not RebindPolicy.NO_REBIND_FOR_CONTROL
            ):
                _invalid("routing_policy_decision.security_rebind")
            claims_security_override = self.security_override_evidence.endswith(
                ":no_rebind_for_control",
            )
            if claims_security_override is not self.security_sensitive:
                _invalid("routing_policy_decision.security_override_evidence")
        elif (
            self.effective_strategy is not None
            or self.effective_rebind_policy is not None
            or self.effective_strategy_parameters is not None
            or self.rejection_reason not in {
                RoutingFailureReason.STRATEGY_NOT_PERMITTED,
                RoutingFailureReason.REBIND_NOT_PERMITTED,
            }
        ):
            _invalid("routing_policy_decision.rejected_shape")


@dataclass(frozen=True, slots=True, kw_only=True)
class RoutingRequest:
    message_reference: str
    message_type: str
    target: TargetGroup = field(repr=False)
    requested_intent: RequestedRoutingIntent
    policy_decision: RoutingPolicyDecision
    authorization_evidence: AuthorizationDecisionEvidence = field(repr=False)

    def __post_init__(self) -> None:
        if _SAFE_REFERENCE.fullmatch(self.message_reference) is None:
            _invalid("routing_request.message_reference")
        _nonempty(self.message_type, "routing_request.message_type")
        if not isinstance(self.target, TargetGroup):
            _invalid("routing_request.target")
        if not isinstance(self.requested_intent, RequestedRoutingIntent):
            _invalid("routing_request.requested_intent")
        if self.requested_intent.normalized_target != self.target:
            _invalid("routing_request.intent_target")
        if not isinstance(self.policy_decision, RoutingPolicyDecision):
            _invalid("routing_request.policy_decision")
        if not self.policy_decision.accepted:
            _invalid("routing_request.unaccepted_policy_decision")
        if (
            self.policy_decision.requested_strategy is not self.requested_intent.requested_strategy
            or self.policy_decision.requested_rebind_policy
            is not self.requested_intent.requested_rebind_policy
            or self.policy_decision.requested_strategy_parameters
            != self.requested_intent.requested_strategy_parameters
        ):
            _invalid("routing_request.policy_intent_mismatch")
        if not isinstance(self.authorization_evidence, AuthorizationDecisionEvidence):
            _invalid("routing_request.authorization_evidence")
        evidence = self.authorization_evidence
        expected_target_reference = AuthorizationDecisionEvidence.target_reference(
            self.target,
            session_tenant_id=evidence.principal_tenant_id,
        )
        target_tenant = self.target.tenant_id
        crosses_tenant = (
            target_tenant is not None
            and target_tenant != evidence.principal_tenant_id
        )
        expected_effective_tenant = (
            target_tenant if crosses_tenant else evidence.principal_tenant_id
        )
        if (
            evidence.message_reference != self.message_reference
            or evidence.message_type != self.message_type
            or evidence.authorized_target_reference != expected_target_reference
            or evidence.cross_tenant_authorized is not crosses_tenant
            or evidence.effective_tenant_id != expected_effective_tenant
            or not evidence.has_valid_binding()
        ):
            _invalid("routing_request.authorization_evidence_mismatch")

    @property
    def effective_tenant_id(self) -> str:
        return self.authorization_evidence.effective_tenant_id

    @property
    def cross_tenant_authorized(self) -> bool:
        return self.authorization_evidence.cross_tenant_authorized

    @property
    def effective_strategy(self) -> RoutingStrategy:
        assert self.policy_decision.effective_strategy is not None
        return self.policy_decision.effective_strategy

    @property
    def effective_rebind_policy(self) -> RebindPolicy:
        assert self.policy_decision.effective_rebind_policy is not None
        return self.policy_decision.effective_rebind_policy

    @property
    def strategy_parameters(self) -> StrategyParameters:
        assert self.policy_decision.effective_strategy_parameters is not None
        return self.policy_decision.effective_strategy_parameters

    @property
    def config_version(self) -> str:
        return self.policy_decision.config_version

    @property
    def policy_version(self) -> str:
        return self.policy_decision.policy_version

    @property
    def iam_decision_reference(self) -> str:
        return self.authorization_evidence.decision_reference

    @property
    def iam_decision_version(self) -> str:
        return self.authorization_evidence.decision_version

    @property
    def scoring_decision(self) -> RoutingScoringDecision:
        return self.policy_decision.scoring_decision


@dataclass(frozen=True, slots=True, kw_only=True)
class SelectedRoutingBinding:
    runtime_id: str = field(repr=False)
    connection_id: str = field(repr=False)
    session_id: str = field(repr=False)
    connection_epoch: int
    tenant_id: str = field(repr=False)
    identity_reference: RoutingIdentityReference = field(repr=False)
    required_capabilities: frozenset[str] = field(repr=False)
    component_type: str
    binding_rebind_policy: RebindPolicy

    def __post_init__(self) -> None:
        for name in ("runtime_id", "connection_id", "session_id", "tenant_id", "component_type"):
            _nonempty(getattr(self, name), f"selected_binding.{name}")
        if isinstance(self.connection_epoch, bool) or not isinstance(self.connection_epoch, int) or self.connection_epoch < 0:
            _invalid("selected_binding.connection_epoch")
        if not isinstance(self.identity_reference, RoutingIdentityReference):
            _invalid("selected_binding.identity_reference")
        if not isinstance(self.required_capabilities, frozenset):
            _invalid("selected_binding.required_capabilities")
        if not isinstance(self.binding_rebind_policy, RebindPolicy):
            _invalid("selected_binding.binding_rebind_policy")
        _unique_strings(tuple(self.required_capabilities), "selected_binding.required_capabilities")


@dataclass(frozen=True, slots=True, kw_only=True)
class CandidateEvidence:
    connection_id: str = field(repr=False)
    session_id: str = field(repr=False)
    connection_epoch: int
    identity_reference: RoutingIdentityReference = field(repr=False)
    tenant_id: str = field(repr=False)
    component_type: str
    capabilities: frozenset[str] = field(repr=False)
    filter_reason: CandidateFilterReason
    score: tuple[int | str, ...] | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        for name in ("connection_id", "session_id", "tenant_id", "component_type"):
            _nonempty(getattr(self, name), f"candidate.{name}")
        if isinstance(self.connection_epoch, bool) or not isinstance(self.connection_epoch, int) or self.connection_epoch < 0:
            _invalid("candidate.connection_epoch")
        if not isinstance(self.identity_reference, RoutingIdentityReference):
            _invalid("candidate.identity_reference")
        if not isinstance(self.capabilities, frozenset):
            _invalid("candidate.capabilities")
        if not isinstance(self.filter_reason, CandidateFilterReason):
            _invalid("candidate.filter_reason")
        if self.score is not None and not isinstance(self.score, tuple):
            _invalid("candidate.score")


@dataclass(frozen=True, slots=True, kw_only=True)
class PreviousRoutingPlanContext:
    plan_id: str
    plan_version: int
    message_reference: str
    decision_fingerprint: str
    context_integrity_fingerprint: str
    selected_bindings: tuple[SelectedRoutingBinding, ...] = field(repr=False)

    def __post_init__(self) -> None:
        _nonempty(self.plan_id, "previous_plan.plan_id")
        if isinstance(self.plan_version, bool) or not isinstance(self.plan_version, int) or self.plan_version < 1:
            _invalid("previous_plan.plan_version")
        if _SAFE_REFERENCE.fullmatch(self.message_reference) is None:
            _invalid("previous_plan.message_reference")
        if _DECISION_FINGERPRINT.fullmatch(self.decision_fingerprint) is None:
            _invalid("previous_plan.decision_fingerprint")
        if _DECISION_FINGERPRINT.fullmatch(self.context_integrity_fingerprint) is None:
            _invalid("previous_plan.context_integrity_fingerprint")
        _validate_bindings(self.selected_bindings, "previous_plan.selected_bindings")

    def has_valid_integrity(self) -> bool:
        return self.context_integrity_fingerprint == _previous_context_integrity(
            plan_id=self.plan_id,
            plan_version=self.plan_version,
            message_reference=self.message_reference,
            decision_fingerprint=self.decision_fingerprint,
            selected_bindings=self.selected_bindings,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ResolvedRoutingPlan:
    schema_version: str
    plan_id: str = field(repr=False)
    plan_version: int
    previous_plan_id: str | None = field(default=None, repr=False)
    previous_decision_fingerprint: str | None = field(default=None, repr=False)
    previous_message_reference: str | None = field(default=None, repr=False)
    message_reference: str = field(repr=False)
    decision_fingerprint: str
    original_target: TargetGroup = field(repr=False)
    candidates: tuple[CandidateEvidence, ...] = field(repr=False)
    filtered_evidence: tuple[CandidateEvidence, ...] = field(repr=False)
    selected_bindings: tuple[SelectedRoutingBinding, ...] = field(repr=False)
    policy_decision: RoutingPolicyDecision = field(repr=False)
    authorization_evidence: AuthorizationDecisionEvidence = field(repr=False)
    requested_strategy: RoutingStrategy
    effective_strategy: RoutingStrategy
    requested_strategy_parameters: StrategyParameters
    effective_strategy_parameters: StrategyParameters
    requested_rebind_policy: RebindPolicy | None
    effective_rebind_policy: RebindPolicy
    requested_policy_evidence: str
    effective_policy_evidence: str
    security_override_evidence: str
    config_version: str
    policy_version: str
    scorer_source: str
    scorer_version: str
    scorer_input_reference: str
    scorer_input_version: str
    iam_decision_reference: str = field(repr=False)
    iam_decision_version: str = field(repr=False)
    authorized_target_reference: str = field(repr=False)
    effective_permission_snapshot_ref: str = field(repr=False)
    effective_permission_snapshot_version: str = field(repr=False)
    index_mutation_sequence: int
    local_hit: bool
    used_stale_route: bool
    created_at: datetime

    def __post_init__(self) -> None:
        for name in (
            "schema_version", "plan_id", "message_reference", "decision_fingerprint",
            "requested_policy_evidence", "effective_policy_evidence",
            "security_override_evidence", "config_version", "policy_version",
            "scorer_source", "scorer_version", "scorer_input_reference",
            "scorer_input_version", "iam_decision_reference",
            "iam_decision_version", "effective_permission_snapshot_ref",
            "effective_permission_snapshot_version",
        ):
            _nonempty(getattr(self, name), f"routing_plan.{name}")
        if _SAFE_REFERENCE.fullmatch(self.message_reference) is None:
            _invalid("routing_plan.message_reference")
        if _PLAN_ID.fullmatch(self.plan_id) is None:
            _invalid("routing_plan.plan_id")
        if _DECISION_FINGERPRINT.fullmatch(self.decision_fingerprint) is None:
            _invalid("routing_plan.decision_fingerprint")
        if isinstance(self.plan_version, bool) or not isinstance(self.plan_version, int) or self.plan_version < 1:
            _invalid("routing_plan.plan_version")
        if (self.plan_version == 1) is not (self.previous_plan_id is None):
            _invalid("routing_plan.version_previous_plan")
        if self.plan_version == 1:
            if (
                self.previous_decision_fingerprint is not None
                or self.previous_message_reference is not None
            ):
                _invalid("routing_plan.previous_context")
        else:
            if self.previous_plan_id is None or _PLAN_ID.fullmatch(self.previous_plan_id) is None:
                _invalid("routing_plan.previous_plan_id")
            if self.previous_decision_fingerprint is None or _DECISION_FINGERPRINT.fullmatch(self.previous_decision_fingerprint) is None:
                _invalid("routing_plan.previous_decision_fingerprint")
            if self.previous_message_reference != self.message_reference:
                _invalid("routing_plan.previous_message_reference")
        if not isinstance(self.original_target, TargetGroup):
            _invalid("routing_plan.original_target")
        for name, values, value_type in (
            ("candidates", self.candidates, CandidateEvidence),
            ("filtered_evidence", self.filtered_evidence, CandidateEvidence),
        ):
            if not isinstance(values, tuple) or any(not isinstance(value, value_type) for value in values):
                _invalid(f"routing_plan.{name}")
        _validate_bindings(self.selected_bindings, "routing_plan.selected_bindings")
        if (
            not isinstance(self.policy_decision, RoutingPolicyDecision)
            or not self.policy_decision.accepted
        ):
            _invalid("routing_plan.policy_decision")
        if not isinstance(
            self.authorization_evidence,
            AuthorizationDecisionEvidence,
        ) or not self.authorization_evidence.has_valid_binding():
            _invalid("routing_plan.authorization_evidence")
        intent = RequestedRoutingIntent.from_target(self.original_target)
        decision = self.policy_decision
        expected_requested_evidence = (
            f"strategy={intent.requested_strategy.value};"
            f"rebind={self.original_target.rebind_policy or 'unspecified'}"
        )
        expected_effective_evidence = (
            f"strategy={decision.effective_strategy.value};"
            f"rebind={decision.effective_rebind_policy.value}"
        )
        if (
            decision.requested_strategy is not intent.requested_strategy
            or decision.requested_rebind_policy is not intent.requested_rebind_policy
            or decision.requested_strategy_parameters
            != intent.requested_strategy_parameters
            or self.requested_strategy is not decision.requested_strategy
            or self.effective_strategy is not decision.effective_strategy
            or self.requested_strategy_parameters
            != decision.requested_strategy_parameters
            or self.effective_strategy_parameters
            != decision.effective_strategy_parameters
            or self.requested_rebind_policy is not decision.requested_rebind_policy
            or self.effective_rebind_policy is not decision.effective_rebind_policy
            or self.security_override_evidence
            != decision.security_override_evidence
            or self.requested_policy_evidence != expected_requested_evidence
            or self.effective_policy_evidence != expected_effective_evidence
            or self.config_version != decision.config_version
            or self.policy_version != decision.policy_version
            or self.scorer_input_reference
            != decision.scoring_decision.scorer_input_reference
            or self.scorer_input_version
            != decision.scoring_decision.scorer_input_version
        ):
            _invalid("routing_plan.policy_authority_mismatch")
        authorization = self.authorization_evidence
        expected_target_reference = AuthorizationDecisionEvidence.target_reference(
            self.original_target,
            session_tenant_id=authorization.principal_tenant_id,
        )
        if (
            self.message_reference != authorization.message_reference
            or self.iam_decision_reference != authorization.decision_reference
            or self.iam_decision_version != authorization.decision_version
            or self.authorized_target_reference
            != authorization.authorized_target_reference
            or self.authorized_target_reference != expected_target_reference
            or self.effective_permission_snapshot_ref
            != authorization.effective_permission_snapshot_ref
            or self.effective_permission_snapshot_version
            != authorization.effective_permission_snapshot_version
        ):
            _invalid("routing_plan.authorization_authority_mismatch")
        if _SAFE_REFERENCE.fullmatch(self.authorized_target_reference) is None:
            _invalid("routing_plan.authorized_target_reference")
        if _DECISION_FINGERPRINT.fullmatch(self.scorer_input_reference) is None:
            _invalid("routing_plan.scorer_input_reference")
        if not isinstance(self.requested_strategy, RoutingStrategy) or not isinstance(self.effective_strategy, RoutingStrategy):
            _invalid("routing_plan.strategy")
        if (
            not isinstance(self.requested_strategy_parameters, StrategyParameters)
            or self.requested_strategy_parameters.strategy is not self.requested_strategy
            or not isinstance(self.effective_strategy_parameters, StrategyParameters)
            or self.effective_strategy_parameters.strategy is not self.effective_strategy
        ):
            _invalid("routing_plan.strategy_parameters")
        if self.requested_rebind_policy is not None and not isinstance(self.requested_rebind_policy, RebindPolicy):
            _invalid("routing_plan.requested_rebind_policy")
        if not isinstance(self.effective_rebind_policy, RebindPolicy):
            _invalid("routing_plan.effective_rebind_policy")
        if self.effective_strategy is not self.requested_strategy:
            _invalid("routing_plan.strategy_expansion")
        _validate_no_parameter_expansion(
            self.requested_strategy_parameters,
            self.effective_strategy_parameters,
        )
        allowed_effective_rebind = {
            RebindPolicy.FIXED_CONNECTION,
            RebindPolicy.NO_REBIND_FOR_CONTROL,
        }
        if self.requested_rebind_policy is not None:
            allowed_effective_rebind.add(self.requested_rebind_policy)
        if self.effective_rebind_policy not in allowed_effective_rebind:
            _invalid("routing_plan.rebind_expansion")
        if (
            self.requested_strategy is RoutingStrategy.BROADCAST
            and self.effective_rebind_policy is not RebindPolicy.FIXED_CONNECTION
        ):
            _invalid("routing_plan.broadcast_rebind")
        claims_security_override = self.security_override_evidence.endswith(
            ":no_rebind_for_control",
        )
        if (
            decision.security_sensitive
            and self.effective_rebind_policy
            is not RebindPolicy.NO_REBIND_FOR_CONTROL
        ) or claims_security_override is not decision.security_sensitive:
            _invalid("routing_plan.security_override_evidence")
        if any(
            binding.binding_rebind_policy is not self.effective_rebind_policy
            for binding in self.selected_bindings
        ):
            _invalid("routing_plan.binding_rebind_policy")
        if isinstance(self.index_mutation_sequence, bool) or not isinstance(self.index_mutation_sequence, int) or self.index_mutation_sequence < 0:
            _invalid("routing_plan.index_mutation_sequence")
        if type(self.local_hit) is not bool or type(self.used_stale_route) is not bool:
            _invalid("routing_plan.flags")
        if self.used_stale_route:
            _invalid("routing_plan.used_stale_route")
        object.__setattr__(self, "created_at", _utc(self.created_at))

    @property
    def strategy(self) -> RoutingStrategy:
        return self.effective_strategy

    @property
    def strategy_parameters(self) -> StrategyParameters:
        return self.effective_strategy_parameters

    def previous_context(self) -> PreviousRoutingPlanContext:
        integrity = _previous_context_integrity(
            plan_id=self.plan_id,
            plan_version=self.plan_version,
            message_reference=self.message_reference,
            decision_fingerprint=self.decision_fingerprint,
            selected_bindings=self.selected_bindings,
        )
        return PreviousRoutingPlanContext(
            plan_id=self.plan_id,
            plan_version=self.plan_version,
            message_reference=self.message_reference,
            decision_fingerprint=self.decision_fingerprint,
            context_integrity_fingerprint=integrity,
            selected_bindings=self.selected_bindings,
        )

    def safe_projection(self) -> "SafeRoutingProjection":
        return SafeRoutingProjection(
            plan_reference=_digest(self.plan_id),
            message_reference=self.message_reference,
            decision_fingerprint=self.decision_fingerprint,
            strategy=self.effective_strategy,
            candidate_count=len(self.candidates),
            filtered_count=len(self.filtered_evidence),
            selected_count=len(self.selected_bindings),
            plan_version=self.plan_version,
            index_mutation_sequence=self.index_mutation_sequence,
            local_hit=self.local_hit,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class RoutingFailureReport:
    outcome: RoutingFailureOutcome
    reason: RoutingFailureReason
    original_target_safe_reference: str
    safe_message_reference: str
    config_version: str
    policy_version: str
    index_mutation_sequence: int | None
    later_action: LaterActionSuggestion
    resolution_hint: ResolutionHint
    occurred_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.outcome, RoutingFailureOutcome):
            _invalid("routing_failure.outcome")
        if not isinstance(self.reason, RoutingFailureReason):
            _invalid("routing_failure.reason")
        if not isinstance(self.resolution_hint, ResolutionHint):
            _invalid("routing_failure.resolution_hint")
        if not isinstance(self.later_action, LaterActionSuggestion):
            _invalid("routing_failure.later_action")
        for name in ("original_target_safe_reference", "safe_message_reference"):
            if _SAFE_REFERENCE.fullmatch(getattr(self, name)) is None:
                _invalid(f"routing_failure.{name}")
        for name in ("config_version", "policy_version"):
            _nonempty(getattr(self, name), f"routing_failure.{name}")
        if self.index_mutation_sequence is not None and (
            isinstance(self.index_mutation_sequence, bool)
            or not isinstance(self.index_mutation_sequence, int)
            or self.index_mutation_sequence < 0
        ):
            _invalid("routing_failure.index_mutation_sequence")
        expected_outcome = _failure_outcome(self.reason)
        if self.outcome is not expected_outcome:
            _invalid("routing_failure.outcome_reason")
        object.__setattr__(self, "occurred_at", _utc(self.occurred_at))

    def public_error(self) -> Exception:
        details = {
            "component": "routing",
            "reason": self.reason.value,
            "resolution_hint": self.resolution_hint.value,
            "later_action": self.later_action.value,
        }
        if self.reason in {
            RoutingFailureReason.TARGET_REQUIRED,
            RoutingFailureReason.STRATEGY_NOT_PERMITTED,
            RoutingFailureReason.REBIND_NOT_PERMITTED,
            RoutingFailureReason.PREVIOUS_MESSAGE_MISMATCH,
            RoutingFailureReason.PREVIOUS_PLAN_ID_INVALID,
            RoutingFailureReason.PREVIOUS_PLAN_VERSION_INVALID,
            RoutingFailureReason.PREVIOUS_FINGERPRINT_INVALID,
            RoutingFailureReason.PREVIOUS_FINGERPRINT_MISMATCH,
        }:
            return NsRuntimeRouteRejectedError(details=details)
        if self.reason is RoutingFailureReason.TARGET_NOT_FOUND:
            return NsRuntimeTargetNotFoundError(details=details)
        if self.reason in {
            RoutingFailureReason.TENANT_DENIED,
            RoutingFailureReason.AUTHORIZATION_EVIDENCE_MISMATCH,
        }:
            return NsRuntimeIamDeniedError(details=details)
        return NsRuntimeRouteUnavailableError(details=details)


@dataclass(frozen=True, slots=True, kw_only=True)
class SafeRoutingProjection:
    plan_reference: str
    message_reference: str
    decision_fingerprint: str
    strategy: RoutingStrategy
    candidate_count: int
    filtered_count: int
    selected_count: int
    plan_version: int
    index_mutation_sequence: int
    local_hit: bool

    def __post_init__(self) -> None:
        for name in ("plan_reference", "message_reference"):
            if _SAFE_REFERENCE.fullmatch(getattr(self, name)) is None:
                _invalid(f"safe_projection.{name}")


RoutingDecision = ResolvedRoutingPlan | RoutingFailureReport


def safe_target_reference(target: TargetGroup | None) -> str:
    payload = None if target is None else target.to_dict()
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return _digest(canonical)


def _validate_no_parameter_expansion(
    requested: StrategyParameters,
    effective: StrategyParameters,
) -> None:
    for name in ("fanout_count", "subset_size"):
        requested_value = getattr(requested, name)
        effective_value = getattr(effective, name)
        if requested_value is not None and effective_value is not None and effective_value > requested_value:
            _invalid(f"routing_policy_decision.{name}_expanded")
    if requested.required_count != effective.required_count:
        _invalid("routing_policy_decision.required_count_changed")


def _scoring_input_reference(
    *,
    version: str,
    affinity: tuple[str, ...],
    weights: tuple[tuple[str, int], ...],
) -> str:
    canonical = json.dumps(
        {
            "version": version,
            "trusted_affinity_connection_ids": affinity,
            "runtime_policy_static_weights": weights,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _failure_outcome(reason: RoutingFailureReason) -> RoutingFailureOutcome:
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
    }:
        return RoutingFailureOutcome.REJECTED
    return RoutingFailureOutcome.UNAVAILABLE


def _validate_bindings(values: object, name: str) -> None:
    if not isinstance(values, tuple) or not values or any(not isinstance(value, SelectedRoutingBinding) for value in values):
        _invalid(name)
    keys = [
        (value.runtime_id, value.connection_id, value.session_id, value.connection_epoch)
        for value in values
    ]
    if len(keys) != len(set(keys)):
        _invalid(f"{name}.duplicate")


def _previous_context_integrity(
    *,
    plan_id: str,
    plan_version: int,
    message_reference: str,
    decision_fingerprint: str,
    selected_bindings: tuple[SelectedRoutingBinding, ...],
) -> str:
    payload = {
        "plan_id": plan_id,
        "plan_version": plan_version,
        "message_reference": message_reference,
        "decision_fingerprint": decision_fingerprint,
        "selected_bindings": [
            {
                "runtime_id": item.runtime_id,
                "connection_id": item.connection_id,
                "session_id": item.session_id,
                "connection_epoch": item.connection_epoch,
                "tenant_id": item.tenant_id,
                "identity": item.identity_reference.value,
                "required_capabilities": sorted(item.required_capabilities),
                "component_type": item.component_type,
                "binding_rebind_policy": item.binding_rebind_policy.value,
            }
            for item in selected_bindings
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _nonempty(value: object, name: str) -> None:
    if not isinstance(value, str) or not value:
        _invalid(name)


def _unique_strings(values: tuple[str, ...], name: str) -> None:
    if not isinstance(values, tuple) or any(not isinstance(value, str) or not value for value in values) or len(values) != len(set(values)):
        _invalid(name)


def _utc(value: object) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None:
        _invalid("datetime")
    return value.astimezone(timezone.utc)


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Routing value is invalid.",
        details={"component": "routing", "field": field_name},
    )


__all__ = (
    "CandidateEvidence", "CandidateFilterReason", "LaterActionSuggestion",
    "PreviousRoutingPlanContext", "RebindPolicy", "RequestedRoutingIntent",
    "ResolvedRoutingPlan", "ResolutionHint", "RoutingDecision",
    "RoutingFailureOutcome", "RoutingFailureReason", "RoutingFailureReport",
    "RoutingIdentityReference", "RoutingPolicyDecision", "RoutingRequest",
    "RoutingScoringDecision", "RoutingStrategy", "SafeRoutingProjection",
    "SelectedRoutingBinding",
    "StrategyParameters", "safe_target_reference",
)
