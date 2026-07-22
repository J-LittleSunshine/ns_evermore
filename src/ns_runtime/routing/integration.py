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
    ProcessorContext,
    ProcessorSafeSummary,
    RoutingPreparation,
    RoutingPreparationResult,
)
from ns_runtime.protocol import (
    BUILTIN_MESSAGE_REGISTRY,
    MessageTypeRegistry,
    RoutingRequirement,
)

from .models import (
    LaterActionSuggestion,
    ResolvedRoutingPlan,
    ResolutionHint,
    RoutingFailureReason,
    RoutingFailureReport,
    RoutingRequest,
)
from .router import LocalRouter


class LocalRoutingPreparation(RoutingPreparation):
    def __init__(
        self,
        *,
        router: LocalRouter,
        protocol_registry: MessageTypeRegistry = BUILTIN_MESSAGE_REGISTRY,
    ) -> None:
        if not isinstance(router, LocalRouter):
            _invalid("router")
        if not isinstance(protocol_registry, MessageTypeRegistry):
            _invalid("protocol_registry")
        self._router = router
        self._registry = protocol_registry

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
        target = context.envelope.target
        if target is None:
            failure = RoutingFailureReport(
                reason=RoutingFailureReason.POLICY_REJECTED,
                resolution_hint=ResolutionHint.LOCAL_INDEX,
                later_action=LaterActionSuggestion.SUBMIT_CORRECTED_TARGET,
                safe_message_reference=(
                    ProcessorSafeSummary.from_envelope(context.envelope)
                    .object_reference
                ),
            )
            return RoutingPreparationResult.rejected(failure)
        target_tenant = target.tenant_id
        crosses_tenant = (
            target_tenant is not None
            and target_tenant != context.session.tenant_id
        )
        try:
            request = RoutingRequest.from_target(
                message_reference=(
                    ProcessorSafeSummary.from_envelope(context.envelope)
                    .object_reference
                ),
                message_type=contract.message_type,
                message_category=contract.category.value,
                target=target,
                effective_tenant_id=(
                    target_tenant if crosses_tenant else context.session.tenant_id
                ),
                config_version=context.config_version,
                policy_version=context.policy_version,
                iam_decision_reference=context.session.permission_snapshot_ref,
                iam_decision_version=context.session.permission_version,
                cross_tenant_authorized=crosses_tenant,
            )
        except NsRuntimeRouteRejectedError as error:
            return RoutingPreparationResult.rejected(
                _public_failure_from_error(context, error),
            )
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


def _public_failure_from_error(
    context: ProcessorContext,
    error: NsRuntimeRouteRejectedError,
) -> RoutingFailureReport:
    return RoutingFailureReport(
        reason=RoutingFailureReason.POLICY_REJECTED,
        resolution_hint=ResolutionHint.LOCAL_INDEX,
        later_action=LaterActionSuggestion.SUBMIT_CORRECTED_TARGET,
        safe_message_reference=(
            ProcessorSafeSummary.from_envelope(context.envelope).object_reference
        ),
    )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Routing preparation dependency is invalid.",
        details={"component": "routing", "field": field_name},
    )


__all__ = ("LocalRoutingPreparation",)
