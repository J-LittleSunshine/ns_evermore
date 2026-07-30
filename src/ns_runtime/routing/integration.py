# -*- coding: utf-8 -*-
"""PC-1 stage-six adapter for the local RP-1 Router."""

from __future__ import annotations

from ns_common.exceptions import (
    NsRuntimeIamDeniedError,
    NsRuntimeRouteRejectedError,
    NsRuntimeTargetNotFoundError,
    NsValidationError,
)
from ns_runtime.processor import (
    AuthorizationDecisionOutcome,
    AuthorizationDecisionEvidence,
    ProcessorContext,
    ProcessorSafeSummary,
    RoutingPreparation,
    RoutingPreparationResult,
)
from ns_runtime.protocol import (
    BUILTIN_MESSAGE_REGISTRY,
    MessageTypeRegistry,
    RoutingRequirement,
    TargetGroup,
)

from .models import (
    LaterActionSuggestion,
    RequestedRoutingIntent,
    ResolvedRoutingPlan,
    ResolutionHint,
    RoutingFailureReason,
    RoutingFailureOutcome,
    RoutingFailureReport,
    RoutingPolicyDecision,
    RoutingPolicyInvocation,
    RoutingRequest,
    safe_target_reference,
)
from .policy import DefaultLocalRoutingPolicy, RoutingPolicy
from .router import LocalRouter


class LocalRoutingPreparation(RoutingPreparation):
    def __init__(
        self,
        *,
        router: LocalRouter,
        policy: RoutingPolicy | None = None,
        protocol_registry: MessageTypeRegistry = BUILTIN_MESSAGE_REGISTRY,
    ) -> None:
        if not isinstance(router, LocalRouter):
            _invalid("router")
        if not isinstance(protocol_registry, MessageTypeRegistry):
            _invalid("protocol_registry")
        self._router = router
        self._registry = protocol_registry
        self._policy = DefaultLocalRoutingPolicy() if policy is None else policy
        if not isinstance(self._policy, RoutingPolicy):
            _invalid("policy")

    async def prepare(
        self,
        context: ProcessorContext,
        value: object,
    ) -> RoutingPreparationResult:
        if not isinstance(context, ProcessorContext):
            _invalid("context")
        contract = self._registry.require(context.envelope.message.type)
        # Feature-disabled messages must not reveal whether their target exists.
        if not contract.feature_enabled:
            return RoutingPreparationResult.no_routing_required()
        if contract.routing_requirement is RoutingRequirement.NONE:
            return RoutingPreparationResult.no_routing_required()
        message_reference = ProcessorSafeSummary.from_envelope(
            context.envelope,
        ).object_reference
        target = context.envelope.target
        if target is None:
            return RoutingPreparationResult.rejected(
                _failure(
                    context,
                    reason=RoutingFailureReason.TARGET_REQUIRED,
                    message_reference=message_reference,
                    target=None,
                ),
            )
        if not isinstance(value, AuthorizationDecisionEvidence):
            return RoutingPreparationResult.rejected(_failure(
                context,
                reason=RoutingFailureReason.AUTHORIZATION_EVIDENCE_MISMATCH,
                message_reference=message_reference,
                target=target,
            ))
        expected_target_reference = AuthorizationDecisionEvidence.target_reference(
            target,
            session_tenant_id=context.session.tenant_id,
        )
        target_tenant = target.tenant_id
        crosses_tenant = (
            target_tenant is not None
            and target_tenant != context.session.tenant_id
        )
        if (
            value.message_reference != message_reference
            or value.message_type != contract.message_type
            or value.config_version != context.config_version
            or value.policy_version != context.policy_version
            or value.principal_tenant_id != context.session.tenant_id
            or value.session_permission_snapshot_ref
            != context.session.permission_snapshot_ref
            or value.session_permission_snapshot_version
            != context.session.permission_version
            or value.effective_permission_snapshot_ref
            != value.session_permission_snapshot_ref
            or value.authorized_target_reference != expected_target_reference
            or value.cross_tenant_authorized is not crosses_tenant
            or value.effective_tenant_id
            != (target_tenant if crosses_tenant else context.session.tenant_id)
            or value.decision_outcome is not AuthorizationDecisionOutcome.ALLOW
            or not value.has_valid_binding()
        ):
            return RoutingPreparationResult.rejected(_failure(
                context,
                reason=RoutingFailureReason.AUTHORIZATION_EVIDENCE_MISMATCH,
                message_reference=message_reference,
                target=target,
            ))
        intent = RequestedRoutingIntent.from_target(target)
        invocation = RoutingPolicyInvocation.from_contract(
            contract=contract,
            requested_intent=intent,
            config_version=context.config_version,
            policy_version=context.policy_version,
        )
        try:
            policy_decision = self._policy.decide(invocation)
        except NsValidationError:
            return RoutingPreparationResult.rejected(_failure(
                context,
                reason=RoutingFailureReason.POLICY_DECISION_MISMATCH,
                message_reference=message_reference,
                target=target,
            ))
        if (
            not isinstance(policy_decision, RoutingPolicyDecision)
            or policy_decision.invocation != invocation
            or policy_decision.invocation_reference
            != invocation.invocation_reference
        ):
            return RoutingPreparationResult.rejected(_failure(
                context,
                reason=RoutingFailureReason.POLICY_DECISION_MISMATCH,
                message_reference=message_reference,
                target=target,
            ))
        if not policy_decision.accepted:
            assert policy_decision.rejection_reason is not None
            return RoutingPreparationResult.rejected(_failure(
                context,
                reason=policy_decision.rejection_reason,
                message_reference=message_reference,
                target=target,
            ))
        try:
            request = RoutingRequest(
                message_reference=message_reference,
                message_type=contract.message_type,
                target=target,
                requested_intent=intent,
                policy_decision=policy_decision,
                authorization_evidence=value,
            )
        except NsValidationError:
            return RoutingPreparationResult.rejected(_failure(
                context,
                reason=RoutingFailureReason.POLICY_DECISION_MISMATCH,
                message_reference=message_reference,
                target=target,
            ))
        decision = await self._router.route(request)
        if isinstance(decision, ResolvedRoutingPlan):
            return RoutingPreparationResult.resolved(decision)
        if not isinstance(decision, RoutingFailureReport):
            _invalid("decision")
        error = decision.public_error()
        if isinstance(error, NsRuntimeRouteRejectedError):
            return RoutingPreparationResult.rejected(decision)
        if isinstance(error, (NsRuntimeTargetNotFoundError, NsRuntimeIamDeniedError)):
            return RoutingPreparationResult.rejected(decision)
        return RoutingPreparationResult.unavailable(decision)


def _failure(
    context: ProcessorContext,
    *,
    reason: RoutingFailureReason,
    message_reference: str,
    target: TargetGroup | None,
) -> RoutingFailureReport:
    return RoutingFailureReport(
        outcome=RoutingFailureOutcome.REJECTED,
        reason=reason,
        original_target_safe_reference=safe_target_reference(target),
        safe_message_reference=message_reference,
        config_version=context.config_version,
        policy_version=context.policy_version,
        index_mutation_sequence=None,
        resolution_hint=ResolutionHint.LOCAL,
        later_action=LaterActionSuggestion.SUBMIT_CORRECTED_TARGET,
        occurred_at=context.clock.utc_now(),
    )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Routing preparation dependency is invalid.",
        details={"component": "routing", "field": field_name},
    )


__all__ = ("LocalRoutingPreparation",)
