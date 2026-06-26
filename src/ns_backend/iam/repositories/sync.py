# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from asgiref.sync import sync_to_async
from django.db import (
    IntegrityError,
    transaction,
)
from django.utils import timezone

from backend.common import BaseRepository
from ns_backend.iam.errors import (
    IamInvalidRelationError,
    IamManagementPersistenceError,
)
from ns_backend.iam.models import (
    IamPermission,
    IamResource,
    IamResourceAction,
)
from ns_backend.iam.repositories.management import IamManagementRepository


class IamSyncRepository(BaseRepository):
    RESOURCE_FIELDS = (
        "id",
        "resource_type",
        "resource_name",
        "module_code",
        "access_mode",
        "status",
    )

    RESOURCE_ACTION_FIELDS = (
        "id",
        "resource_id",
        "action_code",
        "action_name",
        "status",
    )

    PERMISSION_FIELDS = (
        "id",
        "permission_code",
        "permission_name",
        "permission_type",
        "parent_id",
        "status",
    )

    @classmethod
    async def sync_resources(cls, *, resources: list[dict[str, Any]], operator_id: int | None) -> dict[str, Any]:
        db_alias = cls.resolve_db_alias(model_class=IamResource)

        return await sync_to_async(cls._sync_resources_sync, thread_sensitive=True)(
            resources=resources,
            operator_id=operator_id,
            db_alias=db_alias,
        )

    @classmethod
    def _sync_resources_sync(cls, *, resources: list[dict[str, Any]], operator_id: int | None, db_alias: str) -> dict[str, Any]:
        summary = cls.build_empty_summary()
        items: list[dict[str, Any]] = []

        try:
            with transaction.atomic(using=db_alias):
                for spec in resources:
                    resource, resource_result = cls._upsert_resource_sync(
                        spec=spec,
                        operator_id=operator_id,
                        db_alias=db_alias,
                    )

                    cls.increase_summary(
                        summary=summary,
                        section="resources",
                        result=resource_result,
                    )

                    action_items: list[dict[str, Any]] = []
                    for action_spec in spec.get("actions", []):
                        action, action_result = cls._upsert_resource_action_sync(
                            resource=resource,
                            spec=action_spec,
                            operator_id=operator_id,
                            db_alias=db_alias,
                        )

                        cls.increase_summary(
                            summary=summary,
                            section="actions",
                            result=action_result,
                        )

                        action_items.append(
                            {
                                "result": action_result,
                                **IamManagementRepository.serialize_instance(
                                    instance=action,
                                    fields=cls.RESOURCE_ACTION_FIELDS,
                                ),
                            }
                        )

                    items.append(
                        {
                            "result": resource_result,
                            "resource": IamManagementRepository.serialize_instance(
                                instance=resource,
                                fields=cls.RESOURCE_FIELDS,
                            ),
                            "actions": action_items,
                        }
                    )
        except IntegrityError as exc:
            raise IamManagementPersistenceError(
                "Failed to sync IAM resources.",
                details={
                    "resource_count": len(resources),
                },
            ) from exc

        return {
            **summary,
            "total": len(resources),
            "items": items,
        }

    @classmethod
    def _upsert_resource_sync(cls, *, spec: dict[str, Any], operator_id: int | None, db_alias: str) -> tuple[IamResource, str]:
        now = timezone.now()

        resource = (
            IamResource.objects.using(db_alias)
            .select_for_update()
            .filter(resource_type=spec["resource_type"])
            .first()
        )

        if resource is None:
            resource = IamResource.objects.using(db_alias).create(
                resource_type=spec["resource_type"],
                resource_name=spec["resource_name"],
                module_code=spec["module_code"],
                access_mode=spec["access_mode"],
                status=spec["status"],
                created_by=operator_id,
                updated_by=operator_id,
                created_at=now,
                updated_at=now,
            )
            return resource, "created"

        update_fields: list[str] = []
        for field in (
                "resource_name",
                "module_code",
                "access_mode",
                "status",
        ):
            value = spec[field]
            if getattr(resource, field) == value:
                continue

            setattr(resource, field, value)
            update_fields.append(field)

        if not update_fields:
            return resource, "skipped"

        resource.updated_by = operator_id
        resource.updated_at = now
        update_fields.extend(
            [
                "updated_by",
                "updated_at",
            ]
        )
        resource.save(
            using=db_alias,
            update_fields=update_fields,
        )
        return resource, "updated"

    @classmethod
    def _upsert_resource_action_sync(cls, *, resource: IamResource, spec: dict[str, Any], operator_id: int | None, db_alias: str) -> tuple[IamResourceAction, str]:
        now = timezone.now()

        action = (
            IamResourceAction.objects.using(db_alias)
            .select_for_update()
            .filter(
                resource_id=resource.id,
                action_code=spec["action_code"],
            )
            .first()
        )

        if action is None:
            action = IamResourceAction.objects.using(db_alias).create(
                resource_id=resource.id,
                action_code=spec["action_code"],
                action_name=spec["action_name"],
                status=spec["status"],
                created_by=operator_id,
                updated_by=operator_id,
                created_at=now,
                updated_at=now,
            )
            return action, "created"

        update_fields: list[str] = []
        for field in (
                "action_name",
                "status",
        ):
            value = spec[field]
            if getattr(action, field) == value:
                continue

            setattr(action, field, value)
            update_fields.append(field)

        if not update_fields:
            return action, "skipped"

        action.updated_by = operator_id
        action.updated_at = now
        update_fields.extend(
            [
                "updated_by",
                "updated_at",
            ]
        )
        action.save(
            using=db_alias,
            update_fields=update_fields,
        )
        return action, "updated"

    @classmethod
    async def sync_permissions(cls, *, permissions: list[dict[str, Any]], operator_id: int | None) -> dict[str, Any]:
        db_alias = cls.resolve_db_alias(model_class=IamPermission)

        return await sync_to_async(cls._sync_permissions_sync, thread_sensitive=True)(
            permissions=permissions,
            operator_id=operator_id,
            db_alias=db_alias,
        )

    @classmethod
    def _sync_permissions_sync(cls, *, permissions: list[dict[str, Any]], operator_id: int | None, db_alias: str) -> dict[str, Any]:
        summary = cls.build_empty_summary()
        items: list[dict[str, Any]] = []
        result_by_code: dict[str, str] = {}

        try:
            with transaction.atomic(using=db_alias):
                for spec in permissions:
                    permission, result = cls._upsert_permission_base_sync(
                        spec=spec,
                        operator_id=operator_id,
                        db_alias=db_alias,
                    )
                    result_by_code[permission.permission_code] = result

                requested_codes = {
                    spec["permission_code"]
                    for spec in permissions
                }
                parent_codes = {
                    spec["parent_code"]
                    for spec in permissions
                    if spec.get("parent_code")
                }

                permission_by_code = {
                    item.permission_code: item
                    for item in IamPermission.objects.using(db_alias)
                    .select_for_update()
                    .filter(permission_code__in=list(requested_codes | parent_codes))
                }

                for spec in permissions:
                    permission = permission_by_code[spec["permission_code"]]
                    parent_id = cls._resolve_parent_id_sync(
                        spec=spec,
                        permission_by_code=permission_by_code,
                        db_alias=db_alias,
                    )

                    parent_changed = permission.parent_id != parent_id
                    if parent_changed:
                        now = timezone.now()
                        permission.parent_id = parent_id
                        permission.updated_by = operator_id
                        permission.updated_at = now
                        permission.save(
                            using=db_alias,
                            update_fields=[
                                "parent_id",
                                "updated_by",
                                "updated_at",
                            ],
                        )

                    result = result_by_code[permission.permission_code]
                    if result == "skipped" and parent_changed:
                        result = "updated"

                    cls.increase_summary(
                        summary=summary,
                        section="permissions",
                        result=result,
                    )

                    items.append(
                        {
                            "result": result,
                            **IamManagementRepository.serialize_instance(
                                instance=permission,
                                fields=cls.PERMISSION_FIELDS,
                            ),
                        }
                    )
        except IntegrityError as exc:
            raise IamManagementPersistenceError(
                "Failed to sync IAM permissions.",
                details={
                    "permission_count": len(permissions),
                },
            ) from exc

        return {
            **summary,
            "total": len(permissions),
            "items": items,
        }

    @classmethod
    def _upsert_permission_base_sync(cls, *, spec: dict[str, Any], operator_id: int | None, db_alias: str) -> tuple[IamPermission, str]:
        now = timezone.now()

        permission = (
            IamPermission.objects.using(db_alias)
            .select_for_update()
            .filter(permission_code=spec["permission_code"])
            .first()
        )

        if permission is None:
            permission = IamPermission.objects.using(db_alias).create(
                permission_code=spec["permission_code"],
                permission_name=spec["permission_name"],
                permission_type=spec["permission_type"],
                parent_id=None,
                status=spec["status"],
                created_by=operator_id,
                updated_by=operator_id,
                created_at=now,
                updated_at=now,
            )
            return permission, "created"

        if permission.permission_type != spec["permission_type"]:
            raise IamInvalidRelationError(
                "permission_type cannot be changed by sync.",
                details={
                    "permission_code": permission.permission_code,
                    "current_permission_type": permission.permission_type,
                    "request_permission_type": spec["permission_type"],
                },
            )

        update_fields: list[str] = []
        for field in (
                "permission_name",
                "status",
        ):
            value = spec[field]
            if getattr(permission, field) == value:
                continue

            setattr(permission, field, value)
            update_fields.append(field)

        if not update_fields:
            return permission, "skipped"

        permission.updated_by = operator_id
        permission.updated_at = now
        update_fields.extend(
            [
                "updated_by",
                "updated_at",
            ]
        )
        permission.save(
            using=db_alias,
            update_fields=update_fields,
        )
        return permission, "updated"

    @staticmethod
    def _resolve_parent_id_sync(*, spec: dict[str, Any], permission_by_code: dict[str, IamPermission], db_alias: str, ) -> int | None:
        parent_code = spec.get("parent_code")
        if parent_code:
            parent = permission_by_code.get(parent_code)
            if parent is None:
                raise IamInvalidRelationError(
                    "Parent permission does not exist.",
                    details={
                        "parent_code": parent_code,
                    },
                )
            return parent.id

        parent_id = spec.get("parent_id")
        if parent_id is None:
            return None

        parent = (
            IamPermission.objects.using(db_alias)
            .select_for_update()
            .filter(id=parent_id)
            .first()
        )

        if parent is None:
            raise IamInvalidRelationError(
                "Parent permission does not exist.",
                details={
                    "parent_id": parent_id,
                },
            )

        return parent.id

    @staticmethod
    def build_empty_summary() -> dict[str, Any]:
        return {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "resources": {
                "created": 0,
                "updated": 0,
                "skipped": 0,
            },
            "actions": {
                "created": 0,
                "updated": 0,
                "skipped": 0,
            },
            "permissions": {
                "created": 0,
                "updated": 0,
                "skipped": 0,
            },
        }

    @staticmethod
    def increase_summary(*, summary: dict[str, Any], section: str, result: str) -> None:
        if result not in (
                "created",
                "updated",
                "skipped",
        ):
            return

        summary[result] += 1

        if section in summary:
            summary[section][result] += 1
