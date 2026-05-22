# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from iam.error_codes import IamErrorCode
from iam.policies.role import RolePolicy
from iam.policies.tenant import TenantPolicy
from iam.repositories.role import RoleRepository
from iam.services.tenant import TenantService
from ns_backend.exceptions import BusinessError
from ns_backend.utils.audit import AuditDataMixin


class RoleService(AuditDataMixin):
    """角色服务。"""

    @classmethod
    async def list_roles(
        cls,
        fields: tuple[str, ...],
        page: int | str | None,
        page_size: int | str | None,
        operator,
    ) -> dict[str, Any]:
        page, page_size = cls.normalize_page(page, page_size)
        context = TenantService.from_user(operator)

        if TenantPolicy.is_platform_admin(context):
            tenant_filter = None
            include_personal = True
        else:
            TenantPolicy.ensure_enterprise_context(context)
            tenant_filter = {"company_id": context.company_id}
            include_personal = False

        rows, total = await RoleRepository.list_roles(
            page=page,
            page_size=page_size,
            tenant_filter=tenant_filter,
            include_personal=include_personal,
        )

        return {
            "items": [cls.serialize(item, fields) for item in rows],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size,
            },
        }

    @classmethod
    async def get_role(cls, role_id: int | str | None, operator):
        if not role_id:
            raise BusinessError("id cannot be empty", IamErrorCode.ID_EMPTY)

        context = TenantService.from_user(operator)

        if TenantPolicy.is_platform_admin(context):
            return await RoleRepository.get_required_by_id(int(role_id))

        TenantPolicy.ensure_enterprise_context(context)

        return await RoleRepository.get_required_by_id_for_company(
            role_id=int(role_id),
            company_id=context.company_id,
        )

    @classmethod
    async def create_role(
        cls,
        data: dict[str, Any],
        operator,
        operator_id: int | None,
    ) -> dict[str, Any]:
        context = TenantService.from_user(operator)
        final_data = await RolePolicy.build_create_payload(
            context=context,
            data=data,
        )

        create_data = cls.fill_create_audit_fields(final_data, operator_id=operator_id)
        role = await RoleRepository.create_role(create_data)
        return {"id": role.id}

    @classmethod
    async def update_role(
        cls,
        role_id: int | str | None,
        data: dict[str, Any],
        operator,
        operator_id: int | None,
    ) -> None:
        RolePolicy.ensure_can_update_fields(data)

        role = await cls.get_role(role_id=role_id, operator=operator)
        update_data = cls.fill_update_audit_fields(data, operator_id=operator_id)
        await RoleRepository.update_role(role=role, data=update_data)

    @classmethod
    async def delete_role(cls, role_id: int | str | None, operator) -> None:
        role = await cls.get_role(role_id=role_id, operator=operator)
        await RoleRepository.delete_role(role)

    @staticmethod
    def normalize_page(page: int | str | None, page_size: int | str | None) -> tuple[int, int]:
        try:
            normalized_page = max(int(page or 1), 1)
            normalized_page_size = min(max(int(page_size or 20), 1), 100)
        except (TypeError, ValueError):
            raise BusinessError("Invalid pagination parameters", IamErrorCode.INVALID_PAGINATION_PARAMETERS)

        return normalized_page, normalized_page_size

    @staticmethod
    def serialize(instance, fields: tuple[str, ...]) -> dict[str, Any]:
        result = {}

        for field in fields:
            value = getattr(instance, field)

            if isinstance(value, (datetime, date)):
                value = value.isoformat()

            result[field] = value

        return result


__all__ = ["RoleService"]

