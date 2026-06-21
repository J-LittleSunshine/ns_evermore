# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_backend.backend.common import BaseRepository
from ns_backend.iam.models import IamPolicy, IamPolicyRule

if TYPE_CHECKING:
    pass


class PolicyRepository:
    """Repository for IAM policy and policy-rule tables."""

    POLICY_FIELDS: tuple[str, ...] = (
        "id",
        "policy_code",
        "policy_name",
        "priority",
        "status",
        "version",
        "created_at",
        "updated_at",
    )

    POLICY_RULE_FIELDS: tuple[str, ...] = (
        "id",
        "policy_id",
        "subject_type",
        "subject_id",
        "resource_type",
        "resource_id",
        "action_code",
        "effect",
        "data_scope",
        "condition_json",
        "priority",
        "status",
        "created_at",
        "updated_at",
    )

    @staticmethod
    async def get_policy_by_id(policy_id: int) -> IamPolicy | None:
        """Load policy row by primary key."""
        db_alias = BaseRepository.resolve_db_alias(model_class=IamPolicy)
        return await IamPolicy.objects.using(db_alias).filter(id=policy_id).afirst()

    @staticmethod
    async def get_policy_by_code(policy_code: str) -> IamPolicy | None:
        """Load policy row by policy code."""
        db_alias = BaseRepository.resolve_db_alias(model_class=IamPolicy)
        return await IamPolicy.objects.using(db_alias).filter(policy_code=policy_code).afirst()

    @staticmethod
    async def create_policy(*, policy_code: str, policy_name: str, priority: int, status: int, version: int, operator_id: int | None) -> dict[str, Any]:
        """Create one policy row."""
        return await BaseRepository.create_item_with_audit(
            model_class=IamPolicy,
            data={
                "policy_code": policy_code,
                "policy_name": policy_name,
                "priority": priority,
                "status": status,
                "version": version,
            },
            operator_id=operator_id,
        )

    @staticmethod
    async def update_policy(*, item: IamPolicy, data: dict[str, Any], operator_id: int | None) -> None:
        """Update one policy row."""
        update_data = BaseRepository.fill_update_audit_fields(model_class=IamPolicy, data=data, operator_id=operator_id)
        await BaseRepository.update_item(instance=item, data=update_data)

    @classmethod
    async def list_policies(cls, *, page: int | str | None, page_size: int | str | None, filters: dict[str, Any] | None) -> dict[str, Any]:
        """List policy rows."""
        return await BaseRepository.list_items(
            model_class=IamPolicy,
            fields=cls.POLICY_FIELDS,
            page=page,
            page_size=page_size,
            filters=filters,
            order_by=(
                "-priority",
                "id"
            ),
        )

    @staticmethod
    async def get_rule_by_id(rule_id: int) -> IamPolicyRule | None:
        """Load policy rule by primary key."""
        db_alias = BaseRepository.resolve_db_alias(model_class=IamPolicyRule)
        return await IamPolicyRule.objects.using(db_alias).filter(id=rule_id).afirst()

    @staticmethod
    async def create_rule(
            *,
            policy_id: int,
            subject_type: str | None,
            subject_id: int | None,
            resource_type: str | None,
            resource_id: str | None,
            action_code: str,
            effect: str,
            data_scope: str | None,
            condition_json: dict[str, Any] | None,
            priority: int,
            status: int,
            operator_id: int | None,
    ) -> dict[str, Any]:
        """Create one policy-rule row."""
        return await BaseRepository.create_item_with_audit(
            model_class=IamPolicyRule,
            data={
                "policy_id": policy_id,
                "subject_type": subject_type,
                "subject_id": subject_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action_code": action_code,
                "effect": effect,
                "data_scope": data_scope,
                "condition_json": condition_json,
                "priority": priority,
                "status": status,
            },
            operator_id=operator_id,
        )

    @staticmethod
    async def update_rule(*, item: IamPolicyRule, data: dict[str, Any], operator_id: int | None) -> None:
        """Update one policy-rule row."""
        update_data = BaseRepository.fill_update_audit_fields(model_class=IamPolicyRule, data=data, operator_id=operator_id)
        await BaseRepository.update_item(instance=item, data=update_data)

    @staticmethod
    async def delete_rule(item: IamPolicyRule) -> None:
        """Delete one policy-rule row."""
        await BaseRepository.delete_item(item)

    @classmethod
    async def list_rules(cls, *, page: int | str | None, page_size: int | str | None, filters: dict[str, Any] | None) -> dict[str, Any]:
        """List policy-rule rows."""
        return await BaseRepository.list_items(
            model_class=IamPolicyRule,
            fields=cls.POLICY_RULE_FIELDS,
            page=page,
            page_size=page_size,
            filters=filters,
            order_by=(
                "policy_id",
                "-priority",
                "id"
            ),
        )

    @staticmethod
    async def list_active_rules_for_action(*, action_code: str) -> list[dict[str, Any]]:
        """List enabled rules under enabled policies for one action code."""
        db_alias = BaseRepository.resolve_db_alias(model_class=IamPolicyRule)
        queryset = IamPolicyRule.objects.using(db_alias).filter(
            action_code=action_code,
            status=1,
            policy__status=1,
        ).values(
            "id",
            "policy_id",
            "subject_type",
            "subject_id",
            "resource_type",
            "resource_id",
            "action_code",
            "effect",
            "data_scope",
            "condition_json",
            "priority",
            "status",
            "policy__priority",
        )
        return [item async for item in queryset]
