# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, date
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.constants import (
    USER_TYPE_ENTERPRISE,
    USER_TYPE_PERSONAL,
    DATA_SCOPE_ALL,
    DATA_SCOPE_LEVELS,
    DATA_SCOPE_SELF,
    DATA_SCOPE_DEPARTMENT,
    DATA_SCOPE_DEPARTMENT_AND_CHILDREN,
    DATA_SCOPE_SUBSIDIARY,
    DATA_SCOPE_ORGANIZATION,
    normalize_data_scope,
    ROLE_SCOPE_PERSONAL,
    ROLE_SCOPE_ENTERPRISE,
    PERMISSION_TYPE_DATA,
    PERMISSION_EFFECT_DENY,
    PERMISSION_EFFECT_ALLOW,
)
from ns_backend.iam.errors import IamDomainError
from ns_backend.iam.schemas import TenantContext, DataScopeResult, DataScopeFilterPlan, DataScopeFieldMap, AuditEvent
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class AuditPolicy:
    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAILED = "FAILED"
    MAX_AUDIT_STRING_LENGTH = 2048
    MAX_AUDIT_JSON_LENGTH = 32768

    SENSITIVE_KEYS = {
        "password",
        "password_payload",
        "passwordpayload",
        "raw_password",
        "rawpassword",
        "encrypted_password",
        "encryptedpassword",
        "password_ciphertext",
        "passwordciphertext",
        "ciphertext",
        "plain_text",
        "plaintext",
        "decrypted_password",
        "decryptedpassword",
        "password_plaintext",
        "passwordplaintext",
        "old_password",
        "new_password",
        "confirm_password",
        "oldpassword",
        "newpassword",
        "confirmpassword",
        "refresh_token",
        "access_token",
        "refreshtoken",
        "accesstoken",
        "token",
        "authtoken",
        "auth_token",
        "sessiontoken",
        "session_token",
        "authorization",
        "bearer",
        "jwt",
        "jwt_token",
        "secret",
        "client_secret",
        "clientsecret",
        "api_key",
        "apikey",
        "secret_key",
        "secretkey",
        "private_key",
        "privatekey",
        "rsa_private_key",
        "rsaprivatekey",
        "rsa_private_key_file",
        "rsaprivatekeyfile",
        "rsa_private_key_passphrase",
        "rsaprivatekeypassphrase",
        "private_key_file",
        "privatekeyfile",
        "private_key_pem",
        "privatekeypem",
        "key_passphrase",
        "keypassphrase",
        "passphrase",
        "csrf",
        "csrf_token",
        "csrftoken",
    }

    @staticmethod
    def normalize_sensitive_key(key: Any) -> str:
        return str(key).strip().lower()

    @staticmethod
    def compact_sensitive_key(key: Any) -> str:
        normalized = str(key).strip().lower()
        return "".join(ch for ch in normalized if ch not in {"_", "-", ".", " "})

    @classmethod
    def normalize_sensitive_key_variants(cls, keys: Any) -> set[str]:
        if keys is None:
            return set()

        items = keys if isinstance(keys, (list, tuple, set)) else (keys,)
        variants: set[str] = set()
        for key in items:
            if not isinstance(key, str):
                continue
            text = key.strip()
            if not text:
                continue
            variants.add(cls.normalize_sensitive_key(text))
            variants.add(cls.compact_sensitive_key(text))
        return variants

    @classmethod
    def get_configured_sensitive_keys(cls) -> set[str]:
        try:
            from django.conf import settings

            extra_keys = getattr(settings, "IAM_AUDIT_EXTRA_SENSITIVE_KEYS", ())
        except Exception:  # noqa
            return set()

        return cls.normalize_sensitive_key_variants(extra_keys)

    @classmethod
    def get_effective_sensitive_keys(cls) -> set[str]:
        return cls.SENSITIVE_KEYS | cls.get_configured_sensitive_keys()

    @classmethod
    def is_sensitive_key(cls, key: Any) -> bool:
        normalized = cls.normalize_sensitive_key(key)
        compact = cls.compact_sensitive_key(key)
        sensitive_keys = cls.get_effective_sensitive_keys()
        return normalized in sensitive_keys or compact in sensitive_keys

    @classmethod
    def to_json_safe(cls, value: Any) -> Any:
        if value is None or isinstance(value, (str, int, float, bool)):
            return value

        if isinstance(value, (datetime, date)):
            return value.isoformat()

        if isinstance(value, (Decimal, UUID)):
            return str(value)

        if isinstance(value, bytes):
            return value.decode("utf-8", errors="replace")

        if isinstance(value, dict):
            return {str(key): cls.to_json_safe(item) for key, item in value.items()}

        if isinstance(value, (list, tuple, set)):
            return [cls.to_json_safe(item) for item in value]

        return str(value)

    @classmethod
    def mask_sensitive_data(cls, data: Any) -> Any:
        if data is None:
            return None

        if isinstance(data, dict):
            masked: dict[str, Any] = {}
            for key, value in data.items():
                normalized_key = str(key)
                if cls.is_sensitive_key(key):
                    masked[normalized_key] = "***"
                    continue
                masked[normalized_key] = cls.mask_sensitive_data(value)
            return masked

        if isinstance(data, (list, tuple, set)):
            return [cls.mask_sensitive_data(item) for item in data]

        return cls.to_json_safe(data)

    @classmethod
    def get_json_length(cls, value: Any) -> int:
        try:
            return len(json.dumps(value, ensure_ascii=False, default=str))
        except Exception:  # noqa
            return len(str(value))

    @classmethod
    def limit_audit_value(cls, value: Any) -> Any:
        safe_value = cls.to_json_safe(value)
        if isinstance(safe_value, str) and len(safe_value) > cls.MAX_AUDIT_STRING_LENGTH:
            return {
                "__truncated__": True,
                "type": "string",
                "length": len(safe_value),
                "value": safe_value[:cls.MAX_AUDIT_STRING_LENGTH],
            }
        return safe_value

    @classmethod
    def limit_audit_payload(cls, value: Any) -> Any:
        if value is None:
            return None

        if isinstance(value, dict):
            limited_obj = {str(key): cls.limit_audit_payload(item) for key, item in value.items()}
            json_length = cls.get_json_length(limited_obj)
            if json_length > cls.MAX_AUDIT_JSON_LENGTH:
                return {
                    "__truncated__": True,
                    "type": "object",
                    "length": json_length,
                }
            return limited_obj

        if isinstance(value, (list, tuple, set)):
            limited_arr = [cls.limit_audit_payload(item) for item in value]
            json_length = cls.get_json_length(limited_arr)
            if json_length > cls.MAX_AUDIT_JSON_LENGTH:
                return {
                    "__truncated__": True,
                    "type": "array",
                    "length": json_length,
                }
            return limited_arr

        return cls.limit_audit_value(value)

    @classmethod
    def normalize_payload(cls, value: Any) -> Any:
        masked = cls.mask_sensitive_data(value)
        return cls.limit_audit_payload(masked)

    @classmethod
    def normalize_status(cls, status: str | None) -> str:
        if status == cls.STATUS_FAILED:
            return cls.STATUS_FAILED
        return cls.STATUS_SUCCESS

    @staticmethod
    def truncate(value: str | None, max_length: int) -> str | None:
        if value is None:
            return None
        return str(value)[:max_length]

    @classmethod
    def normalize_event(cls, event: AuditEvent) -> AuditEvent:
        if not event.operation_type:
            raise BusinessError("operation_type is required", NsErrorCode.AUDIT_OPERATION_TYPE_REQUIRED)

        if not event.resource_type:
            raise BusinessError("resource_type is required", NsErrorCode.AUDIT_RESOURCE_TYPE_REQUIRED)

        return replace(
            event,
            operation_type=cls.truncate(event.operation_type, 64),
            resource_type=cls.truncate(event.resource_type, 64),
            request_method=cls.truncate(event.request_method, 16),
            request_path=cls.truncate(event.request_path, 255),
            client_ip=cls.truncate(event.client_ip, 64),
            user_agent=cls.truncate(event.user_agent, 512),
            request_data=cls.normalize_payload(event.request_data),
            before_data=cls.normalize_payload(event.before_data),
            after_data=cls.normalize_payload(event.after_data),
            extra_data=cls.normalize_payload(event.extra_data),
            status=cls.normalize_status(event.status),
            error_message=cls.truncate(event.error_message, 512),
            trace_id=cls.truncate(event.trace_id, 64),
        )


class BasePolicy:
    @staticmethod
    def deny(message: str, code: int) -> None:
        raise IamDomainError(message=message, code=code)

    @classmethod
    def ensure(cls, condition: bool, message: str, code: int) -> None:
        if not condition:
            cls.deny(message, code)

    @staticmethod
    def is_truthy(value: object) -> bool:
        return value in (True, 1, "1", "true", "True")

    @staticmethod
    def is_falsy(value: object) -> bool:
        return value in (False, 0, "0", "false", "False")


class DataScopePolicy(BasePolicy):
    @classmethod
    def denied_result(cls) -> DataScopeResult:
        return DataScopeResult(allowed=False)

    @classmethod
    def platform_all_result(cls) -> DataScopeResult:
        return DataScopeResult(allowed=True, scope=DATA_SCOPE_ALL, is_platform_scope=True)

    @classmethod
    def select_max_scope(cls, scopes: list[str]) -> str | None:
        if not scopes:
            return None
        valid_scopes = [scope for scope in scopes if scope in DATA_SCOPE_LEVELS]
        if not valid_scopes:
            return None
        return max(valid_scopes, key=lambda item: DATA_SCOPE_LEVELS[item])

    @classmethod
    def normalize_personal_scope(cls, scopes: list[str]) -> str | None:
        return DATA_SCOPE_SELF if scopes else None

    @classmethod
    def build_result_for_user(cls, *, user: Any, scope: str | None, department_ids: list[int] | None = None) -> DataScopeResult:
        normalized_scope = normalize_data_scope(scope)
        if not normalized_scope:
            return cls.denied_result()

        base_kwargs = {
            "allowed": True,
            "scope": scope,
            "company_id": user.company_id,
            "subsidiary_id": user.subsidiary_id,
            "department_id": user.department_id,
            "user_id": user.id, "is_platform_scope": False
        }

        if normalized_scope == DATA_SCOPE_SELF:
            return DataScopeResult(**base_kwargs, department_ids=[])

        if normalized_scope == DATA_SCOPE_DEPARTMENT:
            if not user.department_id:
                return cls.denied_result()
            return DataScopeResult(**base_kwargs, department_ids=[user.department_id])

        if normalized_scope == DATA_SCOPE_DEPARTMENT_AND_CHILDREN:
            if not user.department_id or not department_ids:
                return cls.denied_result()
            return DataScopeResult(**base_kwargs, department_ids=department_ids)

        if normalized_scope == DATA_SCOPE_SUBSIDIARY:
            if not user.subsidiary_id:
                return cls.denied_result()
            return DataScopeResult(**base_kwargs, department_ids=[])

        if normalized_scope == DATA_SCOPE_ORGANIZATION:
            if not user.company_id:
                return cls.denied_result()
            return DataScopeResult(**base_kwargs, department_ids=[])

        if normalized_scope == DATA_SCOPE_ALL:
            if not user.company_id:
                return cls.denied_result()
            return DataScopeResult(**base_kwargs, department_ids=[])

        return cls.denied_result()

    @classmethod
    def build_filter_plan(cls, *, scope: DataScopeResult, field_map: DataScopeFieldMap) -> DataScopeFilterPlan:
        if not scope.allowed:
            return DataScopeFilterPlan(allowed=False, reason="DATA_SCOPE_DENIED")

        if scope.is_platform_scope:
            return DataScopeFilterPlan(allowed=True, filters={}, is_platform_scope=True)

        normalized_scope = normalize_data_scope(scope.scope)
        if normalized_scope == DATA_SCOPE_SELF:
            if not field_map.self_field:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_SELF_FIELD")
            if scope.user_id is None:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_USER_ID")
            return DataScopeFilterPlan(allowed=True, filters={field_map.self_field: scope.user_id})

        if normalized_scope == DATA_SCOPE_DEPARTMENT:
            if not field_map.department_field:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_DEPARTMENT_FIELD")
            if scope.department_id is None:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_DEPARTMENT_ID")
            return DataScopeFilterPlan(allowed=True, filters={field_map.department_field: scope.department_id})

        if normalized_scope == DATA_SCOPE_DEPARTMENT_AND_CHILDREN:
            if not field_map.department_field:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_DEPARTMENT_FIELD")
            if not scope.department_ids:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_DEPARTMENT_IDS")
            return DataScopeFilterPlan(allowed=True, filters={f"{field_map.department_field}__in": scope.department_ids})

        if normalized_scope == DATA_SCOPE_SUBSIDIARY:
            if not field_map.subsidiary_field:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_SUBSIDIARY_FIELD")
            if scope.subsidiary_id is None:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_SUBSIDIARY_ID")
            return DataScopeFilterPlan(allowed=True, filters={field_map.subsidiary_field: scope.subsidiary_id})

        if normalized_scope in {DATA_SCOPE_ORGANIZATION, DATA_SCOPE_ALL}:
            if not field_map.company_field:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_COMPANY_FIELD")
            if scope.company_id is None:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_COMPANY_ID")
            return DataScopeFilterPlan(allowed=True, filters={field_map.company_field: scope.company_id})

        return DataScopeFilterPlan(allowed=False, reason="UNKNOWN_DATA_SCOPE")

    @classmethod
    def ensure_grant_data_scope_by_permission_type(cls, *, permission_type: str | None, data_scope: str | None, effect: str | None = None, role_permission: bool = False) -> None:
        if permission_type is None:
            cls.deny("Permission does not exist", NsErrorCode.DATA_NOT_FOUND)

        if permission_type != PERMISSION_TYPE_DATA:
            if data_scope:
                cls.deny("Data scope cannot be set for non-data permissions", NsErrorCode.DATA_SCOPE_NOT_ALLOWED_FOR_NON_DATA)
            return

        if role_permission:
            if not data_scope:
                cls.deny("Data permissions must set data scope", NsErrorCode.DATA_SCOPE_REQUIRED)
            return

        if effect == PERMISSION_EFFECT_DENY:
            if data_scope:
                cls.deny("DENY permissions cannot set data scope", NsErrorCode.DATA_SCOPE_FORBIDDEN_FOR_DENY)
            return

        if effect == PERMISSION_EFFECT_ALLOW and not data_scope:
            cls.deny("Data permissions must set data scope", NsErrorCode.DATA_SCOPE_REQUIRED)


class GrantPolicy(BasePolicy):
    """IAM grant boundary policy."""

    @classmethod
    async def ensure_can_bind_user_role(cls, *, user_id: int, role_id: int, operator: Any) -> None:
        """Ensure operator can bind role to user."""
        from ns_backend.iam.repositories import GrantBoundaryRepository
        from ns_backend.iam.services.tenant import TenantService

        if not await GrantBoundaryRepository.user_exists(user_id):
            cls.deny("User does not exist", NsErrorCode.USER_NOT_FOUND)

        role_info = await GrantBoundaryRepository.get_role_scope_and_company_id(role_id)
        if not role_info:
            cls.deny("Role does not exist", NsErrorCode.DATA_NOT_FOUND)

        user_company_id = await GrantBoundaryRepository.get_user_company_id(user_id)
        role_scope, role_company_id = role_info
        context = TenantService.from_user(operator)

        if TenantPolicy.is_platform_admin(context):
            if role_scope == ROLE_SCOPE_PERSONAL and user_company_id is not None:
                cls.deny("Cannot bind user role across companies", 14031)

            if role_scope == ROLE_SCOPE_ENTERPRISE and user_company_id != role_company_id:
                cls.deny("Cannot bind user role across companies", 14031)

            return

        TenantPolicy.ensure_enterprise_context(context)
        operator_company_id = context.company_id

        if user_company_id != operator_company_id:
            cls.deny("Cannot operate users from other companies", 14033)

        if role_company_id != operator_company_id:
            cls.deny("Cannot operate roles from other companies", 14032)

        if user_company_id != role_company_id:
            cls.deny("Cannot bind user role across companies", 14031)

    @classmethod
    async def ensure_can_operate_role(cls, *, role_id: int, operator: Any) -> None:
        """Ensure operator can operate role."""
        from ns_backend.iam.repositories import GrantBoundaryRepository
        from ns_backend.iam.services.tenant import TenantService

        role_info = await GrantBoundaryRepository.get_role_scope_and_company_id(role_id)
        if not role_info:
            cls.deny("Role does not exist", NsErrorCode.DATA_NOT_FOUND)

        _, role_company_id = role_info
        context = TenantService.from_user(operator)

        if TenantPolicy.is_platform_admin(context):
            return

        TenantPolicy.ensure_enterprise_context(context)

        if role_company_id != context.company_id:
            cls.deny("Cannot operate roles from other companies", 14032)

    @classmethod
    async def ensure_can_operate_user(cls, *, user_id: int, operator: Any) -> None:
        """Ensure operator can operate user."""
        from ns_backend.iam.repositories import GrantBoundaryRepository
        from ns_backend.iam.services.tenant import TenantService

        if not await GrantBoundaryRepository.user_exists(user_id):
            cls.deny("User does not exist", NsErrorCode.USER_NOT_FOUND)

        user_company_id = await GrantBoundaryRepository.get_user_company_id(user_id)
        context = TenantService.from_user(operator)

        if TenantPolicy.is_platform_admin(context):
            return

        TenantPolicy.ensure_enterprise_context(context)

        if user_company_id != context.company_id:
            cls.deny("Cannot operate users from other companies", 14033)

    @classmethod
    async def ensure_can_operate_department(cls, *, department_id: int, operator: Any) -> None:
        """Ensure operator can operate department."""
        from ns_backend.iam.repositories import GrantBoundaryRepository
        from ns_backend.iam.services.tenant import TenantService

        department_company_id = await GrantBoundaryRepository.get_department_company_id(department_id)
        if department_company_id is None:
            cls.deny("Data not found", NsErrorCode.DATA_NOT_FOUND)

        context = TenantService.from_user(operator)

        if TenantPolicy.is_platform_admin(context):
            return

        TenantPolicy.ensure_enterprise_context(context)

        if department_company_id != context.company_id:
            cls.deny("Cannot operate departments from other companies", 14034)

    @classmethod
    async def ensure_can_operate_subsidiary(cls, *, subsidiary_id: int, operator: Any) -> None:
        """Ensure operator can operate subsidiary."""
        from ns_backend.iam.repositories import GrantBoundaryRepository
        from ns_backend.iam.services.tenant import TenantService

        subsidiary_company_id = await GrantBoundaryRepository.get_subsidiary_company_id(subsidiary_id)
        if subsidiary_company_id is None:
            cls.deny("Data not found", NsErrorCode.DATA_NOT_FOUND)

        context = TenantService.from_user(operator)

        if TenantPolicy.is_platform_admin(context):
            return

        TenantPolicy.ensure_enterprise_context(context)

        if subsidiary_company_id != context.company_id:
            cls.deny("Cannot operate subsidiaries from other companies", 14035)


class OrganizationPolicy(BasePolicy):
    """Organization boundary policy."""

    @classmethod
    def ensure_can_create_company(cls, context: TenantContext) -> None:
        """Only platform administrators can create companies."""
        TenantPolicy.ensure_platform_admin(context, "Only platform administrators can create companies", 14003)

    @classmethod
    def ensure_can_delete_company(cls, context: TenantContext) -> None:
        """Only platform administrators can delete companies."""
        TenantPolicy.ensure_platform_admin(context, "Only platform administrators can delete companies", 14004)

    @classmethod
    async def ensure_subsidiary_belongs_to_company(cls, *, subsidiary_id: int | None, company_id: int) -> None:
        """Ensure subsidiary belongs to company."""
        if not subsidiary_id:
            return

        from ns_backend.iam.repositories import OrganizationRepository

        subsidiary_company_id = await OrganizationRepository.get_subsidiary_company_id(subsidiary_id)
        if subsidiary_company_id != company_id:
            cls.deny("Subsidiary does not belong to the current company", 14041)

    @classmethod
    async def ensure_department_belongs_to_company(cls, *, department_id: int | None, company_id: int) -> None:
        """Ensure department belongs to company."""
        if not department_id:
            return

        from ns_backend.iam.repositories import OrganizationRepository

        department_company_id = await OrganizationRepository.get_department_company_id(department_id)
        if department_company_id != company_id:
            cls.deny("Department does not belong to the current company", 14042)

    @classmethod
    async def ensure_parent_department_belongs_to_company(cls, *, parent_id: int | None, company_id: int) -> None:
        """Ensure parent department belongs to company."""
        if not parent_id:
            return

        from ns_backend.iam.repositories import OrganizationRepository

        parent_company_id = await OrganizationRepository.get_department_company_id(parent_id)
        if parent_company_id != company_id:
            cls.deny("Parent department does not belong to the current company", 14043)


class RolePolicy(BasePolicy):
    """IAM role boundary policy."""

    @classmethod
    def normalize_company_id(cls, value: Any) -> int:
        """Normalize company id for role boundary policy."""
        try:
            company_id = int(value)
        except (TypeError, ValueError) as exc:
            raise IamDomainError(message="company_id is invalid", code=NsErrorCode.INVALID_VALUE) from exc

        if company_id <= 0:
            cls.deny("company_id is invalid", NsErrorCode.INVALID_VALUE)

        return company_id

    # noinspection PyTypeChecker
    @classmethod
    async def build_create_payload(cls, *, context: TenantContext | None, data: dict[str, Any]) -> dict[str, Any]:
        """Build tenant-safe role create payload."""
        from ns_backend.iam.repositories import RoleRepository

        role_scope = data.get("role_scope")
        role_code = data.get("role_code")
        final_data = dict(data)

        if role_scope == ROLE_SCOPE_PERSONAL:
            if context is None or not TenantPolicy.is_platform_admin(context):
                cls.deny("Only platform administrators can create PERSONAL roles", NsErrorCode.ROLE_PERSONAL_PLATFORM_ADMIN_ONLY)

            if final_data.get("company_id") is not None:
                cls.deny("PERSONAL roles cannot be bound to a company", NsErrorCode.ROLE_PERSONAL_COMPANY_FORBIDDEN)

            if await RoleRepository.exists_personal_role_code(role_code=role_code):
                cls.deny("Role code already exists", NsErrorCode.ROLE_CODE_ALREADY_EXISTS)

            final_data["company_id"] = None
            return final_data

        if role_scope == ROLE_SCOPE_ENTERPRISE:
            if context is not None and TenantPolicy.is_platform_admin(context):
                company_id = final_data.get("company_id")
                if not company_id:
                    cls.deny("ENTERPRISE roles must be bound to a company", NsErrorCode.ROLE_ENTERPRISE_COMPANY_REQUIRED)
            else:
                if context is None:
                    cls.deny("ENTERPRISE roles must be bound to a company", NsErrorCode.ROLE_ENTERPRISE_COMPANY_REQUIRED)
                TenantPolicy.ensure_enterprise_context(context)
                company_id = context.company_id

            normalized_company_id = cls.normalize_company_id(company_id)
            if await RoleRepository.exists_enterprise_role_code(company_id=normalized_company_id, role_code=role_code):
                cls.deny("Role code already exists", NsErrorCode.ROLE_CODE_ALREADY_EXISTS)

            final_data["company_id"] = normalized_company_id
            return final_data

        # noinspection PyInconsistentReturns
        cls.deny("Invalid role_scope value", NsErrorCode.INVALID_VALUE)

    @classmethod
    def ensure_can_update_fields(cls, *, data: dict[str, Any]) -> None:
        """Reject immutable role fields."""
        if "company_id" in data:
            cls.deny("Updating field is not allowed: company_id", NsErrorCode.UPDATE_FIELD_NOT_ALLOWED)

        if "role_scope" in data:
            cls.deny("Updating field is not allowed: role_scope", NsErrorCode.UPDATE_FIELD_NOT_ALLOWED)


class TenantPolicy(BasePolicy):
    @classmethod
    def is_platform_admin(cls, context: TenantContext) -> bool:
        return bool(context.is_superuser)

    @classmethod
    def is_enterprise_user(cls, context: TenantContext) -> bool:
        return context.user_type == USER_TYPE_ENTERPRISE

    @classmethod
    def is_personal_user(cls, context: TenantContext) -> bool:
        return context.user_type == USER_TYPE_PERSONAL

    @classmethod
    def ensure_enterprise_context(cls, context: TenantContext) -> None:
        if cls.is_platform_admin(context):
            return

        if cls.is_personal_user(context):
            cls.deny("Personal users cannot access enterprise organization resources", NsErrorCode.ENTERPRISE_ORG_FORBIDDEN_PERSONAL)

        if cls.is_enterprise_user(context) and not context.company_id:
            cls.deny("Enterprise user is not bound to a company", NsErrorCode.ENTERPRISE_USER_COMPANY_NOT_BOUND)

    @classmethod
    def ensure_platform_admin(cls, context: TenantContext, message: str, code: int) -> None:
        if not cls.is_platform_admin(context):
            cls.deny(message, code)

    @classmethod
    def ensure_same_company(cls, left_company_id: int | None, right_company_id: int | None, message: str, code: int) -> None:
        if left_company_id != right_company_id:
            cls.deny(message, code)

    @classmethod
    def get_company_scope(cls, context: TenantContext) -> int | None:
        if cls.is_platform_admin(context):
            return None

        if cls.is_enterprise_user(context):
            cls.ensure_enterprise_context(context)
            return context.company_id

        return None


class UserPolicy(BasePolicy):
    """User operation policy."""

    ADMIN_USER_PERMISSION = "iam:user:update_staff"
    SUPERUSER_PERMISSION = "iam:user:update_superuser"

    @classmethod
    async def ensure_can_operate_user(cls, *, operator: Any, target_user: Any) -> None:
        """Ensure operator can operate target user."""
        if bool(getattr(target_user, "is_superuser", False)) and not bool(getattr(operator, "is_superuser", False)):
            cls.deny("Staff administrators cannot operate on superusers", NsErrorCode.STAFF_CANNOT_OPERATE_SUPERUSER)

        if bool(getattr(target_user, "is_staff", False)) or bool(getattr(target_user, "is_superuser", False)):
            has_permission = await cls.has_admin_user_permission(operator)
            if not has_permission:
                cls.deny(f"Permission denied: {cls.ADMIN_USER_PERMISSION}", NsErrorCode.PERMISSION_DENIED)

    @classmethod
    async def ensure_can_update_critical_fields(cls, *, operator: Any, update_data: dict[str, Any]) -> None:
        """Ensure operator can update staff or superuser flags."""
        if bool(getattr(operator, "is_superuser", False)):
            return

        if cls.is_truthy(update_data.get("is_superuser")):
            cls.deny("Staff administrators cannot operate on superusers", NsErrorCode.STAFF_CANNOT_OPERATE_SUPERUSER)

        critical_field_permissions = {
            "is_staff": cls.ADMIN_USER_PERMISSION,
            "is_superuser": cls.SUPERUSER_PERMISSION,
        }

        for field, permission_code in critical_field_permissions.items():
            if field not in update_data:
                continue

            if not cls.is_truthy(update_data.get(field)):
                continue

            has_permission = await cls.has_permission(user=operator, permission_code=permission_code)
            if not has_permission:
                cls.deny(f"Permission denied: {permission_code}", NsErrorCode.PERMISSION_DENIED)

    @classmethod
    async def has_admin_user_permission(cls, operator: Any) -> bool:
        """Check whether operator can operate administrator users."""
        if bool(getattr(operator, "is_superuser", False)):
            return True

        return await cls.has_permission(user=operator, permission_code=cls.ADMIN_USER_PERMISSION)

    @staticmethod
    async def has_permission(*, user: Any, permission_code: str) -> bool:
        """Check user permission with lazy import to avoid policy-service import cycles."""
        from ns_backend.iam.services.permission import PermissionService

        return await PermissionService.has_permission(user=user, permission_code=permission_code)

    @classmethod
    def get_user_tenant_filter(cls, *, operator: Any) -> dict[str, Any] | None:
        """Resolve user list tenant filter for operator."""
        from ns_backend.iam.services.tenant import TenantService

        context = TenantService.from_user(operator)

        if TenantPolicy.is_platform_admin(context):
            return None

        if TenantPolicy.is_enterprise_user(context):
            TenantPolicy.ensure_enterprise_context(context)
            return {"company_id": context.company_id}

        return {"id": context.user_id}

    @classmethod
    async def build_user_list_visibility_filters(cls, *, operator: Any, include_staff: Any = None, include_superuser: Any = None) -> dict[str, Any]:
        """Build visibility filters for user list.

        Default behavior aligns with backup:
        1. Hide staff and superuser by default.
        2. include_staff=true allows staff users when operator has admin-user permission.
        3. include_superuser=true only allows platform superusers to see superusers.
        """
        requested_include_superuser = cls.is_truthy(include_superuser)
        requested_include_staff = cls.is_truthy(include_staff) or requested_include_superuser

        if requested_include_superuser and not bool(getattr(operator, "is_superuser", False)):
            cls.deny("Staff administrators cannot operate on superusers", NsErrorCode.STAFF_CANNOT_OPERATE_SUPERUSER)

        if requested_include_staff:
            has_permission = await cls.has_admin_user_permission(operator)
            if not has_permission:
                cls.deny(f"Permission denied: {cls.ADMIN_USER_PERMISSION}", NsErrorCode.PERMISSION_DENIED)

        if not requested_include_staff:
            return {
                "is_staff": 0,
                "is_superuser": 0,
            }

        if not requested_include_superuser:
            return {
                "is_superuser": 0,
            }

        return {}
