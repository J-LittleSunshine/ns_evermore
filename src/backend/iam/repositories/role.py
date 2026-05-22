# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from django.db import IntegrityError

from iam.constants import IAM_DB_ALIAS
from ns_common.error_codes import NsErrorCode
from iam.models import IamRole
from ns_backend.exceptions import BusinessError


class RoleRepository:
    """角色数据访问层。"""

    @staticmethod
    async def exists_personal_role_code(role_code: str, exclude_id: int | None = None) -> bool:
        queryset = IamRole.objects.using(IAM_DB_ALIAS).filter(
            role_scope=IamRole.SCOPE_PERSONAL,
            company_id__isnull=True,
            role_code=role_code,
        )

        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)

        return await queryset.aexists()

    @staticmethod
    async def exists_enterprise_role_code(
        company_id: int,
        role_code: str,
        exclude_id: int | None = None,
    ) -> bool:
        queryset = IamRole.objects.using(IAM_DB_ALIAS).filter(
            company_id=company_id,
            role_scope=IamRole.SCOPE_ENTERPRISE,
            role_code=role_code,
        )

        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)

        return await queryset.aexists()

    @staticmethod
    async def get_by_id(role_id: int) -> IamRole | None:
        return await IamRole.objects.using(IAM_DB_ALIAS).filter(id=role_id).afirst()

    @classmethod
    async def get_required_by_id(cls, role_id: int) -> IamRole:
        role = await cls.get_by_id(role_id)

        if not role:
            raise BusinessError("Data not found", NsErrorCode.DATA_NOT_FOUND)

        return role

    @classmethod
    async def get_required_by_id_for_company(cls, role_id: int, company_id: int) -> IamRole:
        role = await IamRole.objects.using(IAM_DB_ALIAS).filter(
            id=role_id,
            company_id=company_id,
        ).afirst()

        if not role:
            raise BusinessError("Data not found", NsErrorCode.DATA_NOT_FOUND)

        return role

    @staticmethod
    async def list_roles(
        page: int,
        page_size: int,
        tenant_filter: dict[str, Any] | None,
        include_personal: bool = False,
    ) -> tuple[list[IamRole], int]:
        queryset = IamRole.objects.using(IAM_DB_ALIAS).all().order_by("-id")

        if tenant_filter:
            queryset = queryset.filter(**tenant_filter)

        if not include_personal:
            queryset = queryset.filter(role_scope=IamRole.SCOPE_ENTERPRISE)

        offset = (page - 1) * page_size
        total = await queryset.acount()

        rows: list[IamRole] = []
        async for role in queryset[offset: offset + page_size].aiterator():
            rows.append(role)

        return rows, total

    @staticmethod
    async def create_role(data: dict[str, Any]) -> IamRole:
        try:
            return await IamRole.objects.using(IAM_DB_ALIAS).acreate(**data)
        except IntegrityError as exc:
            raise BusinessError(f"Data creation failed: {exc}", NsErrorCode.DATA_CREATION_FAILED)

    @staticmethod
    async def update_role(role: IamRole, data: dict[str, Any]) -> None:
        for field, value in data.items():
            setattr(role, field, value)

        try:
            await role.asave(
                using=IAM_DB_ALIAS,
                update_fields=list(data.keys()),
            )
        except IntegrityError as exc:
            raise BusinessError(f"Data update failed: {exc}", NsErrorCode.DATA_UPDATE_FAILED)

    @staticmethod
    async def delete_role(role: IamRole) -> None:
        await role.adelete(using=IAM_DB_ALIAS)

