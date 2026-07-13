# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from typing import (
    Any,
    TYPE_CHECKING,
)

from ns_backend.iam.constants import (
    PERMISSION_TYPE_ACTION,
    RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW,
)
from ns_backend.iam.errors import (
    IamRuntimeAccessDeniedError,
    IamRuntimeRequestInvalidError,
)
from ns_backend.iam.services.access_decision import AccessDecisionService
from ns_backend.iam.services.sync import IamSyncService

if TYPE_CHECKING:
    pass


class AgentToolAuthorizationGuard:
    DEFAULT_RESOURCE_TYPE = "agent.tool"
    DEFAULT_ACTION_CODE = "execute"
    DEFAULT_MODULE_CODE = "agent"
    DEFAULT_PERMISSION_CODE = "agent:tool:execute"

    TOOL_ACTION_MAP: dict[str, dict[str, str | None]] = {}
    _PROVISIONED_KEYS: set[str] = set()
    _PROVISION_LOCK = asyncio.Lock()

    @staticmethod
    def normalize_required_text(value: Any, field_name: str) -> str:
        normalized_value = str(value or "").strip()
        if not normalized_value:
            details = {
                "field": field_name,
            }
            raise IamRuntimeRequestInvalidError(f"{field_name} is required.", details=details)

        return normalized_value

    @staticmethod
    def normalize_optional_text(value: Any) -> str | None:
        if value in (None, ""):
            return None

        normalized_value = str(value).strip()
        return normalized_value or None

    @classmethod
    def normalize_optional_permission_code(cls, value: Any) -> str | None:
        normalized_value = cls.normalize_optional_text(value)
        return normalized_value.lower() if normalized_value else None

    @classmethod
    def normalize_resource_id(cls, resource_id: Any) -> str:
        return cls.normalize_required_text(resource_id, "resource_id")

    @classmethod
    def register_tool_action(cls, *, tool_name: str, resource_type: str, action_code: str, permission_code: str | None = None) -> dict[str, str | None]:
        normalized_tool_name = cls.normalize_required_text(tool_name, "tool_name")
        normalized_resource_type = cls.normalize_required_text(resource_type, "resource_type").lower()
        normalized_action_code = cls.normalize_required_text(action_code, "action_code").lower()

        mapping = {
            "resource_type": normalized_resource_type,
            "action_code": normalized_action_code,
            "permission_code": cls.normalize_optional_permission_code(permission_code) or cls.DEFAULT_PERMISSION_CODE,
        }

        cls.TOOL_ACTION_MAP[normalized_tool_name] = mapping
        return mapping

    @classmethod
    def normalize_tool_mapping(cls, *, tool_name: str, tool_mapping: dict[str, Any]) -> dict[str, str | None]:
        resource_type = cls.normalize_required_text(tool_mapping.get("resource_type"), "resource_type", ).lower()
        action_code = cls.normalize_required_text(tool_mapping.get("action_code"), "action_code").lower()

        return {
            "resource_type": resource_type,
            "action_code": action_code,
            "permission_code": cls.normalize_optional_permission_code(tool_mapping.get("permission_code")) or cls.DEFAULT_PERMISSION_CODE,
        }

    @classmethod
    async def provision_mapping_if_needed(cls, *, tool_name: str, mapping: dict[str, str | None]) -> None:
        resource_type = cls.normalize_required_text(mapping.get("resource_type"), "resource_type").lower()
        action_code = cls.normalize_required_text(mapping.get("action_code"), "action_code").lower()
        permission_code = cls.normalize_optional_permission_code(mapping.get("permission_code")) or cls.DEFAULT_PERMISSION_CODE

        provision_key = f"{resource_type}:{action_code}:{permission_code}"

        if provision_key in cls._PROVISIONED_KEYS:
            return

        async with cls._PROVISION_LOCK:
            if provision_key in cls._PROVISIONED_KEYS:
                return
            sync_resources_data = {
                "resources": [
                    {
                        "resource_type": resource_type,
                        "resource_name": resource_type,
                        "module_code": cls.DEFAULT_MODULE_CODE,
                        "access_mode": RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW,
                        "status": 1,
                        "actions": [
                            {
                                "action_code": action_code,
                                "action_name": action_code,
                                "status": 1,
                            }
                        ],
                    }
                ],
            }

            sync_permission_data = {
                "permission_code": permission_code,
                "permission_name": f"Agent tool action {tool_name}",
                "permission_type": PERMISSION_TYPE_ACTION,
                "status": 1,
            }
            await IamSyncService.batch_sync_resources(data=sync_resources_data, operator=None)

            await IamSyncService.sync_permission(data=sync_permission_data, operator=None)

            cls._PROVISIONED_KEYS.add(provision_key)

    @classmethod
    async def get_tool_mapping(cls, tool_name: str) -> dict[str, str | None]:
        normalized_tool_name = cls.normalize_required_text(tool_name, "tool_name")

        tool_mapping = cls.TOOL_ACTION_MAP.get(normalized_tool_name)
        if not isinstance(tool_mapping, dict):
            tool_mapping = cls.register_tool_action(tool_name=normalized_tool_name, resource_type=cls.DEFAULT_RESOURCE_TYPE, action_code=cls.DEFAULT_ACTION_CODE, permission_code=cls.DEFAULT_PERMISSION_CODE)

        normalized_mapping = cls.normalize_tool_mapping(tool_name=normalized_tool_name, tool_mapping=tool_mapping)

        await cls.provision_mapping_if_needed(tool_name=normalized_tool_name, mapping=normalized_mapping)

        return normalized_mapping

    @classmethod
    async def ensure_tool_allowed(cls, *, user: Any, tool_name: str, resource_id: str, context: dict[str, Any] | None = None, trace_id: str | None = None) -> dict[str, Any]:
        tool_mapping = await cls.get_tool_mapping(tool_name)
        normalized_resource_id = cls.normalize_resource_id(resource_id)

        check_with_audit_data = {
            "resource_type": tool_mapping.get("resource_type") or cls.DEFAULT_RESOURCE_TYPE,
            "resource_id": normalized_resource_id,
            "action_code": tool_mapping.get("action_code") or cls.DEFAULT_ACTION_CODE,
            "permission_code": tool_mapping.get("permission_code") or cls.DEFAULT_PERMISSION_CODE,
            "context": cls.normalize_context(context),
        }
        decision = await AccessDecisionService.check_with_audit(user=user, data=check_with_audit_data, trace_id=trace_id)

        if not bool(decision.get("allowed", False)):
            details = {
                "tool_name": tool_name,
                "decision": decision,
            }
            raise IamRuntimeAccessDeniedError("Tool execution denied.", details=details)

        return decision

    @staticmethod
    def normalize_context(context: Any) -> dict[str, Any]:
        if context is None:
            return {}

        if not isinstance(context, dict):
            details = {
                "field": "context",
                "actual_type": type(context).__name__,
            }
            raise IamRuntimeRequestInvalidError("context must be an object.", details=details)

        return dict(context)
