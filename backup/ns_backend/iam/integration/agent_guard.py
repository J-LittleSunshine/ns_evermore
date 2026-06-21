# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
from typing import Any, TYPE_CHECKING

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.schemas import PermissionSpec
from ns_backend.iam.services.authorization_context import AuthorizationContextService
from ns_backend.iam.services.authorize import AuthorizeService
from ns_backend.iam.services.permission_sync import PermissionSyncService
from ns_backend.iam.services.resource_registry import ResourceRegistryService
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class AgentToolAuthorizationGuard:
    """Enforce IAM authorization before agent tool execution."""

    DEFAULT_RESOURCE_TYPE = "agent.tool"
    DEFAULT_ACTION_CODE = "execute"
    DEFAULT_MODULE_CODE = "agent"
    DEFAULT_PERMISSION_CODE = "agent:tool:execute"

    TOOL_ACTION_MAP: dict[str, dict[str, str | None]] = {}
    _PROVISIONED_KEYS: set[str] = set()
    _PROVISION_LOCK = asyncio.Lock()

    @staticmethod
    def _normalize_required_text(value: Any, field_name: str) -> str:
        """Normalize one required text field."""
        normalized_value = str(value or "").strip()
        if not normalized_value:
            raise BusinessError(f"{field_name} is required", NsErrorCode.INVALID_VALUE)
        return normalized_value

    @classmethod
    def _normalize_optional_permission_code(cls, value: Any) -> str | None:
        """Normalize optional permission code value."""
        if value in (
                None,
                ""
        ):
            return None
        return str(value).strip().lower()

    @classmethod
    def _normalize_resource_id(cls, resource_id: Any) -> str:
        """Normalize and validate one tool resource identifier."""
        return cls._normalize_required_text(resource_id, "resource_id")

    @classmethod
    def _normalize_tool_mapping(cls, *, tool_name: str, tool_mapping: dict[str, Any]) -> dict[str, str | None]:
        """Normalize one registered tool-action mapping object."""
        resource_type = str(tool_mapping.get("resource_type") or "").strip().lower()
        action_code = str(tool_mapping.get("action_code") or "").strip().lower()
        if not resource_type or not action_code:
            raise BusinessError(
                f"Tool mapping is invalid: {tool_name}",
                NsErrorCode.PERMISSION_DENIED,
                data={
                    "tool_name": tool_name
                },
            )

        return {
            "resource_type": resource_type,
            "action_code": action_code,
            "permission_code": cls._normalize_optional_permission_code(tool_mapping.get("permission_code")),
        }

    @classmethod
    def register_tool_action(
            cls,
            *,
            tool_name: str,
            resource_type: str,
            action_code: str,
            permission_code: str | None = None,
    ) -> dict[str, str | None]:
        """Register one tool-to-action mapping for IAM authorization checks."""
        normalized_tool_name = cls._normalize_required_text(tool_name, "tool_name")
        normalized_resource_type = cls._normalize_required_text(resource_type, "resource_type").lower()
        normalized_action_code = cls._normalize_required_text(action_code, "action_code").lower()

        mapping = {
            "resource_type": normalized_resource_type,
            "action_code": normalized_action_code,
            "permission_code": cls._normalize_optional_permission_code(permission_code) or cls.DEFAULT_PERMISSION_CODE,
        }
        cls.TOOL_ACTION_MAP[normalized_tool_name] = mapping
        return mapping

    @classmethod
    async def _provision_mapping_if_needed(cls, *, tool_name: str, mapping: dict[str, str | None]) -> None:
        """Persist tool IAM mapping to resource/action/permission registries once."""
        resource_type = str(mapping.get("resource_type") or "").strip().lower()
        action_code = str(mapping.get("action_code") or "").strip().lower()
        permission_code = cls._normalize_optional_permission_code(mapping.get("permission_code")) or cls.DEFAULT_PERMISSION_CODE
        provision_key = f"{resource_type}:{action_code}:{permission_code}"

        if provision_key in cls._PROVISIONED_KEYS:
            return

        async with cls._PROVISION_LOCK:
            if provision_key in cls._PROVISIONED_KEYS:
                return

            await ResourceRegistryService.register_resource(
                data={
                    "resource_type": resource_type,
                    "resource_name": resource_type,
                    "module_code": cls.DEFAULT_MODULE_CODE,
                    "status": 1,
                },
                operator_id=None,
            )
            await ResourceRegistryService.register_resource_action(
                data={
                    "resource_type": resource_type,
                    "action_code": action_code,
                    "action_name": action_code,
                    "status": 1,
                },
                operator_id=None,
            )
            await PermissionSyncService.sync_specs(
                [
                    PermissionSpec(
                        code=permission_code,
                        name=f"Agent tool action {tool_name}",
                        permission_type="ACTION",
                    )
                ],
                operator_id=None,
            )

            cls._PROVISIONED_KEYS.add(provision_key)

    @classmethod
    async def get_tool_mapping(cls, tool_name: str) -> dict[str, str | None]:
        """Resolve one normalized tool authorization mapping."""
        normalized_tool_name = cls._normalize_required_text(tool_name, "tool_name")

        tool_mapping = cls.TOOL_ACTION_MAP.get(normalized_tool_name)
        if not isinstance(tool_mapping, dict):
            tool_mapping = cls.register_tool_action(
                tool_name=normalized_tool_name,
                resource_type=cls.DEFAULT_RESOURCE_TYPE,
                action_code=cls.DEFAULT_ACTION_CODE,
                permission_code=cls.DEFAULT_PERMISSION_CODE,
            )

        normalized_mapping = cls._normalize_tool_mapping(tool_name=normalized_tool_name, tool_mapping=tool_mapping)
        await cls._provision_mapping_if_needed(tool_name=normalized_tool_name, mapping=normalized_mapping)
        return normalized_mapping

    @classmethod
    async def ensure_tool_allowed(
            cls,
            *,
            user: Any,
            tool_name: str,
            resource_id: str,
            context: dict[str, Any] | None = None,
            trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Authorize one tool execution and raise when the decision is denied."""
        tool_mapping = await cls.get_tool_mapping(tool_name)
        normalized_resource_id = cls._normalize_resource_id(resource_id)

        # Fast deny path from cached authorization context.
        try:
            auth_context = await AuthorizationContextService.get_or_build(
                user=user,
                resource_type=tool_mapping.get("resource_type") or cls.DEFAULT_RESOURCE_TYPE,
                action_code=tool_mapping.get("action_code") or cls.DEFAULT_ACTION_CODE,
                permission_code=tool_mapping.get("permission_code"),
            )
            context_filters = dict(getattr(auth_context, "readable_resource_filters", {}) or {})
            orm_filters = context_filters.get("orm") if isinstance(context_filters.get("orm"), dict) else {}
            orm_include = orm_filters.get("include") if isinstance(orm_filters.get("include"), dict) else {}
            orm_exclude = orm_filters.get("exclude") if isinstance(orm_filters.get("exclude"), dict) else {}
            denied_ids = {str(item) for item in orm_exclude.get("resource_id__in", [])}
            allowed_ids = {str(item) for item in getattr(auth_context, "readable_resource_ids", [])}
            default_allow = bool(context_filters.get("default_allow", False))
            deny_all = bool(context_filters.get("deny_all", False))

            if not allowed_ids:
                allowed_ids = {str(item) for item in orm_include.get("resource_id__in", [])}

            if normalized_resource_id in denied_ids:
                raise BusinessError(
                    f"Tool execution denied: {tool_name}",
                    NsErrorCode.PERMISSION_DENIED,
                    data={
                        "tool_name": tool_name,
                        "decision": {
                            "allowed": False,
                            "effect": "deny",
                            "reason": "ACL_DENY",
                            "matched_source": "cache",
                        },
                    },
                )

            if deny_all and normalized_resource_id not in allowed_ids:
                raise BusinessError(
                    f"Tool execution denied: {tool_name}",
                    NsErrorCode.PERMISSION_DENIED,
                    data={
                        "tool_name": tool_name,
                        "decision": {
                            "allowed": False,
                            "effect": "deny",
                            "reason": "RETRIEVAL_FILTER_DENY",
                            "matched_source": "cache",
                        },
                    },
                )

            if allowed_ids and not default_allow and normalized_resource_id not in allowed_ids:
                raise BusinessError(
                    f"Tool execution denied: {tool_name}",
                    NsErrorCode.PERMISSION_DENIED,
                    data={
                        "tool_name": tool_name,
                        "decision": {
                            "allowed": False,
                            "effect": "deny",
                            "reason": "ACL_NOT_GRANTED",
                            "matched_source": "cache",
                        },
                    },
                )
        except BusinessError:
            raise
        except Exception:
            # Cache faults should not block online authorization fallback.
            pass

        decision = await AuthorizeService.check(
            user=user,
            data={
                "resource_type": tool_mapping.get("resource_type") or "agent.tool",
                "resource_id": normalized_resource_id,
                "action_code": tool_mapping.get("action_code") or "execute",
                "permission_code": tool_mapping.get("permission_code"),
                "context": {} if context is None else context,
            },
            trace_id=trace_id,
        )

        if not bool(decision.get("allowed", False)):
            raise BusinessError(
                f"Tool execution denied: {tool_name}",
                NsErrorCode.PERMISSION_DENIED,
                data={
                    "tool_name": tool_name,
                    "decision": decision,
                },
            )

        return decision
