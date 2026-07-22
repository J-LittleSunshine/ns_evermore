# -*- coding: utf-8 -*-
"""Immutable RP-1 request, evidence, decision, and safe projection contracts."""

from __future__ import annotations

import hashlib
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
from ns_runtime.protocol import TargetGroup


_SAFE_REFERENCE = re.compile(r"sha256:[0-9a-f]{16}")


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


class RoutingFailureReason(str, Enum):
    POLICY_REJECTED = "policy_rejected"
    TARGET_NOT_FOUND = "target_not_found"
    TENANT_DENIED = "tenant_denied"
    NO_CANDIDATE = "no_candidate"
    DRAINING = "draining"
    RECONNECT_GRACE = "reconnect_grace"
    AUTHORITY_SUSPENDED = "authority_suspended"
    SESSION_EXPIRY_SUSPENDED = "session_expiry_suspended"
    EPOCH_STALE = "epoch_stale"
    LIMIT_EXCEEDED = "limit_exceeded"
    REMOTE_RUNTIME = "remote_runtime"
    AUTHORITY_UNAVAILABLE = "authority_unavailable"
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
    LOCAL_INDEX = "local_index"
    REMOTE_UNAVAILABLE = "remote_unavailable"
    STRONG_AUTHORITY_REQUIRED = "strong_authority_required"


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
class RoutingRequest:
    message_reference: str
    message_type: str
    message_category: str
    target: TargetGroup = field(repr=False)
    effective_tenant_id: str = field(repr=False)
    effective_strategy: RoutingStrategy
    effective_rebind_policy: RebindPolicy
    config_version: str
    policy_version: str
    iam_decision_reference: str = field(repr=False)
    iam_decision_version: str = field(repr=False)
    cross_tenant_authorized: bool = False
    trusted_affinity_connection_ids: tuple[str, ...] = field(
        default=(),
        repr=False,
    )
    runtime_policy_static_weights: tuple[tuple[str, int], ...] = field(
        default=(),
        repr=False,
    )

    def __post_init__(self) -> None:
        for name in (
            "message_type", "message_category",
            "effective_tenant_id", "config_version", "policy_version",
            "iam_decision_reference", "iam_decision_version",
        ):
            _nonempty(getattr(self, name), f"routing_request.{name}")
        if _SAFE_REFERENCE.fullmatch(self.message_reference) is None:
            _invalid("routing_request.message_reference")
        if not isinstance(self.target, TargetGroup):
            _invalid("routing_request.target")
        if not isinstance(self.effective_strategy, RoutingStrategy):
            _invalid("routing_request.effective_strategy")
        if not isinstance(self.effective_rebind_policy, RebindPolicy):
            _invalid("routing_request.effective_rebind_policy")
        if type(self.cross_tenant_authorized) is not bool:
            _invalid("routing_request.cross_tenant_authorized")
        _unique_strings(
            self.trusted_affinity_connection_ids,
            "routing_request.trusted_affinity_connection_ids",
        )
        seen: set[str] = set()
        for connection_id, weight in self.runtime_policy_static_weights:
            _nonempty(connection_id, "routing_request.static_weight.connection_id")
            if connection_id in seen:
                _invalid("routing_request.static_weight.duplicate")
            if isinstance(weight, bool) or not isinstance(weight, int):
                _invalid("routing_request.static_weight.value")
            seen.add(connection_id)

    @classmethod
    def from_target(
        cls,
        *,
        message_reference: str,
        message_type: str,
        message_category: str,
        target: TargetGroup,
        effective_tenant_id: str,
        config_version: str,
        policy_version: str,
        iam_decision_reference: str,
        iam_decision_version: str,
        cross_tenant_authorized: bool = False,
    ) -> "RoutingRequest":
        if not isinstance(target, TargetGroup):
            _invalid("routing_request.target")
        strategy = RoutingStrategy(target.multi_connection_policy or "single")
        if target.rebind_policy is not None:
            rebind = RebindPolicy(target.rebind_policy)
        elif message_category in {"control", "management", "security"}:
            rebind = RebindPolicy.NO_REBIND_FOR_CONTROL
        elif target.kind == "broadcast":
            rebind = RebindPolicy.SAME_TENANT
        else:
            rebind = RebindPolicy.FIXED_CONNECTION
        if message_category in {"control", "management", "security"}:
            if rebind is not RebindPolicy.NO_REBIND_FOR_CONTROL:
                raise NsRuntimeRouteRejectedError(
                    details={
                        "component": "routing",
                        "reason": "control_rebind_policy_forbidden",
                    },
                )
        return cls(
            message_reference=message_reference,
            message_type=message_type,
            message_category=message_category,
            target=target,
            effective_tenant_id=effective_tenant_id,
            effective_strategy=strategy,
            effective_rebind_policy=rebind,
            config_version=config_version,
            policy_version=policy_version,
            iam_decision_reference=iam_decision_reference,
            iam_decision_version=iam_decision_version,
            cross_tenant_authorized=cross_tenant_authorized,
        )


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

    def __post_init__(self) -> None:
        for name in (
            "runtime_id", "connection_id", "session_id", "tenant_id",
            "component_type",
        ):
            _nonempty(getattr(self, name), f"selected_binding.{name}")
        if isinstance(self.connection_epoch, bool) or not isinstance(
            self.connection_epoch,
            int,
        ) or self.connection_epoch < 0:
            _invalid("selected_binding.connection_epoch")
        if not isinstance(self.identity_reference, RoutingIdentityReference):
            _invalid("selected_binding.identity_reference")
        if not isinstance(self.required_capabilities, frozenset):
            _invalid("selected_binding.required_capabilities")
        _unique_strings(
            tuple(self.required_capabilities),
            "selected_binding.required_capabilities",
        )


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
        if isinstance(self.connection_epoch, bool) or not isinstance(
            self.connection_epoch,
            int,
        ) or self.connection_epoch < 0:
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
class StrategyParameters:
    fanout_count: int | None = None
    required_count: int | None = None
    subset_size: int | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class PreviousRoutingPlanContext:
    plan_id: str
    plan_version: int
    selected_bindings: tuple[SelectedRoutingBinding, ...] = field(repr=False)

    def __post_init__(self) -> None:
        _nonempty(self.plan_id, "previous_plan.plan_id")
        if isinstance(self.plan_version, bool) or not isinstance(
            self.plan_version,
            int,
        ) or self.plan_version < 1:
            _invalid("previous_plan.plan_version")
        if not self.selected_bindings or any(
            not isinstance(binding, SelectedRoutingBinding)
            for binding in self.selected_bindings
        ):
            _invalid("previous_plan.selected_bindings")


@dataclass(frozen=True, slots=True, kw_only=True)
class ResolvedRoutingPlan:
    schema_version: str
    plan_id: str = field(repr=False)
    plan_version: int
    previous_plan_id: str | None = field(default=None, repr=False)
    message_reference: str = field(repr=False)
    decision_fingerprint: str
    original_target: TargetGroup = field(repr=False)
    candidates: tuple[CandidateEvidence, ...] = field(repr=False)
    filtered_evidence: tuple[CandidateEvidence, ...] = field(repr=False)
    selected_bindings: tuple[SelectedRoutingBinding, ...] = field(repr=False)
    strategy: RoutingStrategy
    strategy_parameters: StrategyParameters
    effective_rebind_policy: RebindPolicy
    requested_policy_evidence: str
    effective_policy_evidence: str
    config_version: str
    policy_version: str
    scorer_source: str
    scorer_version: str
    iam_decision_reference: str = field(repr=False)
    iam_decision_version: str = field(repr=False)
    index_mutation_sequence: int
    local_hit: bool
    used_stale_route: bool
    created_at: datetime

    def __post_init__(self) -> None:
        for name in (
            "schema_version", "plan_id", "message_reference",
            "decision_fingerprint", "requested_policy_evidence",
            "effective_policy_evidence", "config_version", "policy_version",
            "scorer_source", "scorer_version", "iam_decision_reference",
            "iam_decision_version",
        ):
            _nonempty(getattr(self, name), f"routing_plan.{name}")
        if self.previous_plan_id is not None:
            _nonempty(self.previous_plan_id, "routing_plan.previous_plan_id")
        if isinstance(self.plan_version, bool) or not isinstance(
            self.plan_version,
            int,
        ) or self.plan_version < 1:
            _invalid("routing_plan.plan_version")
        if not isinstance(self.original_target, TargetGroup):
            _invalid("routing_plan.original_target")
        for name, values, value_type in (
            ("candidates", self.candidates, CandidateEvidence),
            ("filtered_evidence", self.filtered_evidence, CandidateEvidence),
            ("selected_bindings", self.selected_bindings, SelectedRoutingBinding),
        ):
            if not isinstance(values, tuple) or any(
                not isinstance(value, value_type) for value in values
            ):
                _invalid(f"routing_plan.{name}")
        if not self.selected_bindings:
            _invalid("routing_plan.selected_bindings")
        if not isinstance(self.strategy, RoutingStrategy):
            _invalid("routing_plan.strategy")
        if not isinstance(self.strategy_parameters, StrategyParameters):
            _invalid("routing_plan.strategy_parameters")
        if not isinstance(self.effective_rebind_policy, RebindPolicy):
            _invalid("routing_plan.effective_rebind_policy")
        if isinstance(self.index_mutation_sequence, bool) or not isinstance(
            self.index_mutation_sequence,
            int,
        ) or self.index_mutation_sequence < 0:
            _invalid("routing_plan.index_mutation_sequence")
        if type(self.local_hit) is not bool or type(self.used_stale_route) is not bool:
            _invalid("routing_plan.flags")
        if self.used_stale_route:
            _invalid("routing_plan.used_stale_route")
        object.__setattr__(self, "created_at", _utc(self.created_at))

    def previous_context(self) -> PreviousRoutingPlanContext:
        return PreviousRoutingPlanContext(
            plan_id=self.plan_id,
            plan_version=self.plan_version,
            selected_bindings=self.selected_bindings,
        )

    def safe_projection(self) -> "SafeRoutingProjection":
        return SafeRoutingProjection(
            plan_reference=_digest(self.plan_id),
            message_reference=self.message_reference,
            decision_fingerprint=self.decision_fingerprint,
            strategy=self.strategy,
            candidate_count=len(self.candidates),
            filtered_count=len(self.filtered_evidence),
            selected_count=len(self.selected_bindings),
            plan_version=self.plan_version,
            index_mutation_sequence=self.index_mutation_sequence,
            local_hit=self.local_hit,
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class RoutingFailureReport:
    reason: RoutingFailureReason
    resolution_hint: ResolutionHint
    later_action: LaterActionSuggestion
    safe_message_reference: str
    index_mutation_sequence: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.reason, RoutingFailureReason):
            _invalid("routing_failure.reason")
        if not isinstance(self.resolution_hint, ResolutionHint):
            _invalid("routing_failure.resolution_hint")
        if not isinstance(self.later_action, LaterActionSuggestion):
            _invalid("routing_failure.later_action")
        if _SAFE_REFERENCE.fullmatch(self.safe_message_reference) is None:
            _invalid("routing_failure.safe_message_reference")

    def public_error(self) -> Exception:
        details = {
            "component": "routing",
            "reason": self.reason.value,
            "resolution_hint": self.resolution_hint.value,
            "later_action": self.later_action.value,
        }
        if self.reason is RoutingFailureReason.POLICY_REJECTED:
            return NsRuntimeRouteRejectedError(details=details)
        if self.reason is RoutingFailureReason.TARGET_NOT_FOUND:
            return NsRuntimeTargetNotFoundError(details=details)
        if self.reason is RoutingFailureReason.TENANT_DENIED:
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


def _digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


def _nonempty(value: object, name: str) -> None:
    if not isinstance(value, str) or not value:
        _invalid(name)


def _unique_strings(values: tuple[str, ...], name: str) -> None:
    if not isinstance(values, tuple) or any(
        not isinstance(value, str) or not value for value in values
    ) or len(values) != len(set(values)):
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
    "CandidateEvidence",
    "CandidateFilterReason",
    "LaterActionSuggestion",
    "PreviousRoutingPlanContext",
    "RebindPolicy",
    "ResolvedRoutingPlan",
    "ResolutionHint",
    "RoutingDecision",
    "RoutingFailureReason",
    "RoutingFailureReport",
    "RoutingIdentityReference",
    "RoutingRequest",
    "RoutingStrategy",
    "SafeRoutingProjection",
    "SelectedRoutingBinding",
    "StrategyParameters",
)
