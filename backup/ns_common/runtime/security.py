# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass(slots=True, frozen=True, kw_only=True)
class NsRuntimePrincipal:
    """Authenticated runtime principal.

    This contract is shared by ns_runtime and ns_backend IAM integration.
    It does not depend on Django ORM.
    """

    principal_type: str
    principal_id: str

    authenticated: bool = False
    display_name: str | None = None

    user_id: str | None = None
    service_id: str | None = None
    backend_id: str | None = None
    node_id: str | None = None
    client_id: str | None = None
    session_id: str | None = None

    claims: dict[str, Any] = field(default_factory=dict)
    expires_at_epoch_ms: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize runtime principal."""
        return {
            "principal_type": self.principal_type,
            "principal_id": self.principal_id,
            "authenticated": bool(self.authenticated),
            "display_name": self.display_name,
            "user_id": self.user_id,
            "service_id": self.service_id,
            "backend_id": self.backend_id,
            "node_id": self.node_id,
            "client_id": self.client_id,
            "session_id": self.session_id,
            "claims": dict(self.claims),
            "expires_at_epoch_ms": self.expires_at_epoch_ms,
        }


@dataclass(slots=True, frozen=True, kw_only=True)
class NsRuntimeAuthorizationRequest:
    """Runtime authorization request.

    The request maps one runtime action to one IAM resource/action decision.
    """

    principal: NsRuntimePrincipal
    resource_type: str
    resource_id: str
    action_code: str

    permission_code: str | None = None
    context: dict[str, Any] = field(default_factory=dict)
    trace_id: str | None = None

    def to_iam_payload(self) -> dict[str, Any]:
        """Serialize request into IAM AuthorizeService.check-compatible payload."""
        payload: dict[str, Any] = {
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action_code": self.action_code,
            "context": {
                **dict(self.context),
                "principal": self.principal.to_dict(),
            },
        }

        if self.permission_code:
            payload["permission_code"] = self.permission_code

        return payload

    def to_dict(self) -> dict[str, Any]:
        """Serialize runtime authorization request."""
        return {
            "principal": self.principal.to_dict(),
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action_code": self.action_code,
            "permission_code": self.permission_code,
            "context": dict(self.context),
            "trace_id": self.trace_id,
        }


@dataclass(slots=True, frozen=True, kw_only=True)
class NsRuntimeAuthorizationDecision:
    """Runtime authorization decision."""

    allowed: bool
    reason: str
    effect: str = "allow"

    resource_type: str | None = None
    resource_id: str | None = None
    action_code: str | None = None
    permission_code: str | None = None

    matched_source: str | None = None
    hit_details: dict[str, Any] = field(default_factory=dict)
    decision_chain: list[dict[str, Any]] = field(default_factory=list)
    raw_decision: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def allow(
            cls,
            *,
            reason: str = "ALLOW",
            resource_type: str | None = None,
            resource_id: str | None = None,
            action_code: str | None = None,
            permission_code: str | None = None,
            matched_source: str | None = None,
            raw_decision: dict[str, Any] | None = None,
    ) -> "NsRuntimeAuthorizationDecision":
        """Build allow decision."""
        return cls(
            allowed=True,
            effect="allow",
            reason=reason,
            resource_type=resource_type,
            resource_id=resource_id,
            action_code=action_code,
            permission_code=permission_code,
            matched_source=matched_source,
            raw_decision=dict(raw_decision or {}),
        )

    @classmethod
    def deny(
            cls,
            *,
            reason: str,
            resource_type: str | None = None,
            resource_id: str | None = None,
            action_code: str | None = None,
            permission_code: str | None = None,
            matched_source: str | None = None,
            raw_decision: dict[str, Any] | None = None,
    ) -> "NsRuntimeAuthorizationDecision":
        """Build deny decision."""
        return cls(
            allowed=False,
            effect="deny",
            reason=reason,
            resource_type=resource_type,
            resource_id=resource_id,
            action_code=action_code,
            permission_code=permission_code,
            matched_source=matched_source,
            raw_decision=dict(raw_decision or {}),
        )

    @classmethod
    def from_iam_decision(
            cls,
            iam_decision: dict[str, Any],
            *,
            resource_type: str | None = None,
            resource_id: str | None = None,
            action_code: str | None = None,
            permission_code: str | None = None,
    ) -> "NsRuntimeAuthorizationDecision":
        """Build runtime decision from IAM AuthorizeService decision payload."""
        allowed = bool(iam_decision.get("allowed"))
        return cls(
            allowed=allowed,
            effect="allow" if allowed else "deny",
            reason=str(iam_decision.get("reason") or ("ALLOW" if allowed else "DENY")),
            resource_type=resource_type,
            resource_id=resource_id,
            action_code=action_code,
            permission_code=permission_code,
            matched_source=str(iam_decision.get("matched_source")).strip() if iam_decision.get("matched_source") is not None else None,
            hit_details=dict(iam_decision.get("hit_details") or {}),
            decision_chain=list(iam_decision.get("decision_chain") or []),
            raw_decision=dict(iam_decision),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize runtime authorization decision."""
        return {
            "allowed": bool(self.allowed),
            "effect": self.effect,
            "reason": self.reason,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action_code": self.action_code,
            "permission_code": self.permission_code,
            "matched_source": self.matched_source,
            "hit_details": dict(self.hit_details),
            "decision_chain": list(self.decision_chain),
            "raw_decision": dict(self.raw_decision),
        }


class NsRuntimeAuthProvider(Protocol):
    """Runtime authentication and authorization provider contract.

    Implementations:
    - static provider: local bearer token only
    - remote IAM provider: call ns_backend IAM internal API
    """

    async def authenticate_frontend(self, payload: dict[str, Any], *, trace_id: str | None = None) -> NsRuntimePrincipal:
        """Authenticate frontend register payload."""

    async def authenticate_service(self, payload: dict[str, Any], *, principal_type: str, trace_id: str | None = None) -> NsRuntimePrincipal:
        """Authenticate backend connector or runtime node register payload."""

    async def authorize(self, request: NsRuntimeAuthorizationRequest) -> NsRuntimeAuthorizationDecision:
        """Authorize one runtime action."""

    async def batch_authorize(self, requests: list[NsRuntimeAuthorizationRequest]) -> list[NsRuntimeAuthorizationDecision]:
        """Authorize multiple runtime actions."""
