# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, date
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID

from django.conf import settings

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.constants import (
    USER_TYPE_ENTERPRISE,
    USER_TYPE_PERSONAL,
    DATA_SCOPE_ALL,
    DATA_SCOPE_LEVELS,
    DATA_SCOPE_SELF,
    DATA_SCOPE_DEPARTMENT,
    DATA_SCOPE_DEPARTMENT_TREE,
    DATA_SCOPE_SUBSIDIARY,
    DATA_SCOPE_COMPANY,
    PERMISSION_TYPE_DATA,
    PERMISSION_EFFECT_DENY,
    PERMISSION_EFFECT_ALLOW
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
        extra_keys = getattr(settings, "IAM_AUDIT_EXTRA_SENSITIVE_KEYS", ())
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
        if not scope:
            return cls.denied_result()

        base_kwargs = {
            "allowed": True,
            "scope": scope,
            "company_id": user.company_id,
            "subsidiary_id": user.subsidiary_id,
            "department_id": user.department_id,
            "user_id": user.id, "is_platform_scope": False
        }

        if scope == DATA_SCOPE_SELF:
            return DataScopeResult(**base_kwargs, department_ids=[])

        if scope == DATA_SCOPE_DEPARTMENT:
            if not user.department_id:
                return cls.denied_result()
            return DataScopeResult(**base_kwargs, department_ids=[user.department_id])

        if scope == DATA_SCOPE_DEPARTMENT_TREE:
            if not user.department_id or not department_ids:
                return cls.denied_result()
            return DataScopeResult(**base_kwargs, department_ids=department_ids)

        if scope == DATA_SCOPE_SUBSIDIARY:
            if not user.subsidiary_id:
                return cls.denied_result()
            return DataScopeResult(**base_kwargs, department_ids=[])

        if scope == DATA_SCOPE_COMPANY:
            if not user.company_id:
                return cls.denied_result()
            return DataScopeResult(**base_kwargs, department_ids=[])

        if scope == DATA_SCOPE_ALL:
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

        if scope.scope == DATA_SCOPE_SELF:
            if not field_map.self_field:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_SELF_FIELD")
            if scope.user_id is None:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_USER_ID")
            return DataScopeFilterPlan(allowed=True, filters={field_map.self_field: scope.user_id})

        if scope.scope == DATA_SCOPE_DEPARTMENT:
            if not field_map.department_field:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_DEPARTMENT_FIELD")
            if scope.department_id is None:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_DEPARTMENT_ID")
            return DataScopeFilterPlan(allowed=True, filters={field_map.department_field: scope.department_id})

        if scope.scope == DATA_SCOPE_DEPARTMENT_TREE:
            if not field_map.department_field:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_DEPARTMENT_FIELD")
            if not scope.department_ids:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_DEPARTMENT_IDS")
            return DataScopeFilterPlan(allowed=True, filters={f"{field_map.department_field}__in": scope.department_ids})

        if scope.scope == DATA_SCOPE_SUBSIDIARY:
            if not field_map.subsidiary_field:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_SUBSIDIARY_FIELD")
            if scope.subsidiary_id is None:
                return DataScopeFilterPlan(allowed=False, reason="MISSING_SUBSIDIARY_ID")
            return DataScopeFilterPlan(allowed=True, filters={field_map.subsidiary_field: scope.subsidiary_id})

        if scope.scope in {DATA_SCOPE_COMPANY, DATA_SCOPE_ALL}:
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
