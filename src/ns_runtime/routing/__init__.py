# -*- coding: utf-8 -*-
"""RP-1 local routing decision layer; delivery execution is out of scope."""

from .authority import (
    DeterministicTestStrongRoutingPlanAuthority,
    InMemoryRoutingPlanRecorder,
    LocalRoutingConsistencyPolicy,
    NoopRoutingPlanRecorder,
    RoutingConsistencyPolicy,
    RoutingConsistencyRequirement,
    RoutingPlanRecorder,
    StrongRoutingPlanAuthority,
    UnavailableStrongRoutingPlanAuthority,
)
from .integration import LocalRoutingPreparation
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
    SafeRoutingProjection,
    SelectedRoutingBinding,
    StrategyParameters,
)
from .router import (
    FALLBACK_SCORER_SOURCE,
    FALLBACK_SCORER_VERSION,
    LocalRouter,
    RP1_SCHEMA_VERSION,
)


__all__ = (
    "CandidateEvidence",
    "CandidateFilterReason",
    "DeterministicTestStrongRoutingPlanAuthority",
    "FALLBACK_SCORER_SOURCE",
    "FALLBACK_SCORER_VERSION",
    "InMemoryRoutingPlanRecorder",
    "LaterActionSuggestion",
    "LocalRouter",
    "LocalRoutingConsistencyPolicy",
    "LocalRoutingPreparation",
    "NoopRoutingPlanRecorder",
    "PreviousRoutingPlanContext",
    "RP1_SCHEMA_VERSION",
    "RebindPolicy",
    "ResolvedRoutingPlan",
    "ResolutionHint",
    "RoutingConsistencyPolicy",
    "RoutingConsistencyRequirement",
    "RoutingDecision",
    "RoutingFailureReason",
    "RoutingFailureReport",
    "RoutingIdentityReference",
    "RoutingPlanRecorder",
    "RoutingRequest",
    "RoutingStrategy",
    "SafeRoutingProjection",
    "SelectedRoutingBinding",
    "StrategyParameters",
    "StrongRoutingPlanAuthority",
    "UnavailableStrongRoutingPlanAuthority",
)
