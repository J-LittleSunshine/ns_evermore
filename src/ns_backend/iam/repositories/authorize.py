# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING,
)

from django.db.models import Q

from backend.common import BaseRepository
from ns_backend.iam.models import (
    IamResource,
    IamResourceAcl,
    IamResourceAction,
    IamResourceRelation,
    IamUserRole,
)

if TYPE_CHECKING:
    pass


class RuntimeAuthorizeRepository:
    MAX_RESOURCE_ANCESTOR_DEPTH = 20

    @staticmethod
    def active_time_filter(now) -> Q:
        return Q(expired_at__isnull=True) | Q(expired_at__gt=now)

    @classmethod
    async def get_resource_by_type(cls, *, resource_type: str) -> IamResource | None:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamResource)

        return await IamResource.objects.using(db_alias).filter(
            resource_type=resource_type,
            status=1,
        ).afirst()

    @classmethod
    async def has_action_for_resource_type(cls, *, resource_type: str, action_code: str) -> bool:
        resource = await cls.get_resource_by_type(
            resource_type=resource_type,
        )

        if resource is None:
            return False

        db_alias = BaseRepository.resolve_db_alias(model_class=IamResourceAction)

        return await IamResourceAction.objects.using(db_alias).filter(
            resource_id=resource.id,
            action_code=action_code,
            status=1,
        ).aexists()

    @classmethod
    async def list_active_role_ids_for_user(cls, *, user_id: int) -> list[int]:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamUserRole)

        queryset = IamUserRole.objects.using(db_alias).filter(
            user_id=user_id,
            role__status=1,
        ).values_list(
            "role_id",
            flat=True,
        )

        return [
            int(role_id)
            async for role_id in queryset
        ]

    @classmethod
    async def list_resource_ancestor_chain(cls, *, resource_type: str, resource_id: str) -> list[dict[str, Any]]:
        chain: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()

        current_pairs: list[tuple[str, str]] = [
            (
                resource_type,
                resource_id,
            )
        ]

        for depth in range(cls.MAX_RESOURCE_ANCESTOR_DEPTH + 1):
            next_pairs: list[tuple[str, str]] = []

            for current_resource_type, current_resource_id in current_pairs:
                pair = (
                    current_resource_type,
                    current_resource_id,
                )

                if pair in seen:
                    continue

                seen.add(pair)
                chain.append(
                    {
                        "resource_type": current_resource_type,
                        "resource_id": current_resource_id,
                        "depth": depth,
                    }
                )

                parent_pairs = await cls.list_parent_pairs(
                    resource_type=current_resource_type,
                    resource_id=current_resource_id,
                )

                for parent_pair in parent_pairs:
                    if parent_pair not in seen:
                        next_pairs.append(parent_pair)

            if not next_pairs:
                break

            current_pairs = next_pairs

        return chain

    @classmethod
    async def list_parent_pairs(cls, *, resource_type: str, resource_id: str) -> list[tuple[str, str]]:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamResourceRelation)

        queryset = IamResourceRelation.objects.using(db_alias).filter(
            resource_type=resource_type,
            resource_id=resource_id,
        ).values(
            "parent_resource_type",
            "parent_resource_id",
        ).order_by(
            "id",
        )

        pairs: list[tuple[str, str]] = []

        async for row in queryset:
            parent_resource_type = str(row.get("parent_resource_type") or "").strip().lower()
            parent_resource_id = str(row.get("parent_resource_id") or "").strip()

            if not parent_resource_type or not parent_resource_id:
                continue

            pairs.append(
                (
                    parent_resource_type,
                    parent_resource_id,
                )
            )

        return pairs

    @classmethod
    async def list_active_acl_effects_for_resources(cls, *, subject_bindings: list[tuple[str, int]], resource_pairs: list[tuple[str, str]], action_code: str, now) -> list[dict[str, Any]]:
        if not subject_bindings or not resource_pairs:
            return []

        subject_query = Q(pk__in=[])
        for subject_type, subject_id in subject_bindings:
            subject_query |= Q(
                subject_type=subject_type,
                subject_id=subject_id,
            )

        resource_query = Q(pk__in=[])
        for resource_type, resource_id in resource_pairs:
            resource_query |= Q(
                resource_type=resource_type,
                resource_id=resource_id,
            )

        db_alias = BaseRepository.resolve_db_alias(model_class=IamResourceAcl)

        queryset = IamResourceAcl.objects.using(db_alias).filter(
            cls.active_time_filter(now),
            subject_query,
            resource_query,
            action_code=action_code,
        ).values(
            "id",
            "subject_type",
            "subject_id",
            "resource_type",
            "resource_id",
            "action_code",
            "effect",
            "data_scope",
            "expired_at",
        ).order_by(
            "id",
        )

        return [
            dict(row)
            async for row in queryset
        ]
