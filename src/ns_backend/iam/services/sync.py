# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any

from ns_backend.iam.constants import (
    PERMISSION_TYPE_ACTION,
    PERMISSION_TYPE_DATA,
    PERMISSION_TYPE_MENU,
    RESOURCE_ACCESS_MODE_ACL_REQUIRED,
    RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW,
)
from ns_backend.iam.errors import IamManagementRequestInvalidError
from ns_backend.iam.repositories import IamSyncRepository
from ns_backend.iam.validators import (
    ResourceActionValidator,
    ResourceValidator,
)


class IamSyncService:
    repository_class = IamSyncRepository

    max_batch_size = 200

    permission_types = (
        PERMISSION_TYPE_MENU,
        PERMISSION_TYPE_ACTION,
        PERMISSION_TYPE_DATA,
    )

    access_modes = (
        RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW,
        RESOURCE_ACCESS_MODE_ACL_REQUIRED,
    )

    @classmethod
    async def sync_resource(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        spec = cls.normalize_resource_spec(data)

        return await cls.repository_class.sync_resources(
            resources=[
                spec,
            ],
            operator_id=cls.get_operator_id(operator),
        )

    @classmethod
    async def batch_sync_resources(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        request_data = cls.ensure_dict(data)
        resources = cls.normalize_list(
            value=request_data.get("resources"),
            field="resources",
        )

        return await cls.repository_class.sync_resources(
            resources=[
                cls.normalize_resource_spec(item)
                for item in resources
            ],
            operator_id=cls.get_operator_id(operator),
        )

    @classmethod
    async def sync_permission(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        spec = cls.normalize_permission_spec(data)

        return await cls.repository_class.sync_permissions(
            permissions=[
                spec,
            ],
            operator_id=cls.get_operator_id(operator),
        )

    @classmethod
    async def batch_sync_permissions(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        request_data = cls.ensure_dict(data)
        permissions = cls.normalize_list(
            value=request_data.get("permissions"),
            field="permissions",
        )

        return await cls.repository_class.sync_permissions(
            permissions=[
                cls.normalize_permission_spec(item)
                for item in permissions
            ],
            operator_id=cls.get_operator_id(operator),
        )

    @classmethod
    def normalize_resource_spec(cls, value: Any) -> dict[str, Any]:
        payload = cls.ensure_dict(value)
        cls.ensure_allowed_fields(
            payload=payload,
            allowed_fields={
                "resource_type",
                "resource_name",
                "module_code",
                "access_mode",
                "status",
                "actions",
            },
        )

        resource_type = ResourceValidator.normalize_resource_key(
            value=payload.get("resource_type"),
            field="resource_type",
        )
        if not resource_type:
            raise IamManagementRequestInvalidError(
                "resource_type is required.",
                details={
                    "field": "resource_type",
                },
            )

        resource_name = cls.normalize_required_text(
            value=payload.get("resource_name"),
            field="resource_name",
            max_length=128,
        )

        raw_module_code = payload.get("module_code")
        if raw_module_code in (None, ""):
            module_code = ResourceValidator.resolve_default_module_code(resource_type)
        else:
            module_code = ResourceValidator.normalize_resource_key(
                value=raw_module_code,
                field="module_code",
            )

        if not module_code:
            raise IamManagementRequestInvalidError(
                "module_code is required.",
                details={
                    "field": "module_code",
                },
            )

        if len(module_code) > 64:
            raise IamManagementRequestInvalidError(
                "module_code length exceeds limit.",
                details={
                    "field": "module_code",
                    "max_length": 64,
                },
            )

        access_mode = cls.normalize_access_mode(payload.get("access_mode"))
        status = cls.normalize_status(payload.get("status"))

        raw_actions = payload.get("actions", [])
        if raw_actions in (None, ""):
            raw_actions = []

        if not isinstance(raw_actions, list):
            raise IamManagementRequestInvalidError(
                "actions must be a list.",
                details={
                    "field": "actions",
                },
            )

        if len(raw_actions) > cls.max_batch_size:
            raise IamManagementRequestInvalidError(
                "actions exceeds max batch size.",
                details={
                    "field": "actions",
                    "max_batch_size": cls.max_batch_size,
                },
            )

        return {
            "resource_type": resource_type,
            "resource_name": resource_name,
            "module_code": module_code,
            "access_mode": access_mode,
            "status": status,
            "actions": [
                cls.normalize_resource_action_spec(item)
                for item in raw_actions
            ],
        }

    @classmethod
    def normalize_resource_action_spec(cls, value: Any) -> dict[str, Any]:
        payload = cls.ensure_dict(value)
        cls.ensure_allowed_fields(
            payload=payload,
            allowed_fields={
                "action_code",
                "action_name",
                "status",
            },
        )

        action_code = ResourceActionValidator.normalize_field_value(
            field="action_code",
            value=payload.get("action_code"),
        )
        action_name = cls.normalize_required_text(
            value=payload.get("action_name"),
            field="action_name",
            max_length=128,
        )
        status = cls.normalize_status(payload.get("status"))

        return {
            "action_code": action_code,
            "action_name": action_name,
            "status": status,
        }

    @classmethod
    def normalize_permission_spec(cls, value: Any) -> dict[str, Any]:
        payload = cls.ensure_dict(value)
        cls.ensure_allowed_fields(
            payload=payload,
            allowed_fields={
                "permission_code",
                "permission_name",
                "permission_type",
                "parent_code",
                "parent_id",
                "status",
            },
        )

        permission_code = cls.normalize_permission_code(
            value=payload.get("permission_code"),
            field="permission_code",
        )
        permission_name = cls.normalize_required_text(
            value=payload.get("permission_name"),
            field="permission_name",
            max_length=128,
        )
        permission_type = cls.normalize_permission_type(
            payload.get("permission_type", PERMISSION_TYPE_ACTION)
        )
        status = cls.normalize_status(payload.get("status"))

        parent_code = None
        if payload.get("parent_code") not in (None, ""):
            parent_code = cls.normalize_permission_code(
                value=payload.get("parent_code"),
                field="parent_code",
            )

        parent_id = None
        if payload.get("parent_id") not in (None, ""):
            parent_id = cls.normalize_positive_int(
                value=payload.get("parent_id"),
                field="parent_id",
            )

        if parent_code and parent_id:
            raise IamManagementRequestInvalidError(
                "parent_code and parent_id cannot be used at the same time.",
                details={
                    "fields": [
                        "parent_code",
                        "parent_id",
                    ],
                },
            )

        if parent_code == permission_code:
            raise IamManagementRequestInvalidError(
                "Permission cannot use itself as parent.",
                details={
                    "permission_code": permission_code,
                    "parent_code": parent_code,
                },
            )

        return {
            "permission_code": permission_code,
            "permission_name": permission_name,
            "permission_type": permission_type,
            "parent_code": parent_code,
            "parent_id": parent_id,
            "status": status,
        }

    @staticmethod
    def ensure_dict(value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise IamManagementRequestInvalidError("Request payload must be an object.")
        return dict(value)

    @classmethod
    def normalize_list(cls, *, value: Any, field: str) -> list[Any]:
        if not isinstance(value, list):
            raise IamManagementRequestInvalidError(
                f"{field} must be a list.",
                details={
                    "field": field,
                },
            )

        if not value:
            raise IamManagementRequestInvalidError(
                f"{field} cannot be empty.",
                details={
                    "field": field,
                },
            )

        if len(value) > cls.max_batch_size:
            raise IamManagementRequestInvalidError(
                f"{field} exceeds max batch size.",
                details={
                    "field": field,
                    "max_batch_size": cls.max_batch_size,
                },
            )

        return value

    @staticmethod
    def ensure_allowed_fields(*, payload: dict[str, Any], allowed_fields: set[str]) -> None:
        unknown_fields = sorted(
            field
            for field in payload
            if field not in allowed_fields
        )
        if not unknown_fields:
            return

        raise IamManagementRequestInvalidError(
            "Request contains unsupported fields.",
            details={
                "fields": unknown_fields,
                "allowed_fields": sorted(allowed_fields),
            },
        )

    @staticmethod
    def normalize_required_text(*, value: Any, field: str, max_length: int) -> str:
        text = str(value or "").strip()
        if not text:
            raise IamManagementRequestInvalidError(
                f"{field} is required.",
                details={
                    "field": field,
                },
            )

        if len(text) > max_length:
            raise IamManagementRequestInvalidError(
                f"{field} length exceeds limit.",
                details={
                    "field": field,
                    "max_length": max_length,
                },
            )

        return text

    @classmethod
    def normalize_access_mode(cls, value: Any) -> str:
        access_mode = str(value or RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW).strip().upper()
        if access_mode not in cls.access_modes:
            raise IamManagementRequestInvalidError(
                "access_mode is invalid.",
                details={
                    "access_mode": access_mode,
                    "allowed_values": list(cls.access_modes),
                },
            )
        return access_mode

    @staticmethod
    def normalize_status(value: Any) -> int:
        if value in (None, ""):
            return 1

        try:
            status = int(value)
        except (TypeError, ValueError) as exc:
            raise IamManagementRequestInvalidError(
                "status is invalid.",
                details={
                    "status": value,
                },
            ) from exc

        if status not in (0, 1):
            raise IamManagementRequestInvalidError(
                "status must be 0 or 1.",
                details={
                    "status": status,
                },
            )

        return status

    @classmethod
    def normalize_permission_type(cls, value: Any) -> str:
        permission_type = str(value or PERMISSION_TYPE_ACTION).strip().upper()
        if permission_type not in cls.permission_types:
            raise IamManagementRequestInvalidError(
                "permission_type is invalid.",
                details={
                    "permission_type": permission_type,
                    "allowed_values": list(cls.permission_types),
                },
            )
        return permission_type

    @staticmethod
    def normalize_permission_code(*, value: Any, field: str) -> str:
        permission_code = str(value or "").strip().lower()
        if not permission_code:
            raise IamManagementRequestInvalidError(
                f"{field} is required.",
                details={
                    "field": field,
                },
            )

        if " " in permission_code:
            raise IamManagementRequestInvalidError(
                f"{field} cannot contain spaces.",
                details={
                    "field": field,
                    "value": permission_code,
                },
            )

        if len(permission_code) > 128:
            raise IamManagementRequestInvalidError(
                f"{field} length exceeds limit.",
                details={
                    "field": field,
                    "max_length": 128,
                },
            )

        return permission_code

    @staticmethod
    def normalize_positive_int(*, value: Any, field: str) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError) as exc:
            raise IamManagementRequestInvalidError(
                f"{field} is invalid.",
                details={
                    "field": field,
                    "value": value,
                },
            ) from exc

        if parsed <= 0:
            raise IamManagementRequestInvalidError(
                f"{field} must be positive.",
                details={
                    "field": field,
                    "value": parsed,
                },
            )

        return parsed

    @staticmethod
    def get_operator_id(operator: Any) -> int | None:
        operator_id = getattr(operator, "id", None)

        if isinstance(operator_id, int):
            return operator_id

        try:
            parsed = int(operator_id)
        except (TypeError, ValueError):
            return None

        return parsed if parsed > 0 else None
