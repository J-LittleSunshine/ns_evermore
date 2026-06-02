# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.utils import timezone

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.repositories import AuthorizeRepository, ResourceAclRepository, ResourceRelationRepository
from ns_backend.iam.schemas import DataScopeFieldMap
from ns_backend.iam.services.data_scope import DataScopeService
from ns_backend.iam.services.permission import PermissionService
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class ResourceAccessFilterService:
    """Resolve retrieval-stage access filters from ACL/RBAC/DataScope signals."""

    DEFAULT_RESOURCE_ID_FIELD = "resource_id"

    @staticmethod
    def _normalize_required_text(value: Any, field_name: str) -> str:
        text_value = str(value or "").strip()
        if not text_value:
            raise BusinessError(f"{field_name} is required", NsErrorCode.INVALID_VALUE)
        return text_value

    @classmethod
    def _normalize_resource_type(cls, value: Any) -> str:
        return cls._normalize_required_text(value, "resource_type").lower()

    @classmethod
    def _normalize_action_code(cls, value: Any) -> str:
        return cls._normalize_required_text(value, "action_code").lower()

    @classmethod
    def _derive_permission_code(cls, *, resource_type: str, action_code: str) -> str | None:
        normalized_resource = resource_type.replace(".", ":")
        if ":" not in normalized_resource:
            return None
        return f"{normalized_resource}:{action_code}"

    @classmethod
    async def _build_subject_bindings(cls, *, user: Any) -> list[tuple[str, int]]:
        user_id = int(getattr(user, "id"))
        subject_bindings: list[tuple[str, int]] = [("USER", user_id)]

        role_ids = await AuthorizeRepository.list_active_role_ids_for_user(user_id=user_id)
        subject_bindings.extend(("ROLE", role_id) for role_id in role_ids)

        department_id = getattr(user, "department_id", None)
        if department_id:
            subject_bindings.append(("DEPARTMENT", int(department_id)))

        company_id = getattr(user, "company_id", None)
        if company_id:
            subject_bindings.append(("ORGANIZATION", int(company_id)))

        subsidiary_id = getattr(user, "subsidiary_id", None)
        if subsidiary_id:
            subject_bindings.append(("SUBSIDIARY", int(subsidiary_id)))

        return subject_bindings

    @staticmethod
    def _build_field_map(field_map_data: Any) -> DataScopeFieldMap:
        if not isinstance(field_map_data, dict):
            return DataScopeFieldMap()

        return DataScopeFieldMap(
            self_field=field_map_data.get("self_field"),
            company_field=field_map_data.get("company_field", "company_id"),
            subsidiary_field=field_map_data.get("subsidiary_field", "subsidiary_id"),
            department_field=field_map_data.get("department_field", "department_id"),
        )

    @staticmethod
    def _apply_acl_effects(*, rows: list[dict[str, Any]], allow_ids: set[str], deny_ids: set[str]) -> None:
        for row in rows:
            resource_id = str(row.get("resource_id") or "").strip()
            if not resource_id:
                continue

            effect = str(row.get("effect") or "").strip().upper()
            if effect == "DENY":
                deny_ids.add(resource_id)
                continue

            if effect == "ALLOW":
                allow_ids.add(resource_id)

    @classmethod
    async def _collect_direct_acl_ids(
        cls,
        *,
        subject_bindings: list[tuple[str, int]],
        resource_type: str,
        action_code: str,
        now,
        allow_ids: set[str],
        deny_ids: set[str],
    ) -> None:
        rows = await ResourceAclRepository.list_active_effects_for_resource_type_action(
            subject_bindings=subject_bindings,
            resource_type=resource_type,
            action_code=action_code,
            now=now,
        )
        cls._apply_acl_effects(rows=rows, allow_ids=allow_ids, deny_ids=deny_ids)

    @classmethod
    async def _collect_inherited_acl_ids(
        cls,
        *,
        subject_bindings: list[tuple[str, int]],
        resource_type: str,
        action_code: str,
        now,
        allow_ids: set[str],
        deny_ids: set[str],
    ) -> None:
        ancestor_types = await ResourceRelationRepository.list_ancestor_resource_types(resource_type=resource_type)
        if not ancestor_types:
            return

        for ancestor_type in ancestor_types:
            ancestor_rows = await ResourceAclRepository.list_active_effects_for_resource_type_action(
                subject_bindings=subject_bindings,
                resource_type=ancestor_type,
                action_code=action_code,
                now=now,
            )
            if not ancestor_rows:
                continue

            for row in ancestor_rows:
                parent_resource_id = str(row.get("resource_id") or "").strip()
                if not parent_resource_id:
                    continue

                descendant_ids = await ResourceRelationRepository.list_descendant_resource_ids(
                    parent_resource_type=ancestor_type,
                    parent_resource_id=parent_resource_id,
                    target_resource_type=resource_type,
                )
                if not descendant_ids:
                    continue

                effect = str(row.get("effect") or "").strip().upper()
                if effect == "DENY":
                    deny_ids.update(descendant_ids)
                    continue

                if effect == "ALLOW":
                    allow_ids.update(descendant_ids)

    @classmethod
    async def resolve_retrieval_filter(
        cls,
        user: Any,
        resource_type: str,
        action_code: str,
        *,
        permission_code: str | None = None,
        field_map: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Resolve resource-level allow/deny ids and query-level filters for retrievers."""
        normalized_resource_type = cls._normalize_resource_type(resource_type)
        normalized_action_code = cls._normalize_action_code(action_code)

        if user is None or not bool(getattr(user, "is_active", False)):
            return {
                "allowed_resource_ids": [],
                "denied_resource_ids": [],
                "filters": {
                    "deny_all": True,
                    "orm": {"include": {f"{cls.DEFAULT_RESOURCE_ID_FIELD}__in": []}, "exclude": {}},
                    "vector": {"must": {"terms": {cls.DEFAULT_RESOURCE_ID_FIELD: []}}, "must_not": {}},
                    "reason": "USER_INACTIVE",
                },
            }

        if bool(getattr(user, "is_superuser", False)):
            return {
                "allowed_resource_ids": [],
                "denied_resource_ids": [],
                "filters": {
                    "allow_all": True,
                    "orm": {},
                    "vector": {},
                    "data_scope": {},
                },
            }

        subject_bindings = await cls._build_subject_bindings(user=user)
        now = timezone.now()

        allow_ids: set[str] = set()
        deny_ids: set[str] = set()
        await cls._collect_direct_acl_ids(
            subject_bindings=subject_bindings,
            resource_type=normalized_resource_type,
            action_code=normalized_action_code,
            now=now,
            allow_ids=allow_ids,
            deny_ids=deny_ids,
        )
        await cls._collect_inherited_acl_ids(
            subject_bindings=subject_bindings,
            resource_type=normalized_resource_type,
            action_code=normalized_action_code,
            now=now,
            allow_ids=allow_ids,
            deny_ids=deny_ids,
        )

        # Deny always overrides allow.
        allow_ids.difference_update(deny_ids)

        resolved_permission_code = permission_code or cls._derive_permission_code(
            resource_type=normalized_resource_type,
            action_code=normalized_action_code,
        )
        has_rbac_allow = False
        if resolved_permission_code:
            has_rbac_allow = await PermissionService.has_permission(user=user, permission_code=resolved_permission_code)

        data_scope_filters: dict[str, Any] = {}
        data_scope_reason: str | None = None
        if resolved_permission_code:
            filter_plan = await DataScopeService.resolve_filter_plan(
                user=user,
                permission_code=resolved_permission_code,
                field_map=cls._build_field_map(field_map),
            )
            if filter_plan.allowed:
                data_scope_filters = dict(filter_plan.filters)
            else:
                data_scope_reason = filter_plan.reason

        deny_all = not has_rbac_allow and not allow_ids
        orm_filters: dict[str, Any] = dict(data_scope_filters)
        orm_include: dict[str, Any] = {}
        orm_exclude: dict[str, Any] = {}
        vector_must: dict[str, Any] = {}
        vector_must_not: dict[str, Any] = {}

        if allow_ids and not has_rbac_allow:
            orm_include[f"{cls.DEFAULT_RESOURCE_ID_FIELD}__in"] = sorted(allow_ids)
            vector_must["terms"] = {cls.DEFAULT_RESOURCE_ID_FIELD: sorted(allow_ids)}

        if deny_ids:
            orm_exclude[f"{cls.DEFAULT_RESOURCE_ID_FIELD}__in"] = sorted(deny_ids)
            vector_must_not["terms"] = {cls.DEFAULT_RESOURCE_ID_FIELD: sorted(deny_ids)}

        if deny_all:
            orm_include[f"{cls.DEFAULT_RESOURCE_ID_FIELD}__in"] = sorted(allow_ids)

        result_filters: dict[str, Any] = {
            "deny_all": deny_all,
            "default_allow": has_rbac_allow,
            "orm": {
                "include": {**orm_filters, **orm_include},
                "exclude": orm_exclude,
            },
            "vector": {
                "must": vector_must,
                "must_not": vector_must_not,
            },
            "data_scope": data_scope_filters,
        }
        if data_scope_reason:
            result_filters["data_scope_reason"] = data_scope_reason

        return {
            "allowed_resource_ids": sorted(allow_ids),
            "denied_resource_ids": sorted(deny_ids),
            "filters": result_filters,
        }

