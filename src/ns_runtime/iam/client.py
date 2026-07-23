# -*- coding: utf-8 -*-
"""HTTP IAM client with explicit ownership, trace and service credential."""

from __future__ import annotations

from typing import Callable, Mapping

from ns_common.exceptions import (
    NsDependencyError,
    NsRuntimeIamDeniedError,
    NsRuntimeIamTimeoutError,
    NsRuntimeIamUnavailableError,
    NsValidationError,
)
from ns_common.http_client import NsAsyncHttpClient, NsHttpClientOwner
from ns_common.iam import (
    IamAccessCheckRequest,
    IamAccessDecision,
    IamCredentialStatus,
    IamIntrospectionRequest,
    IamIntrospectionResult,
    PayloadRefValidationRequest,
    PayloadRefValidationResult,
    PayloadRefRevalidationDecision,
    PayloadRefRevalidationRequest,
)
from ns_common.time import Clock
from ns_runtime.connection.iam import (
    HandshakeIamAdapter,
    HandshakeIamAuthority,
    HandshakeIamRequest,
)

from .models import PermissionSnapshot


class IamClient(HandshakeIamAdapter):
    """One explicitly injected client; it never creates or finds HTTP globals."""

    def __init__(
        self,
        *,
        http_client: NsAsyncHttpClient,
        internal_service_credential: str,
        trace_id_factory: Callable[[], str],
        clock: Clock,
        iam_mode: str = "strict",
        _factory: object | None = None,
        _binding: object | None = None,
        _construction_token: object | None = None,
    ) -> None:
        if (
            type(self) is not IamClient
            or type(_factory) is not IamClientFactory
            or not _factory._consume_construction_token(_construction_token)
        ):
            _invalid("composition_factory")
        if type(http_client) is not NsAsyncHttpClient:
            _invalid("http_client")
        if not isinstance(internal_service_credential, str) or len(internal_service_credential) < 32:
            _invalid("internal_service_credential")
        if not callable(trace_id_factory):
            _invalid("trace_id_factory")
        if not isinstance(clock, Clock):
            _invalid("clock")
        if iam_mode not in {"strict", "cache"}:
            _invalid("iam_mode")
        self._http = http_client
        self._service_credential = internal_service_credential
        self._trace_id_factory = trace_id_factory
        self._clock = clock
        self._iam_mode = iam_mode
        self._composition_factory = _factory
        self._http_binding = _binding
        self._payload_revalidation_results: dict[
            int, tuple[PayloadRefRevalidationRequest, PayloadRefRevalidationDecision]
        ] = {}
        self._authorization_service: object | None = None

    def __repr__(self) -> str:
        return "IamClient(explicit=True, credential=redacted)"

    def _is_production_adapter(self) -> bool:
        """Fail closed for uninitialized instances and method substitution."""

        substituted = {
            "authenticate",
            "access_check",
            "refresh_permission_snapshot",
            "validate_payload_ref",
            "revalidate_payload_ref",
            "_post",
        }.intersection(vars(self))
        return bool(
            type(self) is IamClient
            and type(getattr(self, "_composition_factory", None))
            is IamClientFactory
            and self._composition_factory._owns(self)
            and type(getattr(self, "_http", None)) is NsAsyncHttpClient
            and not substituted
            and getattr(type(self), "revalidate_payload_ref", None)
            is IamClient.revalidate_payload_ref
            and getattr(type(self), "access_check", None) is IamClient.access_check
            and getattr(type(self), "_post", None) is IamClient._post
        )

    async def authenticate(
        self,
        request: HandshakeIamRequest,
    ) -> HandshakeIamAuthority:
        if not isinstance(request, HandshakeIamRequest):
            _invalid("request")
        token = request.credential.take()
        try:
            contract = IamIntrospectionRequest(
                token=token,
                component_type=request.claims.component_type,
                requested_capabilities=request.claims.requested_capabilities,
                protocol_version=str(request.claims.requested_version),
            )
            data = await self._post(
                "internal/introspect_token/",
                contract.to_wire(),
            )
        finally:
            del token
        if data.get("active") is not True:
            raise NsRuntimeIamDeniedError(
                details={
                    "component": "runtime_iam_client",
                    "operation": "introspect",
                    "reason": "credential_inactive",
                },
            )
        try:
            result = IamIntrospectionResult.from_wire(data.get("authority"))
        except NsValidationError:
            raise _malformed("introspection") from None
        now = self._clock.utc_now()
        if (
            result.credential_status is not IamCredentialStatus.ACTIVE
            or result.issued_at > now
            or result.expires_at <= now
        ):
            raise NsRuntimeIamDeniedError(
                details={
                    "component": "runtime_iam_client",
                    "operation": "introspect",
                    "reason": (
                        result.credential_status.value
                        if result.credential_status is not IamCredentialStatus.ACTIVE
                        else "credential_time_invalid"
                    ),
                },
            )
        if result.component_type != request.claims.component_type:
            raise NsRuntimeIamDeniedError(
                details={
                    "component": "runtime_iam_client",
                    "operation": "introspect",
                    "reason": "component_type_mismatch",
                },
            )
        if not result.capabilities.issubset(request.claims.requested_capabilities):
            raise NsRuntimeIamDeniedError(
                details={
                    "component": "runtime_iam_client",
                    "operation": "introspect",
                    "reason": "capability_escalation",
                },
            )
        return HandshakeIamAuthority(
            identity=result.identity,
            tenant_id=result.tenant_id,
            component_type=result.component_type,
            principal_type=result.principal_type,
            capabilities=result.capabilities,
            permissions={},
            permission_snapshot_ref=result.permission_snapshot_ref,
            permission_digest=result.permission_digest,
            permission_version=result.permission_version,
            issued_at=result.issued_at,
            expires_at=result.expires_at,
            resume_eligible=result.resume_eligible,
            iam_mode=self._iam_mode,
        )

    async def access_check(
        self,
        request: IamAccessCheckRequest,
    ) -> IamAccessDecision:
        if not isinstance(request, IamAccessCheckRequest):
            _invalid("request")
        data = await self._post("internal/runtime_access_check/", request.to_wire())
        try:
            return IamAccessDecision.from_wire(data)
        except NsValidationError:
            raise _malformed("access_check") from None

    async def refresh_permission_snapshot(
        self,
        snapshot: PermissionSnapshot,
    ) -> PermissionSnapshot:
        if not isinstance(snapshot, PermissionSnapshot):
            _invalid("snapshot")
        data = await self._post(
            "internal/permission_snapshot/",
            {
                "identity": snapshot.identity,
                "tenant_id": snapshot.tenant_id,
                "permission_snapshot_ref": snapshot.permission_snapshot_ref,
                "known_version": snapshot.permission_version,
                "component_type": snapshot.component_type,
                "capabilities": sorted(snapshot.capabilities),
                "expires_at": snapshot.expires_at.isoformat().replace("+00:00", "Z"),
            },
        )
        try:
            result = IamIntrospectionResult.from_wire(data)
        except NsValidationError:
            raise _malformed("permission_snapshot") from None
        return PermissionSnapshot.from_introspection(result, iam_mode=self._iam_mode)

    async def validate_payload_ref(
        self,
        request: PayloadRefValidationRequest,
    ) -> PayloadRefValidationResult:
        """Perform one live backend validation; no authorization cache is used."""
        if not isinstance(request, PayloadRefValidationRequest):
            _invalid("payload_ref_request")
        data = await self._post(
            "internal/payload_ref/validate/",
            request.to_wire(),
        )
        try:
            return PayloadRefValidationResult.from_wire(data)
        except NsValidationError:
            raise _malformed("payload_ref") from None

    async def revalidate_payload_ref(
        self,
        request: PayloadRefRevalidationRequest,
    ) -> PayloadRefRevalidationDecision:
        """Obtain one backend-issued object-level payload access decision."""
        if not isinstance(request, PayloadRefRevalidationRequest):
            _invalid("payload_ref_revalidation_request")
        data = await self._post(
            "internal/payload_ref/revalidate/",
            request.to_wire(),
        )
        try:
            decision = PayloadRefRevalidationDecision.from_wire(data)
        except NsValidationError:
            raise _malformed("payload_ref_revalidation") from None
        self._payload_revalidation_results[id(decision)] = (request, decision)
        return decision

    def _consume_payload_revalidation(
        self,
        *,
        request: PayloadRefRevalidationRequest,
        decision: PayloadRefRevalidationDecision,
    ) -> bool:
        if not self._is_production_adapter():
            return False
        issued = self._payload_revalidation_results.pop(id(decision), None)
        return bool(
            issued is not None
            and issued[0] is request
            and issued[1] is decision
        )

    def _bind_authorization_service(self, service: object) -> None:
        if (
            not self._is_production_adapter()
            or service is None
            or self._authorization_service is not None
        ):
            _invalid("authorization_service")
        self._authorization_service = service

    def _owns_authorization_service(self, service: object) -> bool:
        return bool(
            self._is_production_adapter()
            and self._authorization_service is service
        )

    async def _post(
        self,
        path: str,
        payload: Mapping[str, object],
    ) -> dict[str, object]:
        trace_id = self._trace_id_factory()
        if not isinstance(trace_id, str) or not trace_id:
            raise _malformed("trace")
        try:
            response = await self._http.post(
                path,
                json_data=dict(payload),
                bearer_token=self._service_credential,
                trace_id=trace_id,
                expected_statuses={200},
            )
            body = response.json()
        except NsDependencyError as error:
            if "timeout_seconds" in error.details:
                raise NsRuntimeIamTimeoutError(
                    details={
                        "component": "runtime_iam_client",
                        "operation": "http_request",
                        "reason": "timeout",
                    },
                ) from None
            raise NsRuntimeIamUnavailableError(
                details={
                    "component": "runtime_iam_client",
                    "operation": "http_request",
                    "reason": "backend_unavailable",
                },
            ) from None
        if not isinstance(body, Mapping):
            raise _malformed("response")
        if body.get("success") is not True or set(body) != {
            "success", "code", "error", "message", "data", "request_id",
        }:
            raise _malformed("response")
        data = body.get("data")
        if not isinstance(data, Mapping):
            raise _malformed("response.data")
        return dict(data)

    def __copy__(self) -> "IamClient":
        del self
        _invalid("copy")

    def __deepcopy__(self, memo: dict[int, object]) -> "IamClient":
        del self, memo
        _invalid("copy")


class IamClientFactory:
    """One composition-owned factory bound to an owner/client/context triple."""

    __slots__ = (
        "_owner", "_http_client", "_composition", "_binding",
        "_pending_token", "_client",
    )

    def __init__(
        self,
        *,
        http_owner: NsHttpClientOwner,
        http_client: NsAsyncHttpClient,
        runtime_composition: object,
    ) -> None:
        if (
            type(self) is not IamClientFactory
            or type(http_owner) is not NsHttpClientOwner
            or type(http_client) is not NsAsyncHttpClient
            or runtime_composition is None
        ):
            _invalid("factory")
        self._owner = http_owner
        self._http_client = http_client
        self._composition = runtime_composition
        self._binding = http_owner._bind_authority_client(
            client=http_client,
            composition=runtime_composition,
        )
        self._pending_token: object | None = None
        self._client: IamClient | None = None

    def create(
        self,
        *,
        internal_service_credential: str,
        trace_id_factory: Callable[[], str],
        clock: Clock,
        iam_mode: str = "strict",
    ) -> IamClient:
        if self._client is not None:
            _invalid("factory.already_created")
        token = object()
        self._pending_token = token
        try:
            client = IamClient(
                http_client=self._http_client,
                internal_service_credential=internal_service_credential,
                trace_id_factory=trace_id_factory,
                clock=clock,
                iam_mode=iam_mode,
                _factory=self,
                _binding=self._binding,
                _construction_token=token,
            )
        finally:
            self._pending_token = None
        self._client = client
        return client

    def _consume_construction_token(self, token: object) -> bool:
        return token is not None and self._pending_token is token

    def _owns(self, client: IamClient) -> bool:
        return bool(
            type(self) is IamClientFactory
            and self._client is client
            and getattr(client, "_http_binding", None) is self._binding
            and self._binding.is_current(
                owner=self._owner,
                client=self._http_client,
                composition=self._composition,
            )
        )

    def __copy__(self) -> "IamClientFactory":
        _invalid("factory.copy")

    def __deepcopy__(self, memo: dict[int, object]) -> "IamClientFactory":
        del memo
        _invalid("factory.copy")


def _malformed(operation: str) -> NsRuntimeIamUnavailableError:
    return NsRuntimeIamUnavailableError(
        details={
            "component": "runtime_iam_client",
            "operation": operation,
            "reason": "malformed_response",
        },
    )


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Runtime IAM client value is invalid.",
        details={"component": "runtime_iam_client", "field": field_name},
    )


__all__ = ("IamClient", "IamClientFactory")
