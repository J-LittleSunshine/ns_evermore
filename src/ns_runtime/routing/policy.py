# -*- coding: utf-8 -*-
"""Explicit trusted runtime routing-policy authority."""

from __future__ import annotations

from abc import ABC, abstractmethod

from ns_common.exceptions import NsValidationError

from .models import (
    RebindPolicy,
    RoutingFailureReason,
    RoutingPolicyInvocation,
    RoutingPolicyDecision,
    RoutingRiskMetadata,
    RoutingScoringDecision,
    RoutingSecurityOverride,
    RoutingStrategy,
)


class RoutingPolicy(ABC):
    @abstractmethod
    def decide(
        self,
        invocation: RoutingPolicyInvocation,
    ) -> RoutingPolicyDecision:
        raise NotImplementedError


class DefaultLocalRoutingPolicy(RoutingPolicy):
    """Default P09 authority: accept valid local intent or explicitly tighten it."""

    def __init__(
        self,
        *,
        allowed_strategies: frozenset[RoutingStrategy] | None = None,
        allowed_rebind_policies: frozenset[RebindPolicy] | None = None,
    ) -> None:
        self._strategies = (
            frozenset(RoutingStrategy)
            if allowed_strategies is None
            else allowed_strategies
        )
        self._rebind = (
            frozenset(RebindPolicy)
            if allowed_rebind_policies is None
            else allowed_rebind_policies
        )
        if (
            not isinstance(self._strategies, frozenset)
            or not self._strategies
            or any(not isinstance(value, RoutingStrategy) for value in self._strategies)
        ):
            _invalid("policy.allowed_strategies")
        if (
            not isinstance(self._rebind, frozenset)
            or not self._rebind
            or any(not isinstance(value, RebindPolicy) for value in self._rebind)
        ):
            _invalid("policy.allowed_rebind_policies")

    def decide(
        self,
        invocation: RoutingPolicyInvocation,
    ) -> RoutingPolicyDecision:
        if not isinstance(invocation, RoutingPolicyInvocation):
            _invalid("policy.invocation")
        intent = invocation.requested_intent
        risk = RoutingRiskMetadata(
            message_type=invocation.message_type,
            category=invocation.category,
            audit_level=invocation.audit_level,
            security_sensitive=invocation.security_sensitive,
        )
        config_version = invocation.config_version
        policy_version = invocation.policy_version
        if intent.requested_strategy not in self._strategies:
            return self._reject(
                invocation,
                RoutingFailureReason.STRATEGY_NOT_PERMITTED,
            )
        requested_rebind = intent.requested_rebind_policy
        if requested_rebind is not None and requested_rebind not in self._rebind:
            return self._reject(
                invocation,
                RoutingFailureReason.REBIND_NOT_PERMITTED,
            )
        if (
            intent.requested_strategy is RoutingStrategy.BROADCAST
            and risk.security_sensitive
        ):
            return self._reject(
                invocation,
                RoutingFailureReason.REBIND_NOT_PERMITTED,
            )
        if intent.requested_strategy is RoutingStrategy.BROADCAST:
            effective_rebind = RebindPolicy.FIXED_CONNECTION
            override = RoutingSecurityOverride.BROADCAST_FIXED_BINDING
        elif risk.security_sensitive:
            effective_rebind = RebindPolicy.NO_REBIND_FOR_CONTROL
            override = RoutingSecurityOverride.NO_REBIND_FOR_SECURITY
        else:
            effective_rebind = requested_rebind or RebindPolicy.FIXED_CONNECTION
            override = RoutingSecurityOverride.NONE
        if effective_rebind not in self._rebind:
            return self._reject(
                invocation,
                RoutingFailureReason.REBIND_NOT_PERMITTED,
            )
        return RoutingPolicyDecision(
            invocation=invocation,
            invocation_reference=invocation.invocation_reference,
            accepted=True,
            requested_strategy=intent.requested_strategy,
            effective_strategy=intent.requested_strategy,
            requested_rebind_policy=requested_rebind,
            effective_rebind_policy=effective_rebind,
            requested_strategy_parameters=intent.requested_strategy_parameters,
            effective_strategy_parameters=intent.requested_strategy_parameters,
            rejection_reason=None,
            config_version=config_version,
            policy_version=policy_version,
            security_override_evidence=override,
            security_sensitive=risk.security_sensitive,
            scoring_decision=RoutingScoringDecision.empty(),
        )

    @staticmethod
    def _reject(
        invocation: RoutingPolicyInvocation,
        reason: RoutingFailureReason,
    ) -> RoutingPolicyDecision:
        intent = invocation.requested_intent
        return RoutingPolicyDecision(
            invocation=invocation,
            invocation_reference=invocation.invocation_reference,
            accepted=False,
            requested_strategy=intent.requested_strategy,
            effective_strategy=None,
            requested_rebind_policy=intent.requested_rebind_policy,
            effective_rebind_policy=None,
            requested_strategy_parameters=intent.requested_strategy_parameters,
            effective_strategy_parameters=None,
            rejection_reason=reason,
            config_version=invocation.config_version,
            policy_version=invocation.policy_version,
            security_override_evidence=RoutingSecurityOverride.REJECTED,
            security_sensitive=invocation.security_sensitive,
            scoring_decision=RoutingScoringDecision.empty(),
        )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Routing policy value is invalid.",
        details={"component": "routing_policy", "field": field_name},
    )


__all__ = ("DefaultLocalRoutingPolicy", "RoutingPolicy", "RoutingRiskMetadata")
