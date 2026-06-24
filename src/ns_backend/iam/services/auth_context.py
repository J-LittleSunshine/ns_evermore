# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING,
)

from ns_backend.iam.constants import normalize_data_scope
from ns_backend.iam.schemas import (
    DataScopeResult,
    TenantContext,
)
from ns_backend.iam.services.auth import AuthService
from ns_backend.iam.services.data_scope import DataScopeService
from ns_backend.iam.services.permission import PermissionService

if TYPE_CHECKING:
    pass


class AuthContextService:
    PLATFORM_USER_TYPES = {
        "PLATFORM",
        "platform",
        "admin",
        "ADMIN",
    }

    PERSONAL_USER_TYPES = {
        "PERSONAL",
        "personal",
    }

    ENTERPRISE_USER_TYPES = {
        "ENTERPRISE",
        "enterprise",
        "COMPANY",
        "company",
    }

    @classmethod
    def build_profile(cls, user: Any) -> dict[str, Any]:
        context = cls.build_tenant_context(user)

        return {
            "user": AuthService.build_current_user_payload(user),
            "tenant": cls.build_tenant_payload(context),
        }

    @classmethod
    def build_tenant_context(cls, user: Any) -> TenantContext:
        return TenantContext(
            user_id=user.id,
            user_type=str(getattr(user, "user_type", "") or ""),
            company_id=getattr(user, "company_id", None),
            subsidiary_id=getattr(user, "subsidiary_id", None),
            department_id=getattr(user, "department_id", None),
            is_staff=bool(getattr(user, "is_staff", False)),
            is_superuser=bool(getattr(user, "is_superuser", False)),
        )

    @classmethod
    def build_tenant_payload(cls, context: TenantContext) -> dict[str, Any]:
        return {
            "is_platform_admin": cls.is_platform_admin(context),
            "is_enterprise_user": cls.is_enterprise_user(context),
            "is_personal_user": cls.is_personal_user(context),
            "company_id": context.company_id,
            "subsidiary_id": context.subsidiary_id,
            "department_id": context.department_id,
        }

    @classmethod
    def is_platform_admin(cls, context: TenantContext) -> bool:
        if context.is_superuser:
            return True

        if context.is_staff and context.user_type in cls.PLATFORM_USER_TYPES:
            return True

        return context.user_type in cls.PLATFORM_USER_TYPES

    @classmethod
    def is_enterprise_user(cls, context: TenantContext) -> bool:
        if context.company_id is not None:
            return True

        return context.user_type in cls.ENTERPRISE_USER_TYPES

    @classmethod
    def is_personal_user(cls, context: TenantContext) -> bool:
        if cls.is_platform_admin(context):
            return False

        if cls.is_enterprise_user(context):
            return False

        if context.user_type in cls.PERSONAL_USER_TYPES:
            return True

        return context.company_id is None

    @staticmethod
    async def list_permission_codes(user: Any) -> list[str]:
        return await PermissionService.list_permission_codes(user)

    @staticmethod
    async def list_menus(user: Any) -> list[dict[str, Any]]:
        return await PermissionService.list_menu_tree(user)

    @classmethod
    async def list_data_scopes(cls, *, user: Any, permission_codes: list[str]) -> list[dict[str, Any]]:
        if not user or not bool(getattr(user, "is_active", False)):
            return []

        items: list[dict[str, Any]] = []
        for permission_code in permission_codes:
            result = await DataScopeService.resolve_scope(
                user=user,
                permission_code=permission_code,
            )
            items.append(
                cls.serialize_data_scope_result(
                    permission_code=permission_code,
                    result=result,
                )
            )

        return items

    @staticmethod
    def serialize_data_scope_result(*, permission_code: str, result: DataScopeResult) -> dict[str, Any]:
        return {
            "permission_code": permission_code,
            "allowed": result.allowed,
            "scope": result.scope,
            "normalized_scope": normalize_data_scope(result.scope),
            "company_id": result.company_id,
            "subsidiary_id": result.subsidiary_id,
            "department_id": result.department_id,
            "department_ids": list(result.department_ids or []),
            "user_id": result.user_id,
            "is_platform_scope": result.is_platform_scope,
        }
