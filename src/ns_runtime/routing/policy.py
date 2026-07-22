# -*- coding: utf-8 -*-
"""Explicit trusted runtime routing-policy authority."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ns_common.exceptions import NsValidationError
from ns_runtime.protocol import MessageAuditLevel, MessageCategory, MessageTypeContract

from .models import (
    RebindPolicy,
    RequestedRoutingIntent,
    RoutingFailureReason,
    RoutingPolicyDecision,
    RoutingScoringDecision,
    RoutingStrategy,
)


@dataclass(frozen=True, slots=True, kw_only=True)
class RoutingRiskMetadata:
    message_type: str
    category: MessageCategory
    audit_level: MessageAuditLevel
    security_sensitive: bool

    def __post_init__(self) -> None:
        if not isinstance(self.message_type, str) or not self.message_type:
            _invalid("risk.message_type")
        if not isinstance(self.category, MessageCategory):
            _invalid("risk.category")
        if not isinstance(self.audit_level, MessageAuditLevel):
            _invalid("risk.audit_level")
        if type(self.security_sensitive) is not bool:
            _invalid("risk.security_sensitive")
        if (
            self.category in {
                MessageCategory.CONTROL,
                MessageCategory.MANAGEMENT,
                MessageCategory.CONFIG,
                MessageCategory.CLUSTER,
            }
            or self.audit_level is MessageAuditLevel.SECURITY
        ) and not self.security_sensitive:
            _invalid("risk.security_sensitive_required")

    @classmethod
    def from_contract(cls, contract: MessageTypeContract) -> "RoutingRiskMetadata":
        if not isinstance(contract, MessageTypeContract):
            _invalid("risk.contract")
        sensitive = (
            contract.category in {
                MessageCategory.CONTROL,
                MessageCategory.MANAGEMENT,
                MessageCategory.CONFIG,
                MessageCategory.CLUSTER,
            }
            or contract.audit_level is MessageAuditLevel.SECURITY
            or "runtime.management" in contract.required_capabilities
        )
        return cls(
            message_type=contract.message_type,
            category=contract.category,
            audit_level=contract.audit_level,
            security_sensitive=sensitive,
        )


class RoutingPolicy(ABC):
    @abstractmethod
    def decide(
        self,
        intent: RequestedRoutingIntent,
        *,
        risk: RoutingRiskMetadata,
        config_version: str,
        policy_version: str,
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
        intent: RequestedRoutingIntent,
        *,
        risk: RoutingRiskMetadata,
        config_version: str,
        policy_version: str,
    ) -> RoutingPolicyDecision:
        if not isinstance(intent, RequestedRoutingIntent):
            _invalid("policy.intent")
        if not isinstance(risk, RoutingRiskMetadata):
            _invalid("policy.risk")
        for value, name in (
            (config_version, "policy.config_version"),
            (policy_version, "policy.policy_version"),
        ):
            if not isinstance(value, str) or not value:
                _invalid(name)
        if intent.requested_strategy not in self._strategies:
            return self._reject(intent, RoutingFailureReason.STRATEGY_NOT_PERMITTED, risk, config_version, policy_version)
        requested_rebind = intent.requested_rebind_policy
        if requested_rebind is not None and requested_rebind not in self._rebind:
            return self._reject(intent, RoutingFailureReason.REBIND_NOT_PERMITTED, risk, config_version, policy_version)
        if (
            intent.requested_strategy is RoutingStrategy.BROADCAST
            and risk.security_sensitive
        ):
            return self._reject(
                intent,
                RoutingFailureReason.REBIND_NOT_PERMITTED,
                risk,
                config_version,
                policy_version,
            )
        if intent.requested_strategy is RoutingStrategy.BROADCAST:
            effective_rebind = RebindPolicy.FIXED_CONNECTION
            override = "trusted_contract:broadcast_fixed_binding"
        elif risk.security_sensitive:
            effective_rebind = RebindPolicy.NO_REBIND_FOR_CONTROL
            override = f"trusted_contract:{risk.message_type}:{risk.category.value}:{risk.audit_level.value}:no_rebind_for_control"
        else:
            effective_rebind = requested_rebind or RebindPolicy.FIXED_CONNECTION
            override = "trusted_contract:no_security_override"
        if effective_rebind not in self._rebind:
            return self._reject(intent, RoutingFailureReason.REBIND_NOT_PERMITTED, risk, config_version, policy_version)
        return RoutingPolicyDecision(
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
    def _reject(intent, reason, risk, config_version, policy_version) -> RoutingPolicyDecision:
        return RoutingPolicyDecision(
            accepted=False,
            requested_strategy=intent.requested_strategy,
            effective_strategy=None,
            requested_rebind_policy=intent.requested_rebind_policy,
            effective_rebind_policy=None,
            requested_strategy_parameters=intent.requested_strategy_parameters,
            effective_strategy_parameters=None,
            rejection_reason=reason,
            config_version=config_version,
            policy_version=policy_version,
            security_override_evidence=f"trusted_contract:{risk.message_type}:{risk.category.value}:rejected",
            security_sensitive=risk.security_sensitive,
            scoring_decision=RoutingScoringDecision.empty(),
        )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Routing policy value is invalid.",
        details={"component": "routing_policy", "field": field_name},
    )


__all__ = ("DefaultLocalRoutingPolicy", "RoutingPolicy", "RoutingRiskMetadata")
