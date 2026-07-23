# -*- coding: utf-8 -*-
from __future__ import annotations

import hmac
import hashlib
from datetime import datetime, timedelta, timezone as datetime_timezone
from typing import (
    Any,
    TYPE_CHECKING,
)

from django.conf import settings
from django.utils import timezone

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
    RuntimeBootstrapRequest,
    RuntimeRoleScope,
)
from ns_common.time import SystemClock

from ns_backend.iam.errors import (
    IamRuntimeAccessDeniedError,
    IamRuntimeRequestInvalidError,
    IamUserDisabledOrNotFoundError,
    IamUserNotLoggedInOrSessionExpiredError,
)
from ns_backend.iam.repositories import AuthUserRepository
from ns_backend.iam.services.access_decision import AccessDecisionService
from ns_backend.iam.services.auth import AuthService
from ns_backend.iam.services.resource_access_filter import ResourceAccessFilterService
from ns_backend.iam.services.permission import PermissionService
from ns_backend.iam.runtime_contracts import (
    RuntimeBootstrapPolicy,
    RuntimeNodeCredentialAuthority,
    runtime_access_context_mismatch,
)
from ns_backend.iam.runtime_django import DjangoRuntimeCredentialStatusStore

if TYPE_CHECKING:
    pass


class InternalIamService:
    PRINCIPAL_TYPE_FRONTEND_USER = "FRONTEND_USER"
    _BASE_RUNTIME_CAPABILITIES = frozenset({
        "runtime.connection",
        "runtime.heartbeat",
        "runtime.resume",
    })

    @classmethod
    def verify_internal_service_token(cls, token: str | None) -> bool:
        expected_token = str(getattr(settings, "IAM_INTERNAL_TOKEN", "") or "").strip()

        if not expected_token:
            return False

        normalized_token = str(token or "").strip()

        if not normalized_token:
            return False

        return hmac.compare_digest(
            normalized_token,
            expected_token,
        )

    @classmethod
    async def introspect_token(cls, data: dict[str, Any]) -> dict[str, Any]:
        request_data = cls.ensure_dict(data)
        try:
            request = IamIntrospectionRequest(
                token=cls.normalize_required_text(request_data.get("token"), "token"),
                component_type=cls.normalize_required_text(
                    request_data.get("component_type"),
                    "component_type",
                ),
                requested_capabilities=frozenset(
                    cls.ensure_string_list(
                        request_data.get("requested_capabilities"),
                        "requested_capabilities",
                    )
                ),
                protocol_version=cls.normalize_required_text(
                    request_data.get("protocol_version"),
                    "protocol_version",
                ),
            )
        except Exception:
            return {"active": False, "reason": "CLAIMS_INVALID", "authority": None}

        try:
            user, token_record = await AuthService.resolve_user_from_access_token(
                request.token,
            )
        except (
                IamUserNotLoggedInOrSessionExpiredError,
                IamUserDisabledOrNotFoundError,
        ):
            return {
                "active": False,
                "reason": "TOKEN_INVALID_OR_EXPIRED",
                "authority": None,
            }
        authority = await cls._build_frontend_authority(
            user=user,
            component_type=request.component_type,
            requested_capabilities=request.requested_capabilities,
            expires_at=token_record.expired_at,
        )
        if authority is None:
            return {"active": False, "reason": "CLAIMS_DENIED", "authority": None}
        return {
            "active": True,
            "reason": "TOKEN_ACTIVE",
            "authority": authority.to_wire(),
        }

    @classmethod
    async def runtime_access_check(
        cls,
        data: dict[str, Any],
        *,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        request_data = cls.ensure_dict(data)
        target_data = cls.ensure_dict(request_data.get("target"))
        try:
            request = IamAccessCheckRequest(
                identity=cls.normalize_required_text(request_data.get("identity"), "identity"),
                tenant_id=cls.normalize_required_text(request_data.get("tenant_id"), "tenant_id"),
                permission_snapshot_ref=cls.normalize_required_text(
                    request_data.get("permission_snapshot_ref"),
                    "permission_snapshot_ref",
                ),
                permission_version=cls.normalize_required_text(
                    request_data.get("permission_version"),
                    "permission_version",
                ),
                message_type=cls.normalize_required_text(
                    request_data.get("message_type"),
                    "message_type",
                ),
                target=IamTargetContext(
                    kind=cls.normalize_required_text(target_data.get("kind"), "target.kind"),
                    tenant_id=cls.normalize_optional(target_data.get("tenant_id")),
                    reference=cls.normalize_optional(target_data.get("reference")),
                ),
                cross_tenant=cls.ensure_bool(request_data.get("cross_tenant"), "cross_tenant"),
                management=cls.ensure_bool(request_data.get("management"), "management"),
                task_creation=cls.ensure_bool(request_data.get("task_creation"), "task_creation"),
            )
        except Exception as error:
            raise IamRuntimeRequestInvalidError(
                "Runtime access request is invalid.",
            ) from error
        user_id = cls._user_id_from_identity(request.identity)
        user = await AuthUserRepository.get_user_by_id(user_id)
        now = timezone.now()
        if user is None or not bool(getattr(user, "is_active", False)):
            return IamAccessDecision(
                allowed=False,
                reason="principal_inactive",
                permission_version=request.permission_version,
                decided_at=now,
            ).to_wire()
        permission_codes = await PermissionService.list_permission_codes(user)
        current_version, _ = cls._permission_metadata(
            user_id=user_id,
            tenant_id=cls._tenant_id(user),
            permission_codes=permission_codes,
        )
        allowed = True
        reason = "allowed"
        context_mismatch = runtime_access_context_mismatch(request)
        target_crosses_tenant = request.cross_tenant
        message_is_management = request.management
        message_creates_task = request.task_creation
        if request.permission_snapshot_ref != f"permission:user:{user_id}":
            allowed, reason = False, "snapshot_mismatch"
        elif request.permission_version != current_version:
            allowed, reason = False, "permission_version_changed"
        elif request.tenant_id != cls._tenant_id(user):
            allowed, reason = False, "tenant_mismatch"
        elif context_mismatch is not None:
            allowed, reason = False, context_mismatch
        elif target_crosses_tenant and not bool(getattr(user, "is_superuser", False)):
            allowed, reason = False, "cross_tenant_denied"
        elif message_is_management and not (
            bool(getattr(user, "is_staff", False))
            or bool(getattr(user, "is_superuser", False))
        ):
            allowed, reason = False, "management_denied"
        elif message_creates_task and "runtime.task.create" not in permission_codes:
            allowed, reason = False, "task_creation_denied"
        return IamAccessDecision(
            allowed=allowed,
            reason=reason,
            permission_version=current_version,
            decided_at=now,
            refresh_required=(request.permission_version != current_version),
        ).to_wire()

    @classmethod
    async def permission_snapshot(cls, data: dict[str, Any]) -> dict[str, Any]:
        request_data = cls.ensure_dict(data)
        identity = cls.normalize_required_text(request_data.get("identity"), "identity")
        requested_tenant_id = cls.normalize_required_text(
            request_data.get("tenant_id"),
            "tenant_id",
        )
        requested_snapshot_ref = cls.normalize_required_text(
            request_data.get("permission_snapshot_ref"),
            "permission_snapshot_ref",
        )
        cls.normalize_required_text(request_data.get("known_version"), "known_version")
        user_id = cls._user_id_from_identity(identity)
        user = await AuthUserRepository.get_user_by_id(user_id)
        if user is None or not bool(getattr(user, "is_active", False)):
            raise IamRuntimeAccessDeniedError("Runtime principal is inactive.")
        if (
            requested_tenant_id != cls._tenant_id(user)
            or requested_snapshot_ref != f"permission:user:{user_id}"
        ):
            raise IamRuntimeAccessDeniedError(
                "Runtime permission snapshot context is invalid."
            )
        authority = await cls._build_frontend_authority(
            user=user,
            component_type=cls.normalize_required_text(
                request_data.get("component_type"),
                "component_type",
            ),
            requested_capabilities=frozenset(cls.ensure_string_list(
                request_data.get("capabilities"),
                "capabilities",
            )),
            expires_at=cls._parse_expiry(request_data.get("expires_at")),
        )
        if authority is None:
            raise IamRuntimeAccessDeniedError("Runtime permission snapshot is denied.")
        return authority.to_wire()

    @classmethod
    async def issue_runtime_node_credential(cls, data: dict[str, Any]) -> dict[str, Any]:
        request_data = cls.ensure_dict(data)
        roles = cls._runtime_roles(request_data.get("roles"))
        capabilities = frozenset(cls.ensure_string_list(
            request_data.get("capabilities"),
            "capabilities",
        ))
        credential = await cls._runtime_node_authority().issue(
            identity=cls.normalize_required_text(request_data.get("identity"), "identity"),
            tenant_id=cls.normalize_required_text(request_data.get("tenant_id"), "tenant_id"),
            roles=roles,
            capabilities=capabilities,
        )
        return cls._serialize_runtime_node_credential(credential)

    @classmethod
    async def refresh_runtime_node_credential(cls, data: dict[str, Any]) -> dict[str, Any]:
        request_data = cls.ensure_dict(data)
        authority = cls._runtime_node_authority()
        token = cls.normalize_required_text(request_data.get("credential"), "credential")
        current = await authority.verify(token)
        if current is None:
            raise IamRuntimeAccessDeniedError("Runtime node credential is invalid.")
        refreshed = await authority.refresh(current)
        return cls._serialize_runtime_node_credential(refreshed)

    @classmethod
    async def revoke_runtime_node_credential(cls, data: dict[str, Any]) -> dict[str, Any]:
        request_data = cls.ensure_dict(data)
        credential_id = cls.normalize_required_text(
            request_data.get("credential_id"),
            "credential_id",
        )
        await cls._runtime_node_authority().revoke(credential_id)
        return {"revoked": True, "credential_id": credential_id}

    @classmethod
    async def runtime_bootstrap(cls, data: dict[str, Any]) -> dict[str, Any]:
        request_data = cls.ensure_dict(data)
        authority = cls._runtime_node_authority()
        credential = await authority.verify(cls.normalize_required_text(
            request_data.get("credential"),
            "credential",
        ))
        if credential is None:
            raise IamRuntimeAccessDeniedError("Runtime node credential is invalid.")
        try:
            request = RuntimeBootstrapRequest(
                runtime_id=cls.normalize_required_text(request_data.get("runtime_id"), "runtime_id"),
                requested_role=RuntimeRoleScope(
                    cls.normalize_required_text(request_data.get("requested_role"), "requested_role")
                ),
                credential_id=credential.credential_id,
            )
        except ValueError:
            raise IamRuntimeRequestInvalidError("Runtime role is invalid.") from None
        result = RuntimeBootstrapPolicy(
            config_version=str(getattr(settings, "IAM_RUNTIME_CONFIG_VERSION", "0")),
            policy_version=str(getattr(settings, "IAM_RUNTIME_POLICY_VERSION", "0")),
        ).authorize(request, credential=credential)
        return {
            "role_authorized": result.role_authorized,
            "authorized_roles": sorted(item.value for item in result.authorized_roles),
            "candidate_master": result.candidate_master,
            "config_version": result.config_version,
            "policy_version": result.policy_version,
        }

    @classmethod
    async def validate_payload_ref(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Freeze P06 validation shape while P10 payload storage stays absent."""
        request_data = cls.ensure_dict(data)
        target_data = cls.ensure_dict(request_data.get("target"))
        PayloadRefValidationRequest(
            object_id=cls.normalize_required_text(request_data.get("object_id"), "object_id"),
            version=cls.normalize_required_text(request_data.get("version"), "version"),
            checksum=cls.normalize_required_text(request_data.get("checksum"), "checksum"),
            tenant_id=cls.normalize_required_text(request_data.get("tenant_id"), "tenant_id"),
            owner_identity=cls.normalize_required_text(
                request_data.get("owner_identity"), "owner_identity"
            ),
            source_identity=cls.normalize_required_text(
                request_data.get("source_identity"), "source_identity"
            ),
            target=IamTargetContext(
                kind=cls.normalize_required_text(target_data.get("kind"), "target.kind"),
                tenant_id=cls.normalize_optional(target_data.get("tenant_id")),
                reference=cls.normalize_optional(target_data.get("reference")),
            ),
            callback_message_type=cls.normalize_optional(
                request_data.get("callback_message_type")
            ),
        )
        result = PayloadRefValidationResult(
            valid=False,
            reason="payload_storage_not_implemented",
            expires_at=timezone.now(),
            revoked=False,
        )
        return result.to_wire()

    @classmethod
    async def revalidate_payload_ref(
        cls,
        data: dict[str, Any],
        *,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Bind live payload metadata to one object-level ACL/policy decision."""

        try:
            request = PayloadRefRevalidationRequest.from_wire(
                cls.ensure_dict(data),
            )
        except Exception as error:
            raise IamRuntimeRequestInvalidError(
                "Payload reference revalidation request is invalid.",
            ) from error
        now = timezone.now()
        provider = getattr(settings, "IAM_PAYLOAD_REF_PROVIDER", None)
        if provider is None or not callable(getattr(provider, "validate", None)):
            return cls._payload_revalidation_decision(
                request=request,
                valid=False,
                allowed=False,
                reason="payload_storage_not_implemented",
                permission_version=request.permission_version,
                decided_at=now,
                expires_at=now,
            ).to_wire()
        try:
            metadata = await provider.validate(request)
        except Exception:
            return cls._payload_revalidation_decision(
                request=request,
                valid=False,
                allowed=False,
                reason="payload_provider_unavailable",
                permission_version=request.permission_version,
                decided_at=now,
                expires_at=now,
            ).to_wire()
        if type(metadata) is not PayloadRefValidationResult:
            raise IamRuntimeRequestInvalidError(
                "Payload provider returned an invalid result.",
            )
        metadata_valid = bool(
            metadata.valid
            and not metadata.revoked
            and metadata.object_id == request.object_id
            and metadata.version == request.version
            and metadata.checksum == request.checksum
            and metadata.size_bytes == request.size_bytes
            and metadata.tenant_id == request.tenant_id
            and metadata.expires_at > now
        )
        if not metadata_valid:
            return cls._payload_revalidation_decision(
                request=request,
                valid=False,
                allowed=False,
                reason="payload_metadata_invalid",
                permission_version=request.permission_version,
                decided_at=now,
                expires_at=now,
            ).to_wire()
        try:
            user_id = cls._user_id_from_identity(request.target_principal)
        except IamRuntimeRequestInvalidError:
            user_id = 0
        user = (
            None
            if user_id == 0
            else await AuthUserRepository.get_user_by_id(user_id)
        )
        if user is None or not bool(getattr(user, "is_active", False)):
            return cls._payload_revalidation_decision(
                request=request,
                valid=True,
                allowed=False,
                reason="principal_inactive",
                permission_version=request.permission_version,
                decided_at=now,
                expires_at=metadata.expires_at,
            ).to_wire()
        permission_codes = await PermissionService.list_permission_codes(user)
        current_version, _ = cls._permission_metadata(
            user_id=user_id,
            tenant_id=cls._tenant_id(user),
            permission_codes=permission_codes,
        )
        snapshot_valid = (
            request.permission_snapshot_ref == f"permission:user:{user_id}"
            and request.permission_version == current_version
            and request.target_tenant_id == cls._tenant_id(user)
            and request.target_tenant_id == request.tenant_id
        )
        if not snapshot_valid:
            return cls._payload_revalidation_decision(
                request=request,
                valid=True,
                allowed=False,
                reason="permission_snapshot_or_tenant_mismatch",
                permission_version=current_version,
                decided_at=now,
                expires_at=metadata.expires_at,
                refresh_required=(request.permission_version != current_version),
            ).to_wire()
        access = await AccessDecisionService.check_with_audit(
            user=user,
            data={
                "resource_type": "payload_ref",
                "resource_id": request.object_id,
                "action_code": "read",
                "permission_code": "payload_ref.read",
            },
            trace_id=trace_id,
        )
        allowed = type(access) is dict and access.get("allowed") is True
        return cls._payload_revalidation_decision(
            request=request,
            valid=True,
            allowed=allowed,
            reason=(
                str(access.get("reason", "object_access_denied"))
                if type(access) is dict
                else "object_access_denied"
            ),
            permission_version=current_version,
            decided_at=now,
            expires_at=metadata.expires_at,
        ).to_wire()

    @classmethod
    def _payload_revalidation_decision(
        cls,
        *,
        request: PayloadRefRevalidationRequest,
        valid: bool,
        allowed: bool,
        reason: str,
        permission_version: str,
        decided_at,
        expires_at,
        refresh_required: bool = False,
    ) -> PayloadRefRevalidationDecision:
        material = "\0".join((
            request.object_id,
            request.version,
            request.checksum,
            request.tenant_id,
            request.target_principal,
            request.target_fingerprint,
            request.permission_snapshot_ref,
            permission_version,
            request.admission_authority_reference,
            "1" if valid else "0",
            "1" if allowed else "0",
            decided_at.isoformat(),
        )).encode("utf-8")
        raw_key = str(getattr(settings, "JWT_SECRET_KEY", "") or settings.SECRET_KEY)
        decision_reference = "iam-payload:" + hmac.new(
            raw_key.encode("utf-8"),
            material,
            hashlib.sha256,
        ).hexdigest()
        return PayloadRefRevalidationDecision(
            valid=valid,
            allowed=allowed,
            reason=reason,
            object_id=request.object_id,
            version=request.version,
            checksum=request.checksum,
            size_bytes=request.size_bytes,
            tenant_id=request.tenant_id,
            target_principal=request.target_principal,
            target_fingerprint=request.target_fingerprint,
            permission_snapshot_ref=request.permission_snapshot_ref,
            permission_version=permission_version,
            decision_reference=decision_reference,
            decided_at=decided_at,
            expires_at=expires_at,
            refresh_required=refresh_required,
        )

    @staticmethod
    def _runtime_node_authority() -> RuntimeNodeCredentialAuthority:
        raw_key = str(getattr(settings, "JWT_SECRET_KEY", "") or settings.SECRET_KEY)
        signing_key = hmac.new(
            raw_key.encode("utf-8"),
            b"ns_runtime_node_credential:iam-r1",
            hashlib.sha256,
        ).digest()
        return RuntimeNodeCredentialAuthority(
            signing_key=signing_key,
            status_store=DjangoRuntimeCredentialStatusStore(),
            clock=SystemClock(),
            ttl_seconds=int(getattr(settings, "IAM_RUNTIME_NODE_CREDENTIAL_TTL_SECONDS", 900)),
        )

    @staticmethod
    def _runtime_roles(value: Any) -> frozenset[RuntimeRoleScope]:
        if not isinstance(value, list):
            raise IamRuntimeRequestInvalidError("roles must be a list.")
        try:
            roles = frozenset(RuntimeRoleScope(item) for item in value)
        except (TypeError, ValueError):
            raise IamRuntimeRequestInvalidError("roles contain an invalid role.") from None
        if not roles or len(roles) != len(value):
            raise IamRuntimeRequestInvalidError("roles must be unique and non-empty.")
        return roles

    @staticmethod
    def _serialize_runtime_node_credential(credential: Any) -> dict[str, Any]:
        return {
            "credential_id": credential.credential_id,
            "credential": credential.token,
            "identity": credential.identity,
            "tenant_id": credential.tenant_id,
            "roles": sorted(item.value for item in credential.roles),
            "capabilities": sorted(credential.capabilities),
            "issued_at": credential.issued_at.isoformat(),
            "expires_at": credential.expires_at.isoformat(),
        }

    @classmethod
    async def _build_frontend_authority(
        cls,
        *,
        user: Any,
        component_type: str,
        requested_capabilities: frozenset[str],
        expires_at: Any,
    ) -> IamIntrospectionResult | None:
        allowed_components = {"frontend", "client"}
        capabilities = set(cls._BASE_RUNTIME_CAPABILITIES)
        if bool(getattr(user, "is_staff", False)) or bool(getattr(user, "is_superuser", False)):
            allowed_components.add("management")
            capabilities.add("runtime.management")
        if component_type not in allowed_components:
            return None
        if not requested_capabilities.issubset(capabilities):
            return None
        user_id = int(getattr(user, "id"))
        tenant_id = cls._tenant_id(user)
        permission_codes = await PermissionService.list_permission_codes(user)
        version, digest = cls._permission_metadata(
            user_id=user_id,
            tenant_id=tenant_id,
            permission_codes=permission_codes,
        )
        now = timezone.now()
        ttl_expiry = now + timedelta(
            seconds=int(getattr(settings, "IAM_AUTHZ_CACHE_TTL_SECONDS", 300)),
        )
        effective_expiry = min(expires_at, ttl_expiry)
        if effective_expiry <= now:
            return None
        return IamIntrospectionResult(
            identity=f"user:{user_id}",
            tenant_id=tenant_id,
            principal_type=IamPrincipalType.FRONTEND_USER,
            component_type=component_type,
            capabilities=requested_capabilities,
            permission_snapshot_ref=f"permission:user:{user_id}",
            permission_digest=digest,
            permission_version=version,
            issued_at=now,
            expires_at=effective_expiry,
            credential_status=IamCredentialStatus.ACTIVE,
            resume_eligible=True,
        )

    @staticmethod
    def _tenant_id(user: Any) -> str:
        company_id = getattr(user, "company_id", None)
        return (
            f"company:{int(company_id)}"
            if company_id is not None
            else f"user:{int(getattr(user, 'id'))}"
        )

    @staticmethod
    def _permission_metadata(
        *,
        user_id: int,
        tenant_id: str,
        permission_codes: list[str],
    ) -> tuple[str, str]:
        canonical = "\n".join((str(user_id), tenant_id, *sorted(permission_codes)))
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return f"version:{digest[:24]}", f"sha256:{digest}"

    @staticmethod
    def _parse_expiry(value: Any) -> datetime:
        if not isinstance(value, str):
            raise IamRuntimeRequestInvalidError("expires_at is invalid.")
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            raise IamRuntimeRequestInvalidError("expires_at is invalid.") from None
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise IamRuntimeRequestInvalidError("expires_at is invalid.")
        parsed = parsed.astimezone(datetime_timezone.utc)
        if parsed <= timezone.now():
            raise IamRuntimeAccessDeniedError("Permission snapshot is expired.")
        return parsed

    @staticmethod
    def _user_id_from_identity(identity: str) -> int:
        prefix, separator, raw_id = identity.partition(":")
        if prefix != "user" or separator != ":":
            raise IamRuntimeRequestInvalidError("Runtime identity is invalid.")
        try:
            user_id = int(raw_id)
        except ValueError:
            raise IamRuntimeRequestInvalidError("Runtime identity is invalid.") from None
        if user_id <= 0:
            raise IamRuntimeRequestInvalidError("Runtime identity is invalid.")
        return user_id

    @classmethod
    async def access_check(cls, data: dict[str, Any], *, trace_id: str | None = None) -> dict[str, Any]:
        request_data = cls.ensure_dict(data)
        principal = cls.ensure_principal(request_data.get("principal"))

        user_id = cls.resolve_user_id_from_principal(principal)

        user = await AuthUserRepository.get_user_by_id(user_id)
        if user is None or not bool(getattr(user, "is_active", False)):
            return cls.deny_decision(
                reason="USER_INACTIVE",
                request_data=request_data,
                principal=principal,
                trace_id=trace_id,
            )

        access_data = cls.attach_runtime_context(
            request_data=request_data,
            principal=principal,
        )

        return await AccessDecisionService.check_with_audit(
            user=user,
            data=access_data,
            trace_id=trace_id,
        )

    @classmethod
    async def batch_access_check(cls, data: dict[str, Any], *, trace_id: str | None = None) -> dict[str, Any]:
        request_data = cls.ensure_dict(data)
        items = request_data.get("items") or request_data.get("requests") or []
        principal = request_data.get("principal")

        if not isinstance(items, list):
            raise IamRuntimeRequestInvalidError(
                "items must be a list.",
            )

        results = []

        for item in items:
            if not isinstance(item, dict):
                results.append(
                    cls.deny_decision(
                        reason="REQUEST_ITEM_INVALID",
                        request_data={},
                        principal={},
                        trace_id=trace_id,
                    )
                )
                continue

            item_data = dict(item)
            if "principal" not in item_data and isinstance(principal, dict):
                item_data["principal"] = dict(principal)

            results.append(
                await cls.access_check(
                    item_data,
                    trace_id=trace_id,
                )
            )

        return {
            "items": results,
            "total": len(results),
        }

    @classmethod
    async def resolve_resource_filter(cls, data: dict[str, Any], *, trace_id: str | None = None) -> dict[str, Any]:
        request_data = cls.ensure_dict(data)
        principal = cls.ensure_principal(request_data.get("principal"))

        user_id = cls.resolve_user_id_from_principal(principal)

        user = await AuthUserRepository.get_user_by_id(user_id)
        if user is None or not bool(getattr(user, "is_active", False)):
            result = ResourceAccessFilterService.build_deny_all_filter(
                reason="USER_INACTIVE",
            )
            result["trace_id"] = trace_id
            return result

        raw_field_map = request_data.get("field_map")
        field_map = raw_field_map if isinstance(raw_field_map, dict) else None

        result = await ResourceAccessFilterService.resolve_retrieval_filter(
            user=user,
            resource_type=request_data.get("resource_type"),
            action_code=request_data.get("action_code"),
            permission_code=cls.normalize_optional(request_data.get("permission_code")),
            field_map=field_map,
        )

        result["trace_id"] = trace_id
        return result

    @classmethod
    def attach_runtime_context(cls, *, request_data: dict[str, Any], principal: dict[str, Any]) -> dict[str, Any]:
        access_data = dict(request_data)

        raw_context = access_data.get("context")
        if isinstance(raw_context, dict):
            context = dict(raw_context)
        else:
            context = {}

        context.setdefault(
            "runtime_principal",
            dict(principal),
        )
        context.setdefault(
            "runtime_principal_type",
            cls.normalize_optional(principal.get("principal_type")),
        )
        context.setdefault(
            "runtime_principal_id",
            cls.normalize_optional(principal.get("principal_id")),
        )
        context.setdefault(
            "runtime_client_id",
            cls.normalize_optional(principal.get("client_id")),
        )
        context.setdefault(
            "runtime_session_id",
            cls.normalize_optional(principal.get("session_id")),
        )

        access_data["context"] = context
        return access_data

    @classmethod
    def resolve_user_id_from_principal(cls, principal: dict[str, Any]) -> int:
        principal_type = str(principal.get("principal_type") or "").strip()

        if principal_type != cls.PRINCIPAL_TYPE_FRONTEND_USER:
            raise IamRuntimeRequestInvalidError(
                "Unsupported runtime principal type.",
                details={
                    "principal_type": principal_type,
                },
            )

        user_id_text = cls.normalize_required_text(
            principal.get("user_id") or principal.get("principal_id"),
            "principal.user_id",
        )

        try:
            user_id = int(user_id_text)
        except (TypeError, ValueError) as exc:
            raise IamRuntimeRequestInvalidError(
                "principal.user_id is invalid.",
                details={
                    "user_id": user_id_text,
                },
            ) from exc

        if user_id <= 0:
            raise IamRuntimeRequestInvalidError(
                "principal.user_id is invalid.",
                details={
                    "user_id": user_id,
                },
            )

        return user_id

    @classmethod
    def deny_decision(cls, *, reason: str, request_data: dict[str, Any], principal: dict[str, Any], trace_id: str | None) -> dict[str, Any]:
        return {
            "allowed": False,
            "effect": "deny",
            "reason": reason,
            "matched_source": "runtime_iam_internal",
            "resource_type": cls.normalize_optional(request_data.get("resource_type")),
            "resource_id": cls.normalize_optional(request_data.get("resource_id")),
            "action_code": cls.normalize_optional(request_data.get("action_code")),
            "permission_code": cls.normalize_optional(request_data.get("permission_code")),
            "filters": {},
            "hit_details": {
                "principal": dict(principal or {}),
            },
            "decision_chain": [
                {
                    "source": "runtime_iam_internal",
                    "effect": "deny",
                    "reason": reason,
                }
            ],
            "trace_id": trace_id,
        }

    @staticmethod
    def ensure_dict(data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise IamRuntimeRequestInvalidError(
                "Request payload must be an object.",
            )

        return dict(data)

    @staticmethod
    def ensure_principal(value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise IamRuntimeRequestInvalidError(
                "principal must be an object.",
            )

        return dict(value)

    @staticmethod
    def normalize_required_text(value: Any, field_name: str) -> str:
        normalized = str(value or "").strip()

        if not normalized:
            raise IamRuntimeRequestInvalidError(
                f"{field_name} is required.",
                details={
                    "field": field_name,
                },
            )

        return normalized

    @staticmethod
    def normalize_optional(value: Any) -> str | None:
        if value is None:
            return None

        normalized = str(value).strip()
        return normalized or None

    @staticmethod
    def ensure_string_list(value: Any, field_name: str) -> list[str]:
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            raise IamRuntimeRequestInvalidError(
                f"{field_name} must be a string list.",
                details={"field": field_name},
            )
        if len(value) != len(set(value)):
            raise IamRuntimeRequestInvalidError(
                f"{field_name} contains duplicates.",
                details={"field": field_name},
            )
        return value

    @staticmethod
    def ensure_bool(value: Any, field_name: str) -> bool:
        if not isinstance(value, bool):
            raise IamRuntimeRequestInvalidError(
                f"{field_name} must be a boolean.",
                details={"field": field_name},
            )
        return value

    @staticmethod
    def serialize_user(user: Any) -> dict[str, Any]:
        return {
            "id": getattr(user, "id", None),
            "username": getattr(user, "username", None),
            "display_name": getattr(user, "display_name", None),
            "user_type": getattr(user, "user_type", None),
            "is_active": bool(getattr(user, "is_active", False)),
            "is_staff": bool(getattr(user, "is_staff", False)),
            "is_superuser": bool(getattr(user, "is_superuser", False)),
            "company_id": getattr(user, "company_id", None),
            "subsidiary_id": getattr(user, "subsidiary_id", None),
            "department_id": getattr(user, "department_id", None),
        }
