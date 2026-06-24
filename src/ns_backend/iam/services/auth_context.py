# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING,
)

from ns_backend.iam.schemas import TenantContext
from ns_backend.iam.services.auth import AuthService
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