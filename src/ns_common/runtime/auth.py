# -*- coding: utf-8 -*-
from __future__ import annotations

import hmac
from dataclasses import dataclass
from typing import Any

from ns_common.runtime.config import NsRuntimeConfig


@dataclass(slots=True, frozen=True, kw_only=True)
class NsRuntimeAuthPayload:
    """Runtime bearer auth payload carried in register frame payload."""

    scheme: str = "bearer"
    token: str = ""

    @property
    def normalized_scheme(self) -> str:
        """Return normalized auth scheme."""
        return str(self.scheme or "").strip().lower()

    @property
    def normalized_token(self) -> str:
        """Return normalized auth token."""
        return str(self.token or "").strip()


@dataclass(slots=True, frozen=True, kw_only=True)
class NsRuntimeAuthDecision:
    """Runtime auth decision."""

    accepted: bool
    authenticated: bool = False
    reason: str | None = None
    principal_type: str | None = None
    principal_id: str | None = None


class NsRuntimeTokenAuthenticator:
    """Static bearer token authenticator for runtime WebSocket register frames.

    P11 deliberately uses static bearer tokens only. IAM JWT introspection,
    OAuth/OIDC and fine-grained authorization are deferred.
    """

    def __init__(self, config: NsRuntimeConfig) -> None:
        """Initialize authenticator."""
        self._config = config

    def verify_service_payload(self, payload: dict[str, Any], *, principal_type: str, principal_id: str | None = None) -> NsRuntimeAuthDecision:
        """Verify backend connector or runtime sub-node service token."""
        normalized_principal_type = str(principal_type or "").strip() or "service"
        normalized_principal_id = self._normalize_optional(principal_id)

        if not self._config.auth_enabled:
            return NsRuntimeAuthDecision(
                accepted=True,
                authenticated=False,
                reason="runtime service auth is disabled",
                principal_type=normalized_principal_type,
                principal_id=normalized_principal_id,
            )

        expected_token = str(self._config.service_token or "").strip()
        if not expected_token:
            return NsRuntimeAuthDecision(
                accepted=False,
                authenticated=False,
                reason="runtime service token is not configured",
                principal_type=normalized_principal_type,
                principal_id=normalized_principal_id,
            )

        auth_payload = self.parse_auth_payload(payload)
        if auth_payload.normalized_scheme != "bearer":
            return NsRuntimeAuthDecision(
                accepted=False,
                authenticated=False,
                reason="runtime auth scheme must be bearer",
                principal_type=normalized_principal_type,
                principal_id=normalized_principal_id,
            )

        if not auth_payload.normalized_token:
            return NsRuntimeAuthDecision(
                accepted=False,
                authenticated=False,
                reason="runtime bearer token is required",
                principal_type=normalized_principal_type,
                principal_id=normalized_principal_id,
            )

        if not hmac.compare_digest(auth_payload.normalized_token, expected_token):
            return NsRuntimeAuthDecision(
                accepted=False,
                authenticated=False,
                reason="runtime bearer token is invalid",
                principal_type=normalized_principal_type,
                principal_id=normalized_principal_id,
            )

        return NsRuntimeAuthDecision(
            accepted=True,
            authenticated=True,
            reason="runtime service token accepted",
            principal_type=normalized_principal_type,
            principal_id=normalized_principal_id,
        )

    def verify_frontend_payload(self, payload: dict[str, Any]) -> NsRuntimeAuthDecision:
        """Verify frontend register token.

        When frontend auth is disabled, frontend registration remains backward
        compatible. When enabled, anonymous frontend can still be allowed by
        configuration for mixed public/private realtime scenarios.
        """
        client_id = self._normalize_optional(payload.get("client_id"))
        user_id = self._normalize_optional(payload.get("user_id"))

        if not self._config.frontend_auth_enabled:
            return NsRuntimeAuthDecision(
                accepted=True,
                authenticated=False,
                reason="runtime frontend auth is disabled",
                principal_type="frontend",
                principal_id=user_id or client_id,
            )

        auth_payload = self.parse_auth_payload(payload)
        if not auth_payload.normalized_token:
            if self._config.allow_anonymous_frontend:
                return NsRuntimeAuthDecision(
                    accepted=True,
                    authenticated=False,
                    reason="anonymous frontend is allowed",
                    principal_type="frontend",
                    principal_id=client_id,
                )

            return NsRuntimeAuthDecision(
                accepted=False,
                authenticated=False,
                reason="runtime frontend bearer token is required",
                principal_type="frontend",
                principal_id=client_id,
            )

        if auth_payload.normalized_scheme != "bearer":
            return NsRuntimeAuthDecision(
                accepted=False,
                authenticated=False,
                reason="runtime frontend auth scheme must be bearer",
                principal_type="frontend",
                principal_id=client_id,
            )

        expected_token = str(self._config.frontend_static_token or "").strip()
        if not expected_token:
            return NsRuntimeAuthDecision(
                accepted=False,
                authenticated=False,
                reason="runtime frontend static token is not configured",
                principal_type="frontend",
                principal_id=client_id,
            )

        if not hmac.compare_digest(auth_payload.normalized_token, expected_token):
            return NsRuntimeAuthDecision(
                accepted=False,
                authenticated=False,
                reason="runtime frontend bearer token is invalid",
                principal_type="frontend",
                principal_id=client_id,
            )

        return NsRuntimeAuthDecision(
            accepted=True,
            authenticated=True,
            reason="runtime frontend token accepted",
            principal_type="frontend",
            principal_id=user_id or client_id,
        )

    @classmethod
    def parse_auth_payload(cls, payload: dict[str, Any]) -> NsRuntimeAuthPayload:
        """Parse auth object from runtime register payload."""
        if not isinstance(payload, dict):
            return NsRuntimeAuthPayload()

        auth_raw = payload.get("auth") or {}
        if isinstance(auth_raw, dict):
            return NsRuntimeAuthPayload(
                scheme=str(auth_raw.get("scheme") or "bearer"),
                token=str(auth_raw.get("token") or ""),
            )

        token = cls._normalize_optional(payload.get("token"))
        if token:
            return NsRuntimeAuthPayload(token=token)

        return NsRuntimeAuthPayload()

    @staticmethod
    def _normalize_optional(value: Any) -> str | None:
        """Normalize optional string."""
        if value is None:
            return None

        normalized = str(value).strip()
        return normalized or None
