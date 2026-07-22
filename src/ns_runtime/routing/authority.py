# -*- coding: utf-8 -*-
"""P09 consistency interfaces; no StateStore authority is activated here."""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum

from ns_common.exceptions import NsRuntimeStateStoreUnavailableError, NsValidationError

from .models import ResolvedRoutingPlan, RoutingRequest, SafeRoutingProjection


class RoutingConsistencyRequirement(str, Enum):
    ORDINARY_LOCAL = "ordinary_local"
    STRONG_REQUIRED = "strong_required"


class RoutingConsistencyPolicy(ABC):
    @abstractmethod
    def requirement_for(
        self,
        request: RoutingRequest,
    ) -> RoutingConsistencyRequirement:
        raise NotImplementedError


class LocalRoutingConsistencyPolicy(RoutingConsistencyPolicy):
    def __init__(self, *, strong_message_types: frozenset[str] = frozenset()) -> None:
        if not isinstance(strong_message_types, frozenset) or any(
            not isinstance(value, str) or not value
            for value in strong_message_types
        ):
            _invalid("strong_message_types")
        self._strong_message_types = strong_message_types

    def requirement_for(
        self,
        request: RoutingRequest,
    ) -> RoutingConsistencyRequirement:
        if not isinstance(request, RoutingRequest):
            _invalid("request")
        if request.message_type in self._strong_message_types:
            return RoutingConsistencyRequirement.STRONG_REQUIRED
        return RoutingConsistencyRequirement.ORDINARY_LOCAL


class RoutingPlanRecorder(ABC):
    @abstractmethod
    async def record(self, projection: SafeRoutingProjection) -> None:
        raise NotImplementedError


class NoopRoutingPlanRecorder(RoutingPlanRecorder):
    async def record(self, projection: SafeRoutingProjection) -> None:
        if not isinstance(projection, SafeRoutingProjection):
            _invalid("projection")


class InMemoryRoutingPlanRecorder(RoutingPlanRecorder):
    """Explicit process-local safe projection recorder for tests/diagnostics."""

    def __init__(self) -> None:
        self._projections: list[SafeRoutingProjection] = []

    @property
    def projections(self) -> tuple[SafeRoutingProjection, ...]:
        return tuple(self._projections)

    async def record(self, projection: SafeRoutingProjection) -> None:
        if not isinstance(projection, SafeRoutingProjection):
            _invalid("projection")
        self._projections.append(projection)


class StrongRoutingPlanAuthority(ABC):
    @abstractmethod
    async def commit(self, plan: ResolvedRoutingPlan) -> None:
        raise NotImplementedError


class UnavailableStrongRoutingPlanAuthority(StrongRoutingPlanAuthority):
    """Fail-closed boundary until a future authority is explicitly activated."""

    async def commit(self, plan: ResolvedRoutingPlan) -> None:
        if not isinstance(plan, ResolvedRoutingPlan):
            _invalid("plan")
        raise NsRuntimeStateStoreUnavailableError(
            details={
                "component": "routing_plan_authority",
                "operation": "commit",
                "reason": "strong_routing_plan_persistence_disabled",
            },
        )


class DeterministicTestStrongRoutingPlanAuthority(StrongRoutingPlanAuthority):
    def __init__(self) -> None:
        self._plans: list[ResolvedRoutingPlan] = []
        self.failure: Exception | None = None

    @property
    def plans(self) -> tuple[ResolvedRoutingPlan, ...]:
        return tuple(self._plans)

    async def commit(self, plan: ResolvedRoutingPlan) -> None:
        if not isinstance(plan, ResolvedRoutingPlan):
            _invalid("plan")
        if self.failure is not None:
            raise self.failure
        self._plans.append(plan)


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Routing consistency dependency is invalid.",
        details={"component": "routing", "field": field_name},
    )


__all__ = (
    "DeterministicTestStrongRoutingPlanAuthority",
    "InMemoryRoutingPlanRecorder",
    "LocalRoutingConsistencyPolicy",
    "NoopRoutingPlanRecorder",
    "RoutingConsistencyPolicy",
    "RoutingConsistencyRequirement",
    "RoutingPlanRecorder",
    "StrongRoutingPlanAuthority",
    "UnavailableStrongRoutingPlanAuthority",
)
