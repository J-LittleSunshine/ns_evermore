# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from ns_common.http_client import (
    NsHttpClientError,
    NsHttpResponseDecodeError,
    NsHttpStatusError,
    get_http_client,
)
from ns_common.runtime.auth import NsRuntimeAuthDecision, NsRuntimeTokenAuthenticator
from ns_common.runtime.config import NsRuntimeConfig
from ns_common.runtime.errors import NsRuntimeConfigurationError, NsRuntimeError
from ns_common.runtime.permissions import (
    RUNTIME_PRINCIPAL_ANONYMOUS_FRONTEND,
    RUNTIME_PRINCIPAL_BACKEND_SERVICE,
    RUNTIME_PRINCIPAL_FRONTEND_USER,
    RUNTIME_PRINCIPAL_RUNTIME_NODE,
)
from ns_common.runtime.security import (NsRuntimeAuthProvider, NsRuntimeAuthorizationDecision, NsRuntimeAuthorizationRequest, NsRuntimePrincipal)


class NsRuntimeAuthProviderError(NsRuntimeError):
    """Raised when runtime auth provider cannot authenticate or authorize."""


class NsRuntimeStaticAuthProvider:
    """Static runtime auth provider adapter.

    This class adapts the existing P11 static bearer token authenticator to the
    P11.5 NsRuntimeAuthProvider protocol. It intentionally allows authorization
    decisions because static mode preserves the current behavior until P11.8
    explicitly enforces runtime authorization.
    """

    def __init__(self, config: NsRuntimeConfig) -> None:
        """Initialize static runtime auth provider."""
        self._config = config
        self._authenticator = NsRuntimeTokenAuthenticator(config)

    async def authenticate_frontend(self, payload: dict[str, Any], *, trace_id: str | None = None) -> NsRuntimePrincipal:
        """Authenticate frontend register payload by static frontend token."""
        _ = trace_id

        decision: NsRuntimeAuthDecision = self._authenticator.verify_frontend_payload(payload)
        if not decision.accepted:
            raise NsRuntimeAuthProviderError(decision.reason or "runtime frontend authentication failed")

        return self._principal_from_frontend_decision(payload=payload, decision=decision)

    async def authenticate_service(self, payload: dict[str, Any], *, principal_type: str, trace_id: str | None = None) -> NsRuntimePrincipal:
        """Authenticate backend connector or runtime node by static service token."""
        _ = trace_id

        normalized_principal_type = _normalize_service_principal_type(principal_type)
        principal_id = _resolve_service_principal_id(payload=payload, principal_type=normalized_principal_type)

        decision: NsRuntimeAuthDecision = self._authenticator.verify_service_payload(
            payload,
            principal_type=normalized_principal_type,
            principal_id=principal_id,
        )
        if not decision.accepted:
            raise NsRuntimeAuthProviderError(decision.reason or "runtime service authentication failed")

        return self._principal_from_service_decision(
            payload=payload,
            decision=decision,
            principal_type=normalized_principal_type,
        )

    async def authorize(self, request: NsRuntimeAuthorizationRequest) -> NsRuntimeAuthorizationDecision:
        """Allow runtime action in static provider mode."""
        return NsRuntimeAuthorizationDecision.allow(
            reason="STATIC_RUNTIME_AUTH_PROVIDER_ALLOW",
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            action_code=request.action_code,
            permission_code=request.permission_code,
            matched_source="runtime_static_auth_provider",
        )

    async def batch_authorize(self, requests: list[NsRuntimeAuthorizationRequest]) -> list[NsRuntimeAuthorizationDecision]:
        """Allow multiple runtime actions in static provider mode."""
        results: list[NsRuntimeAuthorizationDecision] = []
        for request in requests:
            results.append(await self.authorize(request))
        return results

    @staticmethod
    def _principal_from_frontend_decision(*, payload: dict[str, Any], decision: NsRuntimeAuthDecision) -> NsRuntimePrincipal:
        """Build frontend principal from static auth decision."""
        client_id = _normalize_optional(payload.get("client_id"))
        session_id = _normalize_optional(payload.get("session_id"))
        user_id = _normalize_optional(payload.get("user_id"))
        principal_id = _normalize_optional(decision.principal_id) or user_id or client_id or "anonymous"

        if decision.authenticated:
            return NsRuntimePrincipal(
                principal_type=RUNTIME_PRINCIPAL_FRONTEND_USER,
                principal_id=principal_id,
                authenticated=True,
                display_name=principal_id,
                user_id=user_id or principal_id,
                client_id=client_id,
                session_id=session_id,
                claims={
                    "runtime_static_auth": True,
                },
            )

        return NsRuntimePrincipal(
            principal_type=RUNTIME_PRINCIPAL_ANONYMOUS_FRONTEND,
            principal_id=client_id or principal_id,
            authenticated=False,
            display_name="anonymous",
            client_id=client_id,
            session_id=session_id,
            claims={
                "runtime_static_auth": True,
            },
        )

    @staticmethod
    def _principal_from_service_decision(*, payload: dict[str, Any], decision: NsRuntimeAuthDecision, principal_type: str) -> NsRuntimePrincipal:
        """Build backend service or runtime node principal from static auth decision."""
        _ = payload

        principal_id = _normalize_optional(decision.principal_id) or "service:*"
        service_id = principal_id if principal_type == RUNTIME_PRINCIPAL_BACKEND_SERVICE else None
        backend_id = principal_id if principal_type == RUNTIME_PRINCIPAL_BACKEND_SERVICE else None
        node_id = principal_id if principal_type == RUNTIME_PRINCIPAL_RUNTIME_NODE else None

        return NsRuntimePrincipal(
            principal_type=principal_type,
            principal_id=principal_id,
            authenticated=bool(decision.authenticated),
            display_name=principal_id,
            service_id=service_id,
            backend_id=backend_id,
            node_id=node_id,
            claims={
                "runtime_static_auth": True,
            },
        )


class NsRuntimeRemoteIamAuthProvider:
    """Remote IAM auth provider for ns_runtime.

    This provider calls ns_backend IAM internal HTTP API through ns_common's
    process-wide HTTP client. It must not import Django, ns_backend.iam services,
    repositories, or ORM models directly.
    """

    def __init__(self, config: NsRuntimeConfig) -> None:
        """Initialize remote IAM auth provider."""
        self._config = config
        self._static_provider = NsRuntimeStaticAuthProvider(config)
        self._validate_config()

    async def authenticate_frontend(self, payload: dict[str, Any], *, trace_id: str | None = None) -> NsRuntimePrincipal:
        """Authenticate frontend register payload through IAM token introspection."""
        if not self._config.frontend_auth_enabled:
            return self._anonymous_frontend_principal(payload)

        auth_payload = NsRuntimeTokenAuthenticator.parse_auth_payload(payload)
        if not auth_payload.normalized_token:
            if self._config.allow_anonymous_frontend:
                return self._anonymous_frontend_principal(payload)
            raise NsRuntimeAuthProviderError("runtime frontend bearer token is required")

        if auth_payload.normalized_scheme != "bearer":
            raise NsRuntimeAuthProviderError("runtime frontend auth scheme must be bearer")

        response_data = await self._post_json(
            "introspect-token",
            {
                "token": auth_payload.normalized_token,
                "token_type": "access",
                "client_id": _normalize_optional(payload.get("client_id")),
                "session_id": _normalize_optional(payload.get("session_id")),
            },
            trace_id=trace_id,
        )

        if not bool(response_data.get("active")):
            reason = str(response_data.get("reason") or "TOKEN_INVALID_OR_EXPIRED")
            raise NsRuntimeAuthProviderError(reason)

        principal_payload = response_data.get("principal")
        if not isinstance(principal_payload, dict):
            raise NsRuntimeAuthProviderError("runtime IAM introspection response principal is invalid")

        return self._principal_from_payload(principal_payload)

    async def authenticate_service(self, payload: dict[str, Any], *, principal_type: str, trace_id: str | None = None) -> NsRuntimePrincipal:
        """Authenticate backend connector or runtime node.

        P11.6 IAM internal API currently supports frontend token introspection
        and frontend_user authorization. Service-node authentication therefore
        remains static-token based in P11.7. Service authorization is deferred to
        P11.8+.
        """
        return await self._static_provider.authenticate_service(
            payload,
            principal_type=principal_type,
            trace_id=trace_id,
        )

    async def authorize(self, request: NsRuntimeAuthorizationRequest) -> NsRuntimeAuthorizationDecision:
        """Authorize one runtime action through IAM internal API."""
        response_data = await self._post_json("authorize", request.to_dict(), trace_id=request.trace_id)
        return self._decision_from_payload(response_data, request=request)

    async def batch_authorize(self, requests: list[NsRuntimeAuthorizationRequest]) -> list[NsRuntimeAuthorizationDecision]:
        """Authorize multiple runtime actions through IAM internal API."""
        if not requests:
            return []

        response_data = await self._post_json(
            "batch-authorize",
            {
                "items": [
                    request.to_dict()
                    for request in requests
                ],
            },
            trace_id=requests[0].trace_id,
        )

        raw_results = response_data.get("results")
        if not isinstance(raw_results, list):
            raise NsRuntimeAuthProviderError("runtime IAM batch authorization response results is invalid")

        decisions: list[NsRuntimeAuthorizationDecision] = []
        for index, request in enumerate(requests):
            if index >= len(raw_results):
                decisions.append(
                    NsRuntimeAuthorizationDecision.deny(
                        reason="RUNTIME_IAM_BATCH_RESULT_MISSING",
                        resource_type=request.resource_type,
                        resource_id=request.resource_id,
                        action_code=request.action_code,
                        permission_code=request.permission_code,
                        matched_source="runtime_remote_iam_provider",
                    )
                )
                continue

            raw_decision = raw_results[index]
            if not isinstance(raw_decision, dict):
                decisions.append(
                    NsRuntimeAuthorizationDecision.deny(
                        reason="RUNTIME_IAM_BATCH_RESULT_INVALID",
                        resource_type=request.resource_type,
                        resource_id=request.resource_id,
                        action_code=request.action_code,
                        permission_code=request.permission_code,
                        matched_source="runtime_remote_iam_provider",
                    )
                )
                continue

            decisions.append(self._decision_from_payload(raw_decision, request=request))

        return decisions

    async def _post_json(self, endpoint: str, payload: dict[str, Any], *, trace_id: str | None = None) -> dict[str, Any]:
        """Post JSON payload to ns_backend IAM internal API."""
        url = self._build_endpoint_url(endpoint)
        headers = self._build_headers(trace_id)

        try:
            response = await get_http_client().async_post_json(
                url,
                json_data=payload,
                headers=headers,
                timeout_seconds=self._request_timeout_seconds(),
                raise_for_status=True,
            )
            envelope = response.json()
        except NsHttpStatusError as exc:
            raise NsRuntimeAuthProviderError(
                f"runtime IAM internal API HTTP {exc.status_code}: {exc.response_text[:500]}"
            ) from exc
        except NsHttpResponseDecodeError as exc:
            raise NsRuntimeAuthProviderError("runtime IAM internal API response is not valid JSON") from exc
        except NsHttpClientError as exc:
            raise NsRuntimeAuthProviderError(f"runtime IAM internal API request failed: {exc}") from exc
        except Exception as exc:
            # aiohttp/requests transport exceptions are intentionally normalized
            # here so runtime callers do not depend on concrete HTTP libraries.
            raise NsRuntimeAuthProviderError(f"runtime IAM internal API request failed: {exc}") from exc

        return self._extract_success_data(envelope)

    def _build_headers(self, trace_id: str | None) -> dict[str, str]:
        """Build HTTP headers for IAM internal API calls."""
        headers = {
            "Authorization": f"Bearer {self._internal_service_token()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "ns_runtime/remote-iam-auth-provider",
        }

        normalized_trace_id = _normalize_optional(trace_id)
        if normalized_trace_id is not None:
            headers["X-Trace-Id"] = normalized_trace_id

        return headers

    def _build_endpoint_url(self, endpoint: str) -> str:
        """Build full IAM internal API URL from configured base URL."""
        normalized_endpoint = str(endpoint or "").strip().lstrip("/")
        if not normalized_endpoint:
            raise NsRuntimeConfigurationError("runtime IAM internal API endpoint is required")

        return f"{str(self._config.iam_internal_base_url).strip().rstrip('/')}/{normalized_endpoint}"

    def _internal_service_token(self) -> str:
        """Resolve internal service token used by ns_runtime to call ns_backend IAM."""
        token = str(self._config.iam_internal_service_token or self._config.service_token or "").strip()
        if not token:
            raise NsRuntimeConfigurationError("runtime iam_internal_service_token or service_token is required")
        return token

    def _request_timeout_seconds(self) -> float:
        """Resolve positive HTTP request timeout."""
        timeout = float(self._config.iam_internal_request_timeout_seconds or 0)
        if timeout <= 0:
            raise NsRuntimeConfigurationError("runtime iam_internal_request_timeout_seconds must be positive")
        return timeout

    def _validate_config(self) -> None:
        """Validate remote IAM provider configuration."""
        base_url = str(self._config.iam_internal_base_url or "").strip()
        if not base_url:
            raise NsRuntimeConfigurationError("runtime iam_internal_base_url is required when auth_provider is remote_iam")

        self._internal_service_token()
        self._request_timeout_seconds()

    @staticmethod
    def _extract_success_data(envelope: Any) -> dict[str, Any]:
        """Extract data object from backend success response envelope."""
        if not isinstance(envelope, dict):
            raise NsRuntimeAuthProviderError("runtime IAM internal API response must be a JSON object")

        if "code" not in envelope:
            return dict(envelope)

        code = envelope.get("code")
        if str(code) != "0":
            message = str(envelope.get("msg") or envelope.get("message") or "runtime IAM internal API returned failed response")
            raise NsRuntimeAuthProviderError(message)

        data = envelope.get("data") or {}
        if not isinstance(data, dict):
            raise NsRuntimeAuthProviderError("runtime IAM internal API response data must be a JSON object")

        return dict(data)

    @staticmethod
    def _anonymous_frontend_principal(payload: dict[str, Any]) -> NsRuntimePrincipal:
        """Build anonymous frontend principal."""
        client_id = _normalize_optional(payload.get("client_id"))
        session_id = _normalize_optional(payload.get("session_id"))
        principal_id = client_id or "anonymous"

        return NsRuntimePrincipal(
            principal_type=RUNTIME_PRINCIPAL_ANONYMOUS_FRONTEND,
            principal_id=principal_id,
            authenticated=False,
            display_name="anonymous",
            client_id=client_id,
            session_id=session_id,
            claims={},
        )

    @staticmethod
    def _principal_from_payload(payload: dict[str, Any]) -> NsRuntimePrincipal:
        """Build NsRuntimePrincipal from IAM introspection principal payload."""
        principal_type = _normalize_required_text(payload.get("principal_type"), "principal.principal_type")
        principal_id = _normalize_required_text(payload.get("principal_id"), "principal.principal_id")

        claims = payload.get("claims") or {}
        if not isinstance(claims, dict):
            claims = {}

        return NsRuntimePrincipal(
            principal_type=principal_type,
            principal_id=principal_id,
            authenticated=bool(payload.get("authenticated")),
            display_name=_normalize_optional(payload.get("display_name")),
            user_id=_normalize_optional(payload.get("user_id")),
            service_id=_normalize_optional(payload.get("service_id")),
            backend_id=_normalize_optional(payload.get("backend_id")),
            node_id=_normalize_optional(payload.get("node_id")),
            client_id=_normalize_optional(payload.get("client_id")),
            session_id=_normalize_optional(payload.get("session_id")),
            claims=dict(claims),
            expires_at_epoch_ms=_normalize_optional_int(payload.get("expires_at_epoch_ms")),
        )

    @staticmethod
    def _decision_from_payload(payload: dict[str, Any], *, request: NsRuntimeAuthorizationRequest) -> NsRuntimeAuthorizationDecision:
        """Build NsRuntimeAuthorizationDecision from IAM authorization payload."""
        hit_details = payload.get("hit_details") or {}
        if not isinstance(hit_details, dict):
            hit_details = {}

        decision_chain = payload.get("decision_chain") or []
        if not isinstance(decision_chain, list):
            decision_chain = []

        raw_decision = payload.get("raw_decision") or payload
        if not isinstance(raw_decision, dict):
            raw_decision = {}

        allowed = bool(payload.get("allowed"))
        return NsRuntimeAuthorizationDecision(
            allowed=allowed,
            effect=str(payload.get("effect") or ("allow" if allowed else "deny")),
            reason=str(payload.get("reason") or ("ALLOW" if allowed else "DENY")),
            resource_type=_normalize_optional(payload.get("resource_type")) or request.resource_type,
            resource_id=_normalize_optional(payload.get("resource_id")) or request.resource_id,
            action_code=_normalize_optional(payload.get("action_code")) or request.action_code,
            permission_code=_normalize_optional(payload.get("permission_code")) or request.permission_code,
            matched_source=_normalize_optional(payload.get("matched_source")) or "runtime_remote_iam_provider",
            hit_details=dict(hit_details),
            decision_chain=list(decision_chain),
            raw_decision=dict(raw_decision),
        )


def build_runtime_auth_provider(config: NsRuntimeConfig | None = None) -> NsRuntimeAuthProvider:
    """Build runtime auth provider from runtime config."""
    if config is None:
        from ns_common.config import ns_config

        config = ns_config.runtime_config

    provider_name = str(getattr(config, "auth_provider", "static") or "static").strip().lower()
    if provider_name == "static":
        return NsRuntimeStaticAuthProvider(config)

    if provider_name == "remote_iam":
        return NsRuntimeRemoteIamAuthProvider(config)

    raise NsRuntimeConfigurationError(f"runtime auth_provider is invalid: {provider_name}")


def _normalize_service_principal_type(value: Any) -> str:
    """Normalize runtime service principal type aliases."""
    normalized = str(value or "").strip().lower()
    if normalized in {
        "backend",
        "backend_service",
        "ns_backend"
    }:
        return RUNTIME_PRINCIPAL_BACKEND_SERVICE

    if normalized in {
        "runtime",
        "runtime_node",
        "runtime_sub",
        "node",
        "sub"
    }:
        return RUNTIME_PRINCIPAL_RUNTIME_NODE

    return normalized or "service"


def _resolve_service_principal_id(*, payload: dict[str, Any], principal_type: str) -> str:
    """Resolve backend service or runtime node principal id from register payload."""
    if principal_type == RUNTIME_PRINCIPAL_BACKEND_SERVICE:
        return (
                _normalize_optional(payload.get("backend_id"))
                or _normalize_optional(payload.get("instance_id"))
                or "backend:*"
        )

    if principal_type == RUNTIME_PRINCIPAL_RUNTIME_NODE:
        return _normalize_optional(payload.get("node_id")) or "node:*"

    return (
            _normalize_optional(payload.get("principal_id"))
            or _normalize_optional(payload.get("instance_id"))
            or _normalize_optional(payload.get("node_id"))
            or "service:*"
    )


def _normalize_required_text(value: Any, field_name: str) -> str:
    """Normalize required string field."""
    normalized = str(value or "").strip()
    if not normalized:
        raise NsRuntimeAuthProviderError(f"{field_name} is required")
    return normalized


def _normalize_optional(value: Any) -> str | None:
    """Normalize optional string field."""
    if value is None:
        return None

    normalized = str(value).strip()
    return normalized or None


def _normalize_optional_int(value: Any) -> int | None:
    """Normalize optional integer field."""
    if value is None or isinstance(value, bool):
        return None

    try:
        return int(value)
    except (
            TypeError,
            ValueError
    ):
        return None
