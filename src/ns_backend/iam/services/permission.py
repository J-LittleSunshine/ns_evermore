# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    TYPE_CHECKING,
)

from django.utils import timezone

from ns_backend.iam.constants import (
    PERMISSION_EFFECT_ALLOW,
    PERMISSION_EFFECT_DENY,
    PERMISSION_TYPE_MENU,
    ROLE_SCOPE_ENTERPRISE,
    ROLE_SCOPE_PERSONAL,
    USER_TYPE_ENTERPRISE,
    USER_TYPE_PERSONAL,
)
from ns_backend.iam.repositories import PermissionRepository
from ns_backend.iam.services.cache import IamCacheService

if TYPE_CHECKING:
    pass


class PermissionService:
    MAX_ANCESTOR_DEPTH = 20

    SUBJECT_USER = "user"
    SUBJECT_DEPARTMENT = "department"
    SUBJECT_SUBSIDIARY = "subsidiary"

    @classmethod
    async def get_active_permission_ids_with_ancestors(cls, permission_code: str) -> list[int]:
        cache_key = {
            "kind": "permission_ancestor_ids",
            "permission_code": permission_code,
        }

        cached_ids = await IamCacheService.aget_or_set(
            cache_key,
            lambda: cls._get_active_permission_ids_with_ancestors_from_db(permission_code),
            ttl=IamCacheService.cache_ttl_seconds(),
        )

        if isinstance(cached_ids, list):
            normalized_ids: list[int] = []

            for item in cached_ids:
                if isinstance(item, bool):
                    return await cls._get_active_permission_ids_with_ancestors_from_db(permission_code)

                try:
                    normalized_ids.append(int(item))
                except (TypeError, ValueError):
                    return await cls._get_active_permission_ids_with_ancestors_from_db(permission_code)

            return normalized_ids

        return await cls._get_active_permission_ids_with_ancestors_from_db(permission_code)

    @classmethod
    async def _get_active_permission_ids_with_ancestors_from_db(cls, permission_code: str) -> list[int]:
        permission = await PermissionRepository.get_active_permission_by_code(permission_code)
        if not permission:
            return []

        permission_ids: list[int] = []
        seen_ids: set[int] = set()
        current = permission

        for _ in range(cls.MAX_ANCESTOR_DEPTH):
            current_id = current.id
            if current_id in seen_ids:
                break

            seen_ids.add(current_id)
            permission_ids.append(current_id)

            if not current.parent_id:
                break

            next_permission = await PermissionRepository.get_active_permission_by_id(
                current.parent_id,
            )
            if not next_permission:
                break

            current = next_permission

        return permission_ids

    @classmethod
    async def has_permission(cls, user: Any, permission_code: str) -> bool:
        if not user or not bool(getattr(user, "is_active", False)):
            return False

        if bool(getattr(user, "is_superuser", False)):
            return True

        if not permission_code:
            return False

        permission_ids = await cls.get_active_permission_ids_with_ancestors(permission_code)
        if not permission_ids:
            return False

        now = timezone.now()
        user_type = getattr(user, "user_type", None)

        if user_type == USER_TYPE_PERSONAL:
            return await cls._has_personal_permission(
                user=user,
                permission_ids=permission_ids,
                now=now,
            )

        if user_type == USER_TYPE_ENTERPRISE:
            return await cls._has_enterprise_permission(
                user=user,
                permission_ids=permission_ids,
                now=now,
            )

        return False

    @classmethod
    async def _has_direct_effect(cls, *, subject_type: str, subject_id: int, permission_ids: list[int], effect: str, now) -> bool:
        if subject_type == cls.SUBJECT_USER:
            return await PermissionRepository.has_user_effect(
                user_id=subject_id,
                permission_ids=permission_ids,
                effect=effect,
                now=now,
            )

        if subject_type == cls.SUBJECT_DEPARTMENT:
            return await PermissionRepository.has_department_effect(
                department_id=subject_id,
                permission_ids=permission_ids,
                effect=effect,
                now=now,
            )

        if subject_type == cls.SUBJECT_SUBSIDIARY:
            return await PermissionRepository.has_subsidiary_effect(
                subsidiary_id=subject_id,
                permission_ids=permission_ids,
                effect=effect,
                now=now,
            )

        return False

    @classmethod
    async def _has_role_allow(cls, *, user_id: int, permission_ids: list[int], now, role_scope: str, company_id: int | None) -> bool:
        return await PermissionRepository.has_role_allow(
            user_id=user_id,
            permission_ids=permission_ids,
            now=now,
            role_scope=role_scope,
            company_id=company_id,
        )

    @classmethod
    async def _has_personal_permission(cls, *, user: Any, permission_ids: list[int], now) -> bool:
        user_id = int(getattr(user, "id"))

        if await cls._has_direct_effect(subject_type=cls.SUBJECT_USER, subject_id=user_id, permission_ids=permission_ids, effect=PERMISSION_EFFECT_DENY, now=now):
            return False

        has_user_allow = await cls._has_direct_effect(
            subject_type=cls.SUBJECT_USER,
            subject_id=user_id,
            permission_ids=permission_ids,
            effect=PERMISSION_EFFECT_ALLOW,
            now=now,
        )
        has_role_allow = await cls._has_role_allow(
            user_id=user_id,
            permission_ids=permission_ids,
            now=now,
            role_scope=ROLE_SCOPE_PERSONAL,
            company_id=None,
        )

        return has_user_allow or has_role_allow

    @classmethod
    async def _has_enterprise_permission(cls, *, user: Any, permission_ids: list[int], now) -> bool:
        company_id = getattr(user, "company_id", None)
        if not company_id:
            return False

        user_id = int(getattr(user, "id"))
        department_id = getattr(user, "department_id", None)
        subsidiary_id = getattr(user, "subsidiary_id", None)

        has_user_deny = await cls._has_direct_effect(
            subject_type=cls.SUBJECT_USER,
            subject_id=user_id,
            permission_ids=permission_ids,
            effect=PERMISSION_EFFECT_DENY,
            now=now,
        )

        has_department_deny = False
        if department_id:
            has_department_deny = await cls._has_direct_effect(
                subject_type=cls.SUBJECT_DEPARTMENT,
                subject_id=department_id,
                permission_ids=permission_ids,
                effect=PERMISSION_EFFECT_DENY,
                now=now,
            )

        has_subsidiary_deny = False
        if subsidiary_id:
            has_subsidiary_deny = await cls._has_direct_effect(
                subject_type=cls.SUBJECT_SUBSIDIARY,
                subject_id=subsidiary_id,
                permission_ids=permission_ids,
                effect=PERMISSION_EFFECT_DENY,
                now=now,
            )

        if has_user_deny or has_department_deny or has_subsidiary_deny:
            return False

        has_user_allow = await cls._has_direct_effect(
            subject_type=cls.SUBJECT_USER,
            subject_id=user_id,
            permission_ids=permission_ids,
            effect=PERMISSION_EFFECT_ALLOW,
            now=now,
        )
        has_role_allow = await cls._has_role_allow(
            user_id=user_id,
            permission_ids=permission_ids,
            now=now,
            role_scope=ROLE_SCOPE_ENTERPRISE,
            company_id=company_id,
        )

        has_department_allow = False
        if department_id:
            has_department_allow = await cls._has_direct_effect(
                subject_type=cls.SUBJECT_DEPARTMENT,
                subject_id=department_id,
                permission_ids=permission_ids,
                effect=PERMISSION_EFFECT_ALLOW,
                now=now,
            )

        has_subsidiary_allow = False
        if subsidiary_id:
            has_subsidiary_allow = await cls._has_direct_effect(
                subject_type=cls.SUBJECT_SUBSIDIARY,
                subject_id=subsidiary_id,
                permission_ids=permission_ids,
                effect=PERMISSION_EFFECT_ALLOW,
                now=now,
            )

        return (
                has_user_allow
                or has_role_allow
                or has_department_allow
                or has_subsidiary_allow
        )

    @classmethod
    async def list_permission_codes(cls, user: Any) -> list[str]:
        active_permissions = await cls._list_active_permissions()
        effective_ids = await cls.resolve_effective_permission_ids(
            user=user,
            active_permissions=active_permissions,
        )

        codes = [
            item["permission_code"]
            for item in active_permissions
            if item["id"] in effective_ids
        ]

        return sorted(codes)

    @classmethod
    async def list_menu_tree(cls, user: Any) -> list[dict[str, Any]]:
        active_permissions = await cls._list_active_permissions()
        effective_ids = await cls.resolve_effective_permission_ids(
            user=user,
            active_permissions=active_permissions,
        )

        return cls.build_menu_tree(active_permissions, effective_ids)

    @staticmethod
    async def _list_active_permissions() -> list[dict[str, Any]]:
        cache_key = {
            "kind": "active_permissions",
        }

        cached_rows = await IamCacheService.aget_or_set(
            cache_key,
            PermissionRepository.list_active_permissions,
            ttl=IamCacheService.cache_ttl_seconds(),
        )

        if isinstance(cached_rows, list) and all(isinstance(item, dict) for item in cached_rows):
            return [
                dict(item)
                for item in cached_rows
            ]

        rows = await PermissionRepository.list_active_permissions()
        await IamCacheService.aset(
            cache_key,
            rows,
            ttl=IamCacheService.cache_ttl_seconds(),
        )
        return rows

    @classmethod
    async def resolve_effective_permission_ids(cls, *, user: Any, active_permissions: list[dict[str, Any]] | None = None) -> set[int]:
        if not user or not bool(getattr(user, "is_active", False)):
            return set()

        if active_permissions is None:
            active_permissions = await cls._list_active_permissions()

        active_ids = {
            item["id"]
            for item in active_permissions
        }

        if bool(getattr(user, "is_superuser", False)):
            return active_ids

        now = timezone.now()
        user_id = int(getattr(user, "id"))
        user_type = getattr(user, "user_type", None)

        if user_type == USER_TYPE_PERSONAL:
            deny_ids = await cls._list_user_permission_ids(
                user_id,
                now,
                effect=PERMISSION_EFFECT_DENY,
            )
            allow_ids = await cls._list_user_permission_ids(
                user_id,
                now,
                effect=PERMISSION_EFFECT_ALLOW,
            )
            allow_ids.update(
                await cls._list_role_permission_ids(
                    user_id=user_id,
                    now=now,
                    role_scope=ROLE_SCOPE_PERSONAL,
                    company_id=None,
                )
            )

            return cls.expand_effective_permission_ids(
                active_permissions=active_permissions,
                allow_ids=allow_ids,
                deny_ids=deny_ids,
            )

        if user_type == USER_TYPE_ENTERPRISE:
            company_id = getattr(user, "company_id", None)
            if not company_id:
                return set()

            deny_ids = await cls._list_user_permission_ids(
                user_id,
                now,
                effect=PERMISSION_EFFECT_DENY,
            )
            allow_ids = await cls._list_user_permission_ids(
                user_id,
                now,
                effect=PERMISSION_EFFECT_ALLOW,
            )
            allow_ids.update(
                await cls._list_role_permission_ids(
                    user_id=user_id,
                    now=now,
                    role_scope=ROLE_SCOPE_ENTERPRISE,
                    company_id=company_id,
                )
            )

            department_id = getattr(user, "department_id", None)
            subsidiary_id = getattr(user, "subsidiary_id", None)

            if department_id:
                deny_ids.update(
                    await cls._list_department_permission_ids(
                        department_id,
                        now,
                        effect=PERMISSION_EFFECT_DENY,
                    )
                )
                allow_ids.update(
                    await cls._list_department_permission_ids(
                        department_id,
                        now,
                        effect=PERMISSION_EFFECT_ALLOW,
                    )
                )

            if subsidiary_id:
                deny_ids.update(
                    await cls._list_subsidiary_permission_ids(
                        subsidiary_id,
                        now,
                        effect=PERMISSION_EFFECT_DENY,
                    )
                )
                allow_ids.update(
                    await cls._list_subsidiary_permission_ids(
                        subsidiary_id,
                        now,
                        effect=PERMISSION_EFFECT_ALLOW,
                    )
                )

            return cls.expand_effective_permission_ids(
                active_permissions=active_permissions,
                allow_ids=allow_ids,
                deny_ids=deny_ids,
            )

        return set()

    @staticmethod
    async def _list_user_permission_ids(user_id: int, now, *, effect: str) -> set[int]:
        return await PermissionRepository.list_user_permission_ids(
            user_id=user_id,
            now=now,
            effect=effect,
        )

    @staticmethod
    async def _list_department_permission_ids(department_id: int, now, *, effect: str) -> set[int]:
        return await PermissionRepository.list_department_permission_ids(
            department_id=department_id,
            now=now,
            effect=effect,
        )

    @staticmethod
    async def _list_subsidiary_permission_ids(subsidiary_id: int, now, *, effect: str) -> set[int]:
        return await PermissionRepository.list_subsidiary_permission_ids(
            subsidiary_id=subsidiary_id,
            now=now,
            effect=effect,
        )

    @staticmethod
    async def _list_role_permission_ids(*, user_id: int, now, role_scope: str, company_id: int | None) -> set[int]:
        return await PermissionRepository.list_role_permission_ids(
            user_id=user_id,
            now=now,
            role_scope=role_scope,
            company_id=company_id,
        )

    @classmethod
    def expand_effective_permission_ids(cls, *, active_permissions: list[dict[str, Any]], allow_ids: set[int], deny_ids: set[int]) -> set[int]:
        permission_map = {
            item["id"]: item
            for item in active_permissions
        }
        active_ids = set(permission_map.keys())
        normalized_allow = allow_ids & active_ids
        normalized_deny = deny_ids & active_ids

        effective_ids: set[int] = set()

        for permission_id in active_ids:
            chain_ids = cls.get_permission_chain_ids(permission_id=permission_id, permission_map=permission_map)

            if any(chain_id in normalized_deny for chain_id in chain_ids):
                continue

            if any(chain_id in normalized_allow for chain_id in chain_ids):
                effective_ids.add(permission_id)

        return effective_ids

    @classmethod
    def get_permission_chain_ids(cls, *, permission_id: int, permission_map: dict[int, dict[str, Any]]) -> list[int]:
        chain_ids: list[int] = []
        visited_ids: set[int] = set()
        current_id = permission_id

        for _ in range(cls.MAX_ANCESTOR_DEPTH):
            if current_id in visited_ids:
                break

            permission = permission_map.get(current_id)
            if not permission:
                break

            visited_ids.add(current_id)
            chain_ids.append(current_id)

            parent_id = permission.get("parent_id")
            if not parent_id:
                break

            current_id = parent_id

        return chain_ids

    @staticmethod
    def build_menu_tree(permissions: list[dict[str, Any]], allowed_ids: set[int]) -> list[dict[str, Any]]:
        menu_permissions = {
            item["id"]: item
            for item in permissions
            if item.get("permission_type") == PERMISSION_TYPE_MENU
        }
        included_ids = {
            item_id
            for item_id in allowed_ids
            if item_id in menu_permissions
        }

        for permission_id in list(included_ids):
            current_id = permission_id
            visited_chain: set[int] = set()

            while current_id in menu_permissions and current_id not in visited_chain:
                visited_chain.add(current_id)
                parent_id = menu_permissions[current_id].get("parent_id")

                if not parent_id or parent_id not in menu_permissions:
                    break

                included_ids.add(parent_id)
                current_id = parent_id

        if not included_ids:
            return []

        children_map: dict[int, list[int]] = {}

        for node_id in included_ids:
            parent_id = menu_permissions[node_id].get("parent_id")

            if parent_id in included_ids and parent_id != node_id:
                children_map.setdefault(parent_id, []).append(node_id)

        root_ids = [
            node_id
            for node_id in included_ids
            if menu_permissions[node_id].get("parent_id") not in included_ids
               or menu_permissions[node_id].get("parent_id") == node_id
        ]

        built_ids: set[int] = set()

        def build_node(_node_id: int, _path_ids: set[int]) -> dict[str, Any]:
            built_ids.add(_node_id)
            node = menu_permissions[_node_id]
            child_items: list[dict[str, Any]] = []

            next_path_ids = set(_path_ids)
            next_path_ids.add(_node_id)

            child_ids = sorted(
                children_map.get(_node_id, []),
                key=lambda _child_id: menu_permissions[_child_id]["permission_code"],
            )

            for child_id in child_ids:
                if child_id in next_path_ids:
                    continue

                child_items.append(
                    build_node(child_id, next_path_ids)
                )

            return {
                "id": node["id"],
                "code": node["permission_code"],
                "name": node["permission_name"],
                "children": child_items,
            }

        tree: list[dict[str, Any]] = []

        for root_id in sorted(root_ids, key=lambda item_id: menu_permissions[item_id]["permission_code"]):
            tree.append(
                build_node(root_id, set())
            )

        remaining_ids = sorted(
            [
                node_id
                for node_id in included_ids
                if node_id not in built_ids
            ],
            key=lambda item_id: menu_permissions[item_id]["permission_code"],
        )

        for node_id in remaining_ids:
            tree.append(
                build_node(node_id, set())
            )

        return tree
