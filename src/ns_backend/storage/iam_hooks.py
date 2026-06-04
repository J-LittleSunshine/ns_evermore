# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_backend.iam.constants import RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW

if TYPE_CHECKING:
    pass

_STORAGE_RESOURCE_SPECS: tuple[dict[str, Any], ...] = (
    {
        "resource_type": "storage.object",
        "resource_name": "Storage Object",
        "module_code": "storage",
        "access_mode": RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW,
        "status": 1,
        "actions": (
            {
                "action_code": "upload",
                "action_name": "Upload storage object",
            },
            {
                "action_code": "presigned_get",
                "action_name": "Create storage object presigned GET URL",
            },
        ),
    },
    {
        "resource_type": "storage.object_ref",
        "resource_name": "Storage Object Reference",
        "module_code": "storage",
        "access_mode": RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW,
        "status": 1,
        "actions": (
            {
                "action_code": "list",
                "action_name": "List storage object references",
            },
            {
                "action_code": "detail",
                "action_name": "Get storage object reference detail",
            },
            {
                "action_code": "delete",
                "action_name": "Delete storage object reference",
            },
        ),
    },
)


async def register_storage_iam_resources(*, operator_id: int | None = None, resource_registry, policy_service=None) -> dict[str, Any]:
    """Register storage IAM resources and actions.

    This hook is executed by IAM permission sync module hook service.
    """
    _ = policy_service

    registered_resources: int = 0
    registered_actions: int = 0

    for resource_spec in _STORAGE_RESOURCE_SPECS:
        await resource_registry.register_resource(
            data={
                "resource_type": resource_spec["resource_type"],
                "resource_name": resource_spec["resource_name"],
                "module_code": resource_spec["module_code"],
                "access_mode": resource_spec["access_mode"],
                "status": resource_spec["status"],
            },
            operator_id=operator_id,
        )
        registered_resources += 1

        for action_spec in resource_spec["actions"]:
            await resource_registry.register_resource_action(
                data={
                    "resource_type": resource_spec["resource_type"],
                    "action_code": action_spec["action_code"],
                    "action_name": action_spec["action_name"],
                    "status": 1,
                },
                operator_id=operator_id,
            )
            registered_actions += 1

    return {
        "ok": True,
        "module_code": "storage",
        "registered_resources": registered_resources,
        "registered_actions": registered_actions,
    }
