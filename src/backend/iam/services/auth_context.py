# -*- coding: utf-8 -*-
from __future__ import annotations

from django.utils import timezone

from iam.policies.tenant import TenantPolicy
from iam.repositories.auth_context import AuthContextRepository
from iam.services.tenant import TenantService


class AuthContextService:
    USER_TYPE_PERSONAL = "PERSONAL"
    USER_TYPE_ENTERPRISE = "ENTERPRISE"

    @classmethod
    def build_profile(cls, user) -> dict:
        context = TenantService.from_user(user)

        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "email": user.email,
                "phone": user.phone,
                "user_type": user.user_type,
                "company_id": user.company_id,
                "subsidiary_id": user.subsidiary_id,
                "department_id": user.department_id,
                "is_active": user.is_active,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
            },
            "tenant": {
                "is_platform_admin": TenantPolicy.is_platform_admin(context),
                "is_enterprise_user": TenantPolicy.is_enterprise_user(context),
                "is_personal_user": TenantPolicy.is_personal_user(context),
                "company_id": context.company_id,
                "subsidiary_id": context.subsidiary_id,
                "department_id": context.department_id,
            },
        }

    @classmethod
    async def list_permission_codes(cls, user) -> list[str]:
        active_permissions = await AuthContextRepository.list_active_permissions()
        effective_ids = await cls.resolve_effective_permission_ids(user)

        codes = [
            permission["permission_code"]
            for permission in active_permissions
            if permission["id"] in effective_ids
        ]
        return sorted(codes)

    @classmethod
    async def list_menu_tree(cls, user) -> list[dict]:
        active_permissions = await AuthContextRepository.list_active_permissions()
        effective_ids = await cls.resolve_effective_permission_ids(user)
        return cls.build_menu_tree(active_permissions, effective_ids)

    @classmethod
    async def resolve_effective_permission_ids(cls, user) -> set[int]:
        if not user or not user.is_active:
            return set()

        active_permissions = await AuthContextRepository.list_active_permissions()
        active_ids = {permission["id"] for permission in active_permissions}

        if user.is_superuser:
            return active_ids

        now = timezone.now()

        if user.user_type == cls.USER_TYPE_PERSONAL:
            deny_ids = await AuthContextRepository.list_user_deny_permission_ids(user.id, now)
            allow_ids = await AuthContextRepository.list_user_allow_permission_ids(user.id, now)
            allow_ids.update(
                await AuthContextRepository.list_role_allow_permission_ids(
                    user_id=user.id,
                    now=now,
                    role_scope=cls.USER_TYPE_PERSONAL,
                    company_id=None,
                ),
            )
            return (allow_ids - deny_ids) & active_ids

        if user.user_type == cls.USER_TYPE_ENTERPRISE:
            if not user.company_id:
                return set()

            deny_ids = await AuthContextRepository.list_user_deny_permission_ids(user.id, now)
            allow_ids = await AuthContextRepository.list_user_allow_permission_ids(user.id, now)
            allow_ids.update(
                await AuthContextRepository.list_role_allow_permission_ids(
                    user_id=user.id,
                    now=now,
                    role_scope=cls.USER_TYPE_ENTERPRISE,
                    company_id=user.company_id,
                ),
            )

            if user.department_id:
                deny_ids.update(
                    await AuthContextRepository.list_department_deny_permission_ids(
                        user.department_id,
                        now,
                    ),
                )
                allow_ids.update(
                    await AuthContextRepository.list_department_allow_permission_ids(
                        user.department_id,
                        now,
                    ),
                )

            if user.subsidiary_id:
                deny_ids.update(
                    await AuthContextRepository.list_subsidiary_deny_permission_ids(
                        user.subsidiary_id,
                        now,
                    ),
                )
                allow_ids.update(
                    await AuthContextRepository.list_subsidiary_allow_permission_ids(
                        user.subsidiary_id,
                        now,
                    ),
                )

            return (allow_ids - deny_ids) & active_ids

        return set()

    @staticmethod
    def build_menu_tree(permissions: list[dict], allowed_ids: set[int]) -> list[dict]:
        menu_permissions = {
            permission["id"]: permission
            for permission in permissions
            if permission.get("permission_type") == "MENU"
        }

        included_ids: set[int] = {
            permission_id
            for permission_id in allowed_ids
            if permission_id in menu_permissions
        }

        # Include parent menus to keep the rendered tree connected.
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

        def build_node(node_id: int, path_ids: set[int]) -> dict:
            built_ids.add(node_id)
            node = menu_permissions[node_id]
            child_items: list[dict] = []

            next_path_ids = set(path_ids)
            next_path_ids.add(node_id)

            child_ids = sorted(
                children_map.get(node_id, []),
                key=lambda child_id: menu_permissions[child_id]["permission_code"],
            )
            for child_id in child_ids:
                if child_id in next_path_ids:
                    continue
                child_items.append(build_node(child_id, next_path_ids))

            return {
                "id": node["id"],
                "code": node["permission_code"],
                "name": node["permission_name"],
                "children": child_items,
            }

        tree: list[dict] = []
        for root_id in sorted(root_ids, key=lambda item_id: menu_permissions[item_id]["permission_code"]):
            tree.append(build_node(root_id, set()))

        remaining_ids = sorted(
            [node_id for node_id in included_ids if node_id not in built_ids],
            key=lambda item_id: menu_permissions[item_id]["permission_code"],
        )
        for node_id in remaining_ids:
            tree.append(build_node(node_id, set()))

        return tree


__all__ = ["AuthContextService"]

