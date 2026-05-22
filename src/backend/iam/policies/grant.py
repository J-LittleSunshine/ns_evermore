# -*- coding: utf-8 -*-
from __future__ import annotations

from iam.policies.tenant import TenantPolicy
from iam.repositories.grant import GrantRepository
from iam.services.tenant import TenantService
from ns_backend.policies import BasePolicy


class GrantPolicy(BasePolicy):
    """IAM 授权边界策略。"""

    @classmethod
    async def ensure_can_bind_user_role(cls, user_id: int, role_id: int, operator) -> None:
        if not await GrantRepository.user_exists(user_id):
            cls.deny("User does not exist", 10103)

        role_info = await GrantRepository.get_role_scope_and_company_id(role_id)

        if not role_info:
            cls.deny("Role does not exist", 10002)

        user_company_id = await GrantRepository.get_user_company_id(user_id)
        role_scope, role_company_id = role_info
        context = TenantService.from_user(operator)

        if TenantPolicy.is_platform_admin(context):
            if role_scope == "PERSONAL" and user_company_id is not None:
                cls.deny("Cannot bind user role across companies", 14031)

            if role_scope == "ENTERPRISE" and user_company_id != role_company_id:
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
    async def ensure_can_operate_role(cls, role_id: int, operator) -> None:
        role_info = await GrantRepository.get_role_scope_and_company_id(role_id)

        if not role_info:
            cls.deny("Role does not exist", 10002)

        _, role_company_id = role_info
        context = TenantService.from_user(operator)

        if TenantPolicy.is_platform_admin(context):
            return

        TenantPolicy.ensure_enterprise_context(context)

        if role_company_id != context.company_id:
            cls.deny("Cannot operate roles from other companies", 14032)

    @classmethod
    async def ensure_can_operate_user(cls, user_id: int, operator) -> None:
        if not await GrantRepository.user_exists(user_id):
            cls.deny("User does not exist", 10103)

        user_company_id = await GrantRepository.get_user_company_id(user_id)
        context = TenantService.from_user(operator)

        if TenantPolicy.is_platform_admin(context):
            return

        TenantPolicy.ensure_enterprise_context(context)

        if user_company_id != context.company_id:
            cls.deny("Cannot operate users from other companies", 14033)

    @classmethod
    async def ensure_can_operate_department(cls, department_id: int, operator) -> None:
        department_company_id = await GrantRepository.get_department_company_id(department_id)

        if department_company_id is None:
            cls.deny("Data not found", 10002)

        context = TenantService.from_user(operator)

        if TenantPolicy.is_platform_admin(context):
            return

        TenantPolicy.ensure_enterprise_context(context)

        if department_company_id != context.company_id:
            cls.deny("Cannot operate departments from other companies", 14034)

    @classmethod
    async def ensure_can_operate_subsidiary(cls, subsidiary_id: int, operator) -> None:
        subsidiary_company_id = await GrantRepository.get_subsidiary_company_id(subsidiary_id)

        if subsidiary_company_id is None:
            cls.deny("Data not found", 10002)

        context = TenantService.from_user(operator)

        if TenantPolicy.is_platform_admin(context):
            return

        TenantPolicy.ensure_enterprise_context(context)

        if subsidiary_company_id != context.company_id:
            cls.deny("Cannot operate subsidiaries from other companies", 14035)


__all__ = ["GrantPolicy"]

