# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db.models import Q

from ns_backend.backend.common import BaseRepository
from ns_backend.iam.models import IamResourceRelation

if TYPE_CHECKING:
    pass


class ResourceRelationRepository:
    """Repository for IAM resource inheritance relations."""

    MAX_RELATION_DEPTH = 8

    @staticmethod
    def _normalize_resource_type(resource_type: str) -> str:
        return str(resource_type or "").strip().lower()

    @staticmethod
    def _normalize_resource_id(resource_id: str) -> str:
        return str(resource_id or "").strip()

    @staticmethod
    def _build_pair_query(*, pairs: list[tuple[str, str]], left_field: str, right_field: str) -> Q:
        query = Q()
        for left_value, right_value in pairs:
            query |= Q(**{left_field: left_value, right_field: right_value})
        return query

    @staticmethod
    async def get_relation(
        *,
        resource_type: str,
        resource_id: str,
        parent_resource_type: str,
        parent_resource_id: str,
    ) -> IamResourceRelation | None:
        """Load one relation row by unique child-parent tuple."""
        db_alias = BaseRepository.resolve_db_alias(model_class=IamResourceRelation)
        return await IamResourceRelation.objects.using(db_alias).filter(
            resource_type=resource_type,
            resource_id=resource_id,
            parent_resource_type=parent_resource_type,
            parent_resource_id=parent_resource_id,
        ).afirst()

    @staticmethod
    async def create_relation(
        *,
        resource_type: str,
        resource_id: str,
        parent_resource_type: str,
        parent_resource_id: str,
        relation_type: str,
        operator_id: int | None,
    ) -> dict[str, Any]:
        """Create one resource relation row."""
        return await BaseRepository.create_item_with_audit(
            model_class=IamResourceRelation,
            data={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "parent_resource_type": parent_resource_type,
                "parent_resource_id": parent_resource_id,
                "relation_type": relation_type,
            },
            operator_id=operator_id,
        )

    @staticmethod
    async def update_relation(*, item: IamResourceRelation, relation_type: str, operator_id: int | None) -> None:
        """Update relation_type for one resource relation row."""
        update_data = BaseRepository.fill_update_audit_fields(
            model_class=IamResourceRelation,
            data={"relation_type": relation_type},
            operator_id=operator_id,
        )
        await BaseRepository.update_item(instance=item, data=update_data)

    @classmethod
    async def upsert_parent_relation(
        cls,
        *,
        resource_type: str,
        resource_id: str,
        parent_resource_type: str,
        parent_resource_id: str,
        relation_type: str,
        operator_id: int | None,
    ) -> dict[str, Any]:
        """Create or update one parent relation row idempotently."""
        existing = await cls.get_relation(
            resource_type=resource_type,
            resource_id=resource_id,
            parent_resource_type=parent_resource_type,
            parent_resource_id=parent_resource_id,
        )
        if existing is None:
            return await cls.create_relation(
                resource_type=resource_type,
                resource_id=resource_id,
                parent_resource_type=parent_resource_type,
                parent_resource_id=parent_resource_id,
                relation_type=relation_type,
                operator_id=operator_id,
            )

        if str(existing.relation_type or "").upper() != str(relation_type or "").upper():
            await cls.update_relation(item=existing, relation_type=relation_type, operator_id=operator_id)

        return {"id": existing.id}

    @classmethod
    async def list_parent_relations(cls, *, resource_type: str, resource_id: str) -> list[dict[str, Any]]:
        """List direct parent relations for one resource instance."""
        db_alias = BaseRepository.resolve_db_alias(model_class=IamResourceRelation)
        queryset = IamResourceRelation.objects.using(db_alias).filter(
            resource_type=cls._normalize_resource_type(resource_type),
            resource_id=cls._normalize_resource_id(resource_id),
        ).values(
            "id",
            "resource_type",
            "resource_id",
            "parent_resource_type",
            "parent_resource_id",
            "relation_type",
        )
        return [item async for item in queryset]

    @classmethod
    async def list_ancestor_chain(cls, *, resource_type: str, resource_id: str, max_depth: int | None = None) -> list[dict[str, Any]]:
        """List self + ancestor chain for one resource instance."""
        depth_limit = cls.MAX_RELATION_DEPTH if max_depth is None else max(int(max_depth), 1)

        normalized_type = cls._normalize_resource_type(resource_type)
        normalized_id = cls._normalize_resource_id(resource_id)
        chain: list[dict[str, Any]] = [{
            "resource_type": normalized_type,
            "resource_id": normalized_id,
            "depth": 0,
            "relation_type": None,
        }]

        seen_pairs: set[tuple[str, str]] = {(normalized_type, normalized_id)}
        frontier_pairs: list[tuple[str, str]] = [(normalized_type, normalized_id)]

        db_alias = BaseRepository.resolve_db_alias(model_class=IamResourceRelation)

        for depth in range(1, depth_limit + 1):
            if not frontier_pairs:
                break

            pair_query = cls._build_pair_query(
                pairs=frontier_pairs,
                left_field="resource_type",
                right_field="resource_id",
            )
            queryset = IamResourceRelation.objects.using(db_alias).filter(pair_query).values(
                "resource_type",
                "resource_id",
                "parent_resource_type",
                "parent_resource_id",
                "relation_type",
            )
            rows = [item async for item in queryset]

            next_frontier: list[tuple[str, str]] = []
            for row in rows:
                parent_type = cls._normalize_resource_type(row.get("parent_resource_type", ""))
                parent_id = cls._normalize_resource_id(row.get("parent_resource_id", ""))
                if not parent_type or not parent_id:
                    continue

                parent_pair = (parent_type, parent_id)
                if parent_pair in seen_pairs:
                    continue

                seen_pairs.add(parent_pair)
                chain.append(
                    {
                        "resource_type": parent_type,
                        "resource_id": parent_id,
                        "depth": depth,
                        "relation_type": str(row.get("relation_type") or "").strip().upper() or None,
                    }
                )
                next_frontier.append(parent_pair)

            frontier_pairs = next_frontier

        return chain

    @classmethod
    async def list_descendant_resource_ids(
        cls,
        *,
        parent_resource_type: str,
        parent_resource_id: str,
        target_resource_type: str,
        max_depth: int | None = None,
        include_parent_when_target: bool = True,
    ) -> list[str]:
        """List descendant resource ids that match one target resource type."""
        depth_limit = cls.MAX_RELATION_DEPTH if max_depth is None else max(int(max_depth), 1)

        normalized_parent_type = cls._normalize_resource_type(parent_resource_type)
        normalized_parent_id = cls._normalize_resource_id(parent_resource_id)
        normalized_target_type = cls._normalize_resource_type(target_resource_type)

        if not normalized_parent_type or not normalized_parent_id or not normalized_target_type:
            return []

        result_ids: list[str] = []
        seen_result_ids: set[str] = set()
        if include_parent_when_target and normalized_parent_type == normalized_target_type:
            result_ids.append(normalized_parent_id)
            seen_result_ids.add(normalized_parent_id)

        seen_pairs: set[tuple[str, str]] = {(normalized_parent_type, normalized_parent_id)}
        frontier_pairs: list[tuple[str, str]] = [(normalized_parent_type, normalized_parent_id)]

        db_alias = BaseRepository.resolve_db_alias(model_class=IamResourceRelation)

        for _ in range(depth_limit):
            if not frontier_pairs:
                break

            pair_query = cls._build_pair_query(
                pairs=frontier_pairs,
                left_field="parent_resource_type",
                right_field="parent_resource_id",
            )
            queryset = IamResourceRelation.objects.using(db_alias).filter(pair_query).values(
                "resource_type",
                "resource_id",
            )
            rows = [item async for item in queryset]

            next_frontier: list[tuple[str, str]] = []
            for row in rows:
                child_type = cls._normalize_resource_type(row.get("resource_type", ""))
                child_id = cls._normalize_resource_id(row.get("resource_id", ""))
                if not child_type or not child_id:
                    continue

                child_pair = (child_type, child_id)
                if child_pair in seen_pairs:
                    continue

                seen_pairs.add(child_pair)
                next_frontier.append(child_pair)

                if child_type == normalized_target_type and child_id not in seen_result_ids:
                    seen_result_ids.add(child_id)
                    result_ids.append(child_id)

            frontier_pairs = next_frontier

        return result_ids

    @classmethod
    async def list_ancestor_resource_types(cls, *, resource_type: str, max_depth: int | None = None) -> list[str]:
        """List resource-type ancestors discovered from relation graph."""
        depth_limit = cls.MAX_RELATION_DEPTH if max_depth is None else max(int(max_depth), 1)
        normalized_resource_type = cls._normalize_resource_type(resource_type)
        if not normalized_resource_type:
            return []

        result_types: list[str] = []
        seen_types: set[str] = {normalized_resource_type}
        frontier_types: list[str] = [normalized_resource_type]

        db_alias = BaseRepository.resolve_db_alias(model_class=IamResourceRelation)

        for _ in range(depth_limit):
            if not frontier_types:
                break

            queryset = IamResourceRelation.objects.using(db_alias).filter(
                resource_type__in=frontier_types,
            ).values_list("parent_resource_type", flat=True)
            parent_types = [cls._normalize_resource_type(value) async for value in queryset]

            next_frontier: list[str] = []
            for parent_type in parent_types:
                if not parent_type or parent_type in seen_types:
                    continue
                seen_types.add(parent_type)
                result_types.append(parent_type)
                next_frontier.append(parent_type)

            frontier_types = next_frontier

        return result_types

