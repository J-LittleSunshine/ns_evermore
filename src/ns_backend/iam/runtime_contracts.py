# -*- coding: utf-8 -*-
"""Backend implementation primitives for the IAM-R1 runtime contract.

The module has no Django import. Production composition supplies persistent
repositories; tests can use the explicit in-memory implementations below.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from typing import Callable, Protocol
from uuid import uuid4

from ns_common.exceptions import NsValidationError
from ns_common.iam import (
    IamAccessCheckRequest,
    IamAccessDecision,
    IamCredentialStatus,
    IamIntrospectionRequest,
    IamIntrospectionResult,
    IamPrincipalType,
    IamTargetContext,
    PayloadRefValidationRequest,
    PayloadRefValidationResult,
    PayloadRefRevalidationDecision,
    PayloadRefRevalidationRequest,
    PermissionInvalidation,
    RuntimeBootstrapRequest,
    RuntimeBootstrapResult,
    RuntimeRoleScope,
)
from ns_common.time import Clock


_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:@/-]{0,255}")
_CAPABILITY = re.compile(r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+")
_NODE_CREDENTIAL_FIELDS = {
    "credential_id", "identity", "tenant_id", "principal_type",
    "component_type", "roles", "capabilities", "issued_at", "expires_at",
}
_MANAGEMENT_MESSAGE_PREFIXES = (
    "runtime.control.", "config.", "cluster.", "dead_letter.",
    "replay.", "cancel.", "hold.", "status.",
)


@dataclass(frozen=True, slots=True, kw_only=True)
class ResolvedPrincipal:
    identity: str = field(repr=False)
    tenant_id: str = field(repr=False)
    principal_type: IamPrincipalType
    component_type: str
    allowed_capabilities: frozenset[str] = field(repr=False)
    permission_snapshot_ref: str = field(repr=False)
    permission_digest: str = field(repr=False)
    permission_version: str = field(repr=False)
    issued_at: datetime
    expires_at: datetime
    credential_status: IamCredentialStatus
    resume_eligible: bool

    def as_result(self, *, capabilities: frozenset[str]) -> IamIntrospectionResult:
        return IamIntrospectionResult(
            identity=self.identity,
            tenant_id=self.tenant_id,
            principal_type=self.principal_type,
            component_type=self.component_type,
            capabilities=capabilities,
            permission_snapshot_ref=self.permission_snapshot_ref,
            permission_digest=self.permission_digest,
            permission_version=self.permission_version,
            issued_at=self.issued_at,
            expires_at=self.expires_at,
            credential_status=self.credential_status,
            resume_eligible=self.resume_eligible,
        )


class PrincipalResolver(Protocol):
    async def resolve(self, token: str) -> ResolvedPrincipal | None: ...


class PermissionPolicy(Protocol):
    async def decide(self, request: IamAccessCheckRequest) -> IamAccessDecision: ...


class PayloadRefPolicy(Protocol):
    async def validate(
        self,
        request: PayloadRefValidationRequest,
    ) -> PayloadRefValidationResult: ...


class BackendRuntimeIamService:
    """Validate client claims while retaining IAM as the only authority."""

    def __init__(
        self,
        *,
        principal_resolver: PrincipalResolver,
        permission_policy: PermissionPolicy,
        payload_ref_policy: PayloadRefPolicy,
        clock: Clock,
        payload_decision_reference_factory: Callable[[], str] | None = None,
    ) -> None:
        for value, method, name in (
            (principal_resolver, "resolve", "principal_resolver"),
            (permission_policy, "decide", "permission_policy"),
            (payload_ref_policy, "validate", "payload_ref_policy"),
        ):
            if not callable(getattr(value, method, None)):
                _invalid(name)
        if not isinstance(clock, Clock):
            _invalid("clock")
        self._resolver = principal_resolver
        self._permissions = permission_policy
        self._payload_refs = payload_ref_policy
        self._clock = clock
        self._payload_decision_references = (
            payload_decision_reference_factory
            or (lambda: f"iam-payload:{uuid4()}")
        )

    async def introspect(
        self,
        request: IamIntrospectionRequest,
    ) -> IamIntrospectionResult | None:
        if not isinstance(request, IamIntrospectionRequest):
            _invalid("request")
        resolved = await self._resolver.resolve(request.token)
        if resolved is None:
            return None
        now = self._clock.utc_now()
        if resolved.credential_status is not IamCredentialStatus.ACTIVE:
            return resolved.as_result(capabilities=frozenset())
        if resolved.expires_at <= now:
            return replace(
                resolved.as_result(capabilities=frozenset()),
                credential_status=IamCredentialStatus.EXPIRED,
            )
        # The declaration is evidence to validate, never authority to widen.
        if request.component_type != resolved.component_type:
            return None
        if not request.requested_capabilities.issubset(
            resolved.allowed_capabilities,
        ):
            return None
        return resolved.as_result(
            capabilities=request.requested_capabilities,
        )

    async def access_check(
        self,
        request: IamAccessCheckRequest,
    ) -> IamAccessDecision:
        if not isinstance(request, IamAccessCheckRequest):
            _invalid("request")
        mismatch = runtime_access_context_mismatch(request)
        if mismatch is not None:
            return IamAccessDecision(
                allowed=False,
                reason=mismatch,
                permission_version=request.permission_version,
                decided_at=self._clock.utc_now(),
            )
        return await self._permissions.decide(request)

    async def validate_payload_ref(
        self,
        request: PayloadRefValidationRequest,
    ) -> PayloadRefValidationResult:
        if not isinstance(request, PayloadRefValidationRequest):
            _invalid("request")
        return await self._payload_refs.validate(request)

    async def revalidate_payload_ref(
        self,
        request: PayloadRefRevalidationRequest,
    ) -> PayloadRefRevalidationDecision:
        if not isinstance(request, PayloadRefRevalidationRequest):
            _invalid("request")
        now = self._clock.utc_now()
        revalidate = getattr(self._payload_refs, "revalidate", None)
        metadata = (
            await revalidate(request)
            if callable(revalidate)
            else None
        )
        metadata_valid = bool(
            type(metadata) is PayloadRefValidationResult
            and metadata.valid
            and not metadata.revoked
            and metadata.object_id == request.object_id
            and metadata.version == request.version
            and metadata.checksum == request.checksum
            and metadata.size_bytes == request.size_bytes
            and metadata.tenant_id == request.tenant_id
            and metadata.expires_at > now
        )
        decision = None
        if metadata_valid:
            decision = await self.access_check(IamAccessCheckRequest(
                identity=request.target_principal,
                tenant_id=request.target_tenant_id,
                permission_snapshot_ref=request.permission_snapshot_ref,
                permission_version=request.permission_version,
                message_type="payload_ref.read",
                target=IamTargetContext(
                    kind="payload_ref",
                    tenant_id=request.tenant_id,
                    reference=request.object_id,
                ),
                cross_tenant=(
                    request.target_tenant_id != request.tenant_id
                ),
                management=False,
                task_creation=False,
            ))
        reference = self._payload_decision_references()
        if type(reference) is not str or not reference:
            _invalid("payload_decision_reference")
        expires_at = (
            metadata.expires_at
            if metadata_valid
            else now
        )
        return PayloadRefRevalidationDecision(
            valid=metadata_valid,
            allowed=bool(
                metadata_valid
                and decision is not None
                and decision.allowed
                and not decision.refresh_required
                and decision.permission_version == request.permission_version
            ),
            reason=(
                decision.reason
                if decision is not None
                else "payload_provider_unavailable_or_invalid"
            ),
            object_id=request.object_id,
            version=request.version,
            checksum=request.checksum,
            size_bytes=request.size_bytes,
            tenant_id=request.tenant_id,
            target_principal=request.target_principal,
            target_fingerprint=request.target_fingerprint,
            permission_snapshot_ref=request.permission_snapshot_ref,
            permission_version=(
                decision.permission_version
                if decision is not None
                else request.permission_version
            ),
            decision_reference=reference,
            decided_at=(
                decision.decided_at if decision is not None else now
            ),
            expires_at=expires_at,
            refresh_required=bool(
                decision is not None and decision.refresh_required
            ),
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class RuntimeNodeCredential:
    credential_id: str = field(repr=False)
    token: str = field(repr=False)
    identity: str = field(repr=False)
    tenant_id: str = field(repr=False)
    roles: frozenset[RuntimeRoleScope]
    capabilities: frozenset[str] = field(repr=False)
    issued_at: datetime
    expires_at: datetime


class RuntimeCredentialStatusStore(Protocol):
    async def put(
        self,
        credential_id: str,
        status: IamCredentialStatus,
        expires_at: datetime,
    ) -> None: ...

    async def get(self, credential_id: str) -> IamCredentialStatus | None: ...


class InMemoryRuntimeCredentialStatusStore:
    """Explicit test/reference store; production must inject persistence."""

    def __init__(self) -> None:
        self._items: dict[str, tuple[IamCredentialStatus, datetime]] = {}

    async def put(
        self,
        credential_id: str,
        status: IamCredentialStatus,
        expires_at: datetime,
    ) -> None:
        self._items[credential_id] = (status, expires_at)

    async def get(self, credential_id: str) -> IamCredentialStatus | None:
        item = self._items.get(credential_id)
        return item[0] if item is not None else None


class RuntimeNodeCredentialAuthority:
    """Issue, rotate, revoke and verify signed runtime-node credentials."""

    TOKEN_PREFIX = "nsrn1"

    def __init__(
        self,
        *,
        signing_key: bytes,
        status_store: RuntimeCredentialStatusStore,
        clock: Clock,
        credential_id_factory: Callable[[], str] | None = None,
        ttl_seconds: int = 900,
    ) -> None:
        if not isinstance(signing_key, bytes) or len(signing_key) < 32:
            _invalid("signing_key")
        if not callable(getattr(status_store, "put", None)) or not callable(
            getattr(status_store, "get", None)
        ):
            _invalid("status_store")
        if not isinstance(clock, Clock):
            _invalid("clock")
        if isinstance(ttl_seconds, bool) or not isinstance(ttl_seconds, int) or ttl_seconds <= 0:
            _invalid("ttl_seconds")
        self._key = bytes(signing_key)
        self._store = status_store
        self._clock = clock
        self._id_factory = credential_id_factory or (
            lambda: f"node_credential:{uuid4().hex}"
        )
        self._ttl = ttl_seconds

    async def issue(
        self,
        *,
        identity: str,
        tenant_id: str,
        roles: frozenset[RuntimeRoleScope],
        capabilities: frozenset[str],
    ) -> RuntimeNodeCredential:
        _valid_name(identity, "identity")
        _valid_name(tenant_id, "tenant_id")
        if not isinstance(roles, frozenset) or not roles or any(
            not isinstance(item, RuntimeRoleScope) for item in roles
        ):
            _invalid("roles")
        _valid_capabilities(capabilities)
        credential_id = self._id_factory()
        _valid_name(credential_id, "credential_id")
        issued_at = self._clock.utc_now().astimezone(timezone.utc)
        expires_at = issued_at + timedelta(seconds=self._ttl)
        claims = {
            "credential_id": credential_id,
            "identity": identity,
            "tenant_id": tenant_id,
            "principal_type": IamPrincipalType.RUNTIME_NODE.value,
            "component_type": "runtime",
            "roles": sorted(item.value for item in roles),
            "capabilities": sorted(capabilities),
            "issued_at": issued_at.isoformat(),
            "expires_at": expires_at.isoformat(),
        }
        token = self._encode(claims)
        await self._store.put(
            credential_id,
            IamCredentialStatus.ACTIVE,
            expires_at,
        )
        return RuntimeNodeCredential(
            credential_id=credential_id,
            token=token,
            identity=identity,
            tenant_id=tenant_id,
            roles=roles,
            capabilities=capabilities,
            issued_at=issued_at,
            expires_at=expires_at,
        )

    async def refresh(
        self,
        credential: RuntimeNodeCredential,
    ) -> RuntimeNodeCredential:
        verified = await self.verify(credential.token)
        if verified is None or verified.credential_id != credential.credential_id:
            raise NsValidationError(
                "Runtime node credential cannot be refreshed.",
                details={"component": "backend_runtime_iam", "reason": "credential_invalid"},
            )
        await self.revoke(verified.credential_id)
        return await self.issue(
            identity=verified.identity,
            tenant_id=verified.tenant_id,
            roles=verified.roles,
            capabilities=verified.capabilities,
        )

    async def revoke(self, credential_id: str) -> None:
        _valid_name(credential_id, "credential_id")
        await self._store.put(
            credential_id,
            IamCredentialStatus.REVOKED,
            self._clock.utc_now() + timedelta(seconds=self._ttl),
        )

    async def verify(self, token: str) -> RuntimeNodeCredential | None:
        claims = self._decode(token)
        if claims is None:
            return None
        try:
            if set(claims) != _NODE_CREDENTIAL_FIELDS:
                return None
            credential_id = _verified_name(claims["credential_id"])
            issued_at = _verified_time(claims["issued_at"])
            expires_at = _verified_time(claims["expires_at"])
            raw_roles = claims["roles"]
            if not isinstance(raw_roles, list) or len(raw_roles) != len(set(raw_roles)):
                return None
            roles = frozenset(RuntimeRoleScope(item) for item in raw_roles)
            raw_capabilities = claims["capabilities"]
            if (
                not isinstance(raw_capabilities, list)
                or len(raw_capabilities) != len(set(raw_capabilities))
            ):
                return None
            capabilities = frozenset(_verified_capability(item) for item in raw_capabilities)
            identity = _verified_name(claims["identity"])
            tenant_id = _verified_name(claims["tenant_id"])
        except (KeyError, TypeError, ValueError):
            return None
        if claims.get("principal_type") != IamPrincipalType.RUNTIME_NODE.value:
            return None
        if claims.get("component_type") != "runtime":
            return None
        if not roles or expires_at <= issued_at or issued_at > self._clock.utc_now():
            return None
        status = await self._store.get(credential_id)
        if status is not IamCredentialStatus.ACTIVE:
            return None
        if expires_at <= self._clock.utc_now():
            return None
        return RuntimeNodeCredential(
            credential_id=credential_id,
            token=token,
            identity=identity,
            tenant_id=tenant_id,
            roles=roles,
            capabilities=capabilities,
            issued_at=issued_at,
            expires_at=expires_at,
        )

    def _encode(self, claims: dict[str, object]) -> str:
        payload = json.dumps(
            claims,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        signature = hmac.new(self._key, payload, hashlib.sha256).digest()
        return f"{self.TOKEN_PREFIX}.{_b64(payload)}.{_b64(signature)}"

    def _decode(self, token: str) -> dict[str, object] | None:
        if not isinstance(token, str) or not token or len(token) > 65_536:
            return None
        parts = token.split(".")
        if len(parts) != 3 or parts[0] != self.TOKEN_PREFIX:
            return None
        try:
            payload = _unb64(parts[1])
            signature = _unb64(parts[2])
            expected = hmac.new(self._key, payload, hashlib.sha256).digest()
            if not hmac.compare_digest(signature, expected):
                return None
            value = json.loads(payload.decode("utf-8"))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError):
            return None
        return value if isinstance(value, dict) else None


class RuntimeBootstrapPolicy:
    """Authorize configured roles only; this never grants cluster authority."""

    def __init__(self, *, config_version: str, policy_version: str) -> None:
        _valid_name(config_version, "config_version")
        _valid_name(policy_version, "policy_version")
        self._config_version = config_version
        self._policy_version = policy_version

    def authorize(
        self,
        request: RuntimeBootstrapRequest,
        *,
        credential: RuntimeNodeCredential,
    ) -> RuntimeBootstrapResult:
        if not isinstance(request, RuntimeBootstrapRequest):
            _invalid("bootstrap.request")
        if not isinstance(credential, RuntimeNodeCredential):
            _invalid("bootstrap.credential")
        if request.credential_id != credential.credential_id:
            _invalid("bootstrap.credential_id")
        authorized = request.requested_role in credential.roles
        return RuntimeBootstrapResult(
            role_authorized=authorized,
            authorized_roles=credential.roles,
            candidate_master=(
                authorized
                and request.requested_role in {
                    RuntimeRoleScope.ACTIVE_MASTER,
                    RuntimeRoleScope.STANDBY_MASTER,
                }
            ),
            config_version=self._config_version,
            policy_version=self._policy_version,
        )


class PermissionInvalidationLedger:
    """Explicit version-polling contract; not a runtime authoritative store."""

    def __init__(self) -> None:
        self._items: dict[str, PermissionInvalidation] = {}

    def publish(self, event: PermissionInvalidation) -> None:
        if not isinstance(event, PermissionInvalidation):
            _invalid("invalidation")
        self._items[event.permission_snapshot_ref] = event

    def poll(
        self,
        permission_snapshot_ref: str,
        known_version: str,
    ) -> PermissionInvalidation | None:
        _valid_name(permission_snapshot_ref, "permission_snapshot_ref")
        _valid_name(known_version, "known_version")
        event = self._items.get(permission_snapshot_ref)
        if event is None or event.current_version == known_version:
            return None
        return event


def runtime_access_context_mismatch(
    request: IamAccessCheckRequest,
) -> str | None:
    """Recompute security flags from authoritative request fields."""
    if not isinstance(request, IamAccessCheckRequest):
        _invalid("access_request")
    target_crosses_tenant = (
        request.target.tenant_id is not None
        and request.target.tenant_id != request.tenant_id
    )
    if request.cross_tenant != target_crosses_tenant:
        return "cross_tenant_context_mismatch"
    if request.management != request.message_type.startswith(
        _MANAGEMENT_MESSAGE_PREFIXES,
    ):
        return "management_context_mismatch"
    if request.task_creation != (request.message_type == "task.dispatch"):
        return "task_creation_context_mismatch"
    return None


def _b64(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _unb64(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.b64decode(value + padding, altchars=b"-_", validate=True)


def _valid_name(value: object, field_name: str) -> None:
    if not isinstance(value, str) or _NAME.fullmatch(value) is None:
        _invalid(field_name)


def _valid_capabilities(value: object) -> None:
    if not isinstance(value, frozenset) or any(
        not isinstance(item, str) or _CAPABILITY.fullmatch(item) is None
        for item in value
    ):
        _invalid("capabilities")


def _verified_name(value: object) -> str:
    if not isinstance(value, str) or _NAME.fullmatch(value) is None:
        raise ValueError
    return value


def _verified_capability(value: object) -> str:
    if not isinstance(value, str) or _CAPABILITY.fullmatch(value) is None:
        raise ValueError
    return value


def _verified_time(value: object) -> datetime:
    if not isinstance(value, str):
        raise ValueError
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError
    return parsed.astimezone(timezone.utc)


def _invalid(field_name: str) -> None:
    raise NsValidationError(
        "Backend runtime IAM value is invalid.",
        details={"component": "backend_runtime_iam", "field": field_name},
    )


__all__ = (
    "BackendRuntimeIamService", "InMemoryRuntimeCredentialStatusStore",
    "PayloadRefPolicy", "PermissionInvalidationLedger", "PermissionPolicy",
    "PrincipalResolver", "ResolvedPrincipal", "RuntimeBootstrapPolicy",
    "RuntimeCredentialStatusStore", "RuntimeNodeCredential",
    "RuntimeNodeCredentialAuthority", "runtime_access_context_mismatch",
)
