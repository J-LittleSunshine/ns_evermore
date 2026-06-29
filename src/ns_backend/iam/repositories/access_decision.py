# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import (
    Any,
    TYPE_CHECKING,
)

from django.db.models import Q

from backend.common import BaseRepository
from ns_backend.iam.models import (
    IamPolicyRule,
    IamResource,
    IamResourceAcl,
    IamResourceAction,
    IamResourceRelation,
    IamUserRole
)
from ns_backend.iam.services.cache import IamCacheService

if TYPE_CHECKING:
    pass


class AccessDecisionRepository:
    MAX_RESOURCE_ANCESTOR_DEPTH = 20

    @staticmethod
    def active_time_filter(now) -> Q:
        return Q(expired_at__isnull=True) | Q(expired_at__gt=now)

    @staticmethod
    def normalize_resource_type(value: Any) -> str:
        return str(value or "").strip().lower()

    @staticmethod
    def normalize_resource_id(value: Any) -> str:
        return str(value or "").strip()

    @staticmethod
    def build_pair_query(*, pairs: list[tuple[str, str]], left_field: str, right_field: str) -> Q:
        query = Q(pk__in=[])
        for left_value, right_value in pairs:
            query |= Q(
                **{
                    left_field: left_value,
                    right_field: right_value,
                }
            )
        return query

    @classmethod
    async def list_active_acl_effects_for_resource_type_action(cls, *, subject_bindings: list[tuple[str, int]], resource_type: str, action_code: str, now) -> list[dict[str, Any]]:
        if not subject_bindings:
            return []

        subject_query = Q(pk__in=[])
        for subject_type, subject_id in subject_bindings:
            subject_query |= Q(
                subject_type=subject_type,
                subject_id=subject_id,
            )

        db_alias = BaseRepository.resolve_db_alias(model_class=IamResourceAcl)

        queryset = IamResourceAcl.objects.using(db_alias).filter(
            cls.active_time_filter(now),
            subject_query,
            resource_type=cls.normalize_resource_type(resource_type),
            action_code=str(action_code or "").strip().lower(),
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

    @classmethod
    async def list_descendant_resource_ids(cls, *, parent_resource_type: str, parent_resource_id: str, target_resource_type: str, max_depth: int | None = None, include_parent_when_target: bool = True) -> list[str]:
        depth_limit = cls.MAX_RESOURCE_ANCESTOR_DEPTH if max_depth is None else max(int(max_depth), 1)

        normalized_parent_type = cls.normalize_resource_type(parent_resource_type)
        normalized_parent_id = cls.normalize_resource_id(parent_resource_id)
        normalized_target_type = cls.normalize_resource_type(target_resource_type)

        if not normalized_parent_type or not normalized_parent_id or not normalized_target_type:
            return []

        result_ids: list[str] = []
        seen_result_ids: set[str] = set()

        if include_parent_when_target and normalized_parent_type == normalized_target_type:
            result_ids.append(normalized_parent_id)
            seen_result_ids.add(normalized_parent_id)

        seen_pairs: set[tuple[str, str]] = {
            (
                normalized_parent_type,
                normalized_parent_id,
            )
        }
        frontier_pairs: list[tuple[str, str]] = [
            (
                normalized_parent_type,
                normalized_parent_id,
            )
        ]

        db_alias = BaseRepository.resolve_db_alias(model_class=IamResourceRelation)

        for _ in range(depth_limit):
            if not frontier_pairs:
                break

            pair_query = cls.build_pair_query(
                pairs=frontier_pairs,
                left_field="parent_resource_type",
                right_field="parent_resource_id",
            )

            queryset = IamResourceRelation.objects.using(db_alias).filter(pair_query).values(
                "resource_type",
                "resource_id",
            )

            rows = [
                item
                async for item in queryset
            ]

            next_frontier: list[tuple[str, str]] = []
            for row in rows:
                child_type = cls.normalize_resource_type(row.get("resource_type"))
                child_id = cls.normalize_resource_id(row.get("resource_id"))

                if not child_type or not child_id:
                    continue

                child_pair = (
                    child_type,
                    child_id,
                )

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
        depth_limit = cls.MAX_RESOURCE_ANCESTOR_DEPTH if max_depth is None else max(int(max_depth), 1)
        normalized_resource_type = cls.normalize_resource_type(resource_type)

        if not normalized_resource_type:
            return []

        result_types: list[str] = []
        seen_types: set[str] = {
            normalized_resource_type,
        }
        frontier_types: list[str] = [
            normalized_resource_type,
        ]

        db_alias = BaseRepository.resolve_db_alias(model_class=IamResourceRelation)

        for _ in range(depth_limit):
            if not frontier_types:
                break

            queryset = IamResourceRelation.objects.using(db_alias).filter(
                resource_type__in=frontier_types,
            ).values_list(
                "parent_resource_type",
                flat=True,
            )

            parent_types = [
                cls.normalize_resource_type(value)
                async for value in queryset
            ]

            next_frontier: list[str] = []
            for parent_type in parent_types:
                if not parent_type or parent_type in seen_types:
                    continue

                seen_types.add(parent_type)
                result_types.append(parent_type)
                next_frontier.append(parent_type)

            frontier_types = next_frontier

        return result_types

    @classmethod
    async def get_resource_by_type(cls, *, resource_type: str) -> IamResource | None:
        cache_key = {
            "kind": "resource_by_type",
            "resource_type": resource_type,
        }

        payload = await IamCacheService.aget_or_set(
            cache_key,
            lambda: cls._get_resource_payload_by_type_from_db(resource_type=resource_type),
            ttl=IamCacheService.cache_ttl_seconds(),
        )

        resource = cls._resource_from_cache_payload(payload)
        if resource is not None or payload is None:
            return resource

        payload = await cls._get_resource_payload_by_type_from_db(
            resource_type=resource_type,
        )
        await IamCacheService.aset(
            cache_key,
            payload,
            ttl=IamCacheService.cache_ttl_seconds(),
        )
        return cls._resource_from_cache_payload(payload)

    @classmethod
    async def _get_resource_payload_by_type_from_db(cls, *, resource_type: str) -> dict[str, Any] | None:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamResource)

        row = await IamResource.objects.using(db_alias).filter(
            resource_type=resource_type,
            status=1,
        ).values(
            "id",
            "resource_type",
            "resource_name",
            "module_code",
            "access_mode",
            "status",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
        ).afirst()

        if row is None:
            return None

        payload = dict(row)
        payload["created_at"] = cls._datetime_to_cache_value(payload.get("created_at"))
        payload["updated_at"] = cls._datetime_to_cache_value(payload.get("updated_at"))
        return payload

    @classmethod
    def _resource_from_cache_payload(cls, payload: Any) -> IamResource | None:
        if payload is None:
            return None

        if not isinstance(payload, dict):
            return None

        try:
            resource_id = cls._required_int(payload.get("id"))
            status = cls._required_int(payload.get("status"))
        except (TypeError, ValueError):
            return None

        return IamResource(
            id=resource_id,
            resource_type=str(payload.get("resource_type") or ""),
            resource_name=str(payload.get("resource_name") or ""),
            module_code=str(payload.get("module_code") or ""),
            access_mode=str(payload.get("access_mode") or ""),
            status=status,
            created_by=cls._optional_int(payload.get("created_by")),
            updated_by=cls._optional_int(payload.get("updated_by")),
            created_at=cls._datetime_from_cache_value(payload.get("created_at")),
            updated_at=cls._datetime_from_cache_value(payload.get("updated_at")),
        )

    @staticmethod
    def _required_int(value: Any) -> int:
        if isinstance(value, bool):
            raise TypeError("boolean is not a valid integer value.")

        return int(value)

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        if value is None or value == "":
            return None

        if isinstance(value, bool):
            return None

        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _datetime_to_cache_value(value: Any) -> str | None:
        if value is None:
            return None

        if isinstance(value, datetime):
            return value.isoformat()

        return str(value)

    @staticmethod
    def _datetime_from_cache_value(value: Any) -> datetime | None:
        if isinstance(value, datetime):
            return value

        if not isinstance(value, str):
            return None

        text = value.strip()
        if not text:
            return None

        try:
            return datetime.fromisoformat(text)
        except ValueError:
            return None

    @classmethod
    async def has_action_for_resource_type(cls, *, resource_type: str, action_code: str) -> bool:
        cache_key = {
            "kind": "resource_action_exists",
            "resource_type": resource_type,
            "action_code": action_code,
        }

        async def load_from_db() -> bool:
            resource = await cls.get_resource_by_type(
                resource_type=resource_type,
            )

            if resource is None:
                return False

            return await cls._has_action_for_resource_id(
                resource_id=int(resource.id),
                action_code=action_code,
            )

        cached_value = await IamCacheService.aget_or_set(
            cache_key,
            load_from_db,
            ttl=IamCacheService.cache_ttl_seconds(),
        )

        if isinstance(cached_value, bool):
            return cached_value

        result = await load_from_db()
        await IamCacheService.aset(
            cache_key,
            result,
            ttl=IamCacheService.cache_ttl_seconds(),
        )
        return result

    @classmethod
    async def _has_action_for_resource_id(cls, *, resource_id: int, action_code: str) -> bool:
        db_alias = BaseRepository.resolve_db_alias(model_class=IamResourceAction)

        return await IamResourceAction.objects.using(db_alias).filter(
            resource_id=resource_id,
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

    @classmethod
    async def list_active_policy_rules_for_action(cls, *, action_code: str) -> list[dict[str, Any]]:
        cache_key = {
            "kind": "active_policy_rules_for_action",
            "action_code": action_code,
        }

        cached_rows = await IamCacheService.aget_or_set(
            cache_key,
            lambda: cls._list_active_policy_rules_for_action_from_db(action_code=action_code),
            ttl=IamCacheService.cache_ttl_seconds(),
        )

        if isinstance(cached_rows, list) and all(isinstance(item, dict) for item in cached_rows):
            return [
                dict(item)
                for item in cached_rows
            ]

        rows = await cls._list_active_policy_rules_for_action_from_db(
            action_code=action_code,
        )
        await IamCacheService.aset(
            cache_key,
            rows,
            ttl=IamCacheService.cache_ttl_seconds(),
        )
        return rows

    @classmethod
    async def _list_active_policy_rules_for_action_from_db(cls, *, action_code: str) -> list[dict[str, Any]]:
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

        return [
            dict(item)
            async for item in queryset
        ]
