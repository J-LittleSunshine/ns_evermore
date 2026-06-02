# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db.models import Q

from ns_backend.backend.common import BaseRepository
from ns_backend.iam.models import IamResourceAcl

if TYPE_CHECKING:
    pass


class ResourceAclRepository:
    """Repository for IAM resource ACL records."""

    ACL_FIELDS: tuple[str, ...] = (
        "id",
        "subject_type",
        "subject_id",
        "resource_type",
        "resource_id",
        "action_code",
        "effect",
        "data_scope",
        "expired_at",
        "created_at",
        "updated_at",
    )

    @staticmethod
    async def get_acl(
        *,
        subject_type: str,
        subject_id: int,
        resource_type: str,
        resource_id: str,
        action_code: str,
    ) -> IamResourceAcl | None:
        """Load one ACL record by unique key."""
        db_alias: str = BaseRepository.resolve_db_alias(model_class=IamResourceAcl)
        return await IamResourceAcl.objects.using(db_alias).filter(
            subject_type=subject_type,
            subject_id=subject_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action_code=action_code,
        ).afirst()

    @staticmethod
    async def create_acl(
        *,
        subject_type: str,
        subject_id: int,
        resource_type: str,
        resource_id: str,
        action_code: str,
        effect: str,
        data_scope: str | None,
        expired_at,
        operator_id: int | None,
    ) -> dict[str, Any]:
        """Create one ACL record."""
        return await BaseRepository.create_item_with_audit(
            model_class=IamResourceAcl,
            data={
                "subject_type": subject_type,
                "subject_id": subject_id,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "action_code": action_code,
                "effect": effect,
                "data_scope": data_scope,
                "expired_at": expired_at,
            },
            operator_id=operator_id,
        )

    @staticmethod
    async def update_acl(
        *,
        item: IamResourceAcl,
        effect: str,
        data_scope: str | None,
        expired_at,
        operator_id: int | None,
    ) -> None:
        """Update one ACL record."""
        update_data: dict[str, Any] = BaseRepository.fill_update_audit_fields(
            model_class=IamResourceAcl,
            data={
                "effect": effect,
                "data_scope": data_scope,
                "expired_at": expired_at,
            },
            operator_id=operator_id,
        )
        await BaseRepository.update_item(instance=item, data=update_data)

    @staticmethod
    async def delete_acl(item: IamResourceAcl) -> None:
        """Delete one ACL record."""
        await BaseRepository.delete_item(item)

    @classmethod
    async def list_acls(cls, *, page: int | str | None, page_size: int | str | None, filters: dict[str, Any] | None) -> dict[str, Any]:
        """List ACL records with pagination."""
        return await BaseRepository.list_items(
            model_class=IamResourceAcl,
            fields=cls.ACL_FIELDS,
            page=page,
            page_size=page_size,
            filters=filters,
            order_by=("-id",),
        )

    @staticmethod
    async def list_active_effects(
        *,
        subject_bindings: list[tuple[str, int]],
        resource_type: str,
        resource_id: str,
        action_code: str,
        now,
    ) -> list[dict[str, Any]]:
        """List active ACL effect candidates for one subject-resource-action tuple."""
        if not subject_bindings:
            return []

        subject_query: Q = Q()
        for subject_type, subject_id in subject_bindings:
            subject_query |= Q(subject_type=subject_type, subject_id=subject_id)

        db_alias: str = BaseRepository.resolve_db_alias(model_class=IamResourceAcl)
        queryset = IamResourceAcl.objects.using(db_alias).filter(
            subject_query,
            resource_type=resource_type,
            resource_id=resource_id,
            action_code=action_code,
        ).filter(Q(expired_at__isnull=True) | Q(expired_at__gt=now)).values(
            "id",
            "subject_type",
            "subject_id",
            "effect",
            "data_scope",
            "expired_at",
        )

        return [item async for item in queryset]

    @staticmethod
    async def list_active_effects_for_resources(
        *,
        subject_bindings: list[tuple[str, int]],
        resource_pairs: list[tuple[str, str]],
        action_code: str,
        now,
    ) -> list[dict[str, Any]]:
        """List active ACL effects for one subject against multiple resources."""
        if not subject_bindings or not resource_pairs:
            return []

        subject_query: Q = Q()
        for subject_type, subject_id in subject_bindings:
            subject_query |= Q(subject_type=subject_type, subject_id=subject_id)

        resource_query: Q = Q()
        for resource_type, resource_id in resource_pairs:
            resource_query |= Q(resource_type=resource_type, resource_id=resource_id)

        db_alias: str = BaseRepository.resolve_db_alias(model_class=IamResourceAcl)
        queryset = IamResourceAcl.objects.using(db_alias).filter(
            subject_query,
            resource_query,
            action_code=action_code,
        ).filter(Q(expired_at__isnull=True) | Q(expired_at__gt=now)).values(
            "id",
            "subject_type",
            "subject_id",
            "resource_type",
            "resource_id",
            "effect",
            "data_scope",
            "expired_at",
        )
        return [item async for item in queryset]

    @staticmethod
    async def list_active_effects_for_resource_type_action(
        *,
        subject_bindings: list[tuple[str, int]],
        resource_type: str,
        action_code: str,
        now,
    ) -> list[dict[str, Any]]:
        """List active ACL effects for one subject and resource type/action scope."""
        if not subject_bindings:
            return []

        subject_query: Q = Q()
        for subject_type, subject_id in subject_bindings:
            subject_query |= Q(subject_type=subject_type, subject_id=subject_id)

        db_alias: str = BaseRepository.resolve_db_alias(model_class=IamResourceAcl)
        queryset = IamResourceAcl.objects.using(db_alias).filter(
            subject_query,
            resource_type=resource_type,
            action_code=action_code,
        ).filter(Q(expired_at__isnull=True) | Q(expired_at__gt=now)).values(
            "id",
            "subject_type",
            "subject_id",
            "resource_type",
            "resource_id",
            "effect",
            "data_scope",
            "expired_at",
        )
        return [item async for item in queryset]

