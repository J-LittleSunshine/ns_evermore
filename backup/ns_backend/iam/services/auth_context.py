# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_backend.iam.constants import normalize_data_scope
from ns_backend.iam.policies import TenantPolicy
from ns_backend.iam.schemas import DataScopeResult, TenantContext
from ns_backend.iam.services.data_scope import DataScopeService
from ns_backend.iam.services.permission import PermissionService

if TYPE_CHECKING:
    pass


class AuthContextService:
    """Authentication context facade used by auth views."""

    @classmethod
    def build_profile(cls, user: Any) -> dict[str, Any]:
        """Build current user profile payload."""
        context = cls.build_tenant_context(user)
        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "email": user.email,
                "phone": user.phone,
                "user_type": user.user_type,
                "company_id": user.company_id,
                "subsidiary_id": user.subsidiary_id,
                "department_id": user.department_id,
                "is_active": user.is_active,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
            },
            "tenant": {
                "is_platform_admin": TenantPolicy.is_platform_admin(context),
                "is_enterprise_user": TenantPolicy.is_enterprise_user(context),
                "is_personal_user": TenantPolicy.is_personal_user(context),
                "company_id": context.company_id,
                "subsidiary_id": context.subsidiary_id,
                "department_id": context.department_id,
            },
        }

    @staticmethod
    def build_tenant_context(user: Any) -> TenantContext:
        """Build tenant context without touching persistence."""
        return TenantContext(
            user_id=user.id,
            user_type=getattr(user, "user_type", ""),
            company_id=getattr(user, "company_id", None),
            subsidiary_id=getattr(user, "subsidiary_id", None),
            department_id=getattr(user, "department_id", None),
            is_staff=bool(getattr(user, "is_staff", False)),
            is_superuser=bool(getattr(user, "is_superuser", False)),
        )

    @staticmethod
    async def list_permission_codes(user: Any) -> list[str]:
        """List current user's effective permission codes."""
        return await PermissionService.list_permission_codes(user)

    @staticmethod
    async def list_menu_tree(user: Any) -> list[dict[str, Any]]:
        """List current user's effective menu tree."""
        return await PermissionService.list_menu_tree(user)

    @classmethod
    async def list_data_scopes(cls, *, user: Any, permission_codes: list[str]) -> list[dict[str, Any]]:
        """List data scope resolution results for permission codes."""
        if not user or not bool(getattr(user, "is_active", False)):
            return []

        items: list[dict[str, Any]] = []
        for permission_code in permission_codes:
            result = await DataScopeService.resolve_scope(user=user, permission_code=permission_code)
            items.append(cls.serialize_data_scope_result(permission_code=permission_code, result=result))
        return items

    @staticmethod
    def serialize_data_scope_result(*, permission_code: str, result: DataScopeResult) -> dict[str, Any]:
        """Serialize data-scope result to API payload."""
        return {
            "permission_code": permission_code,
            "allowed": result.allowed,
            "scope": result.scope,
            "normalized_scope": normalize_data_scope(result.scope),
            "company_id": result.company_id,
            "subsidiary_id": result.subsidiary_id,
            "department_id": result.department_id,
            "department_ids": list(result.department_ids),
            "user_id": result.user_id,
            "is_platform_scope": result.is_platform_scope,
        }
