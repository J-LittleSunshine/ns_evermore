# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.services.authorize import AuthorizeService
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class AgentToolAuthorizationGuard:
    """Enforce IAM authorization before agent tool execution."""

    TOOL_ACTION_MAP: dict[str, dict[str, str | None]] = {
        # tool_name: {resource_type, action_code, permission_code}
        "knowledge.search": {
            "resource_type": "agent.tool",
            "action_code": "execute",
            "permission_code": "agent:tool:execute",
        },
    }

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
        if value in (None, ""):
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
                data={"tool_name": tool_name},
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
    ) -> None:
        """Register one tool-to-action mapping for IAM authorization checks."""
        normalized_tool_name = cls._normalize_required_text(tool_name, "tool_name")
        normalized_resource_type = cls._normalize_required_text(resource_type, "resource_type").lower()
        normalized_action_code = cls._normalize_required_text(action_code, "action_code").lower()

        cls.TOOL_ACTION_MAP[normalized_tool_name] = {
            "resource_type": normalized_resource_type,
            "action_code": normalized_action_code,
            "permission_code": cls._normalize_optional_permission_code(permission_code),
        }

    @classmethod
    def get_tool_mapping(cls, tool_name: str) -> dict[str, str | None]:
        """Resolve one normalized tool authorization mapping."""
        normalized_tool_name = cls._normalize_required_text(tool_name, "tool_name")

        tool_mapping = cls.TOOL_ACTION_MAP.get(normalized_tool_name)
        if not isinstance(tool_mapping, dict):
            raise BusinessError(
                f"Tool mapping not configured: {normalized_tool_name}",
                NsErrorCode.PERMISSION_DENIED,
                data={"tool_name": normalized_tool_name},
            )

        return cls._normalize_tool_mapping(tool_name=normalized_tool_name, tool_mapping=tool_mapping)

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
        tool_mapping = cls.get_tool_mapping(tool_name)
        normalized_resource_id = cls._normalize_resource_id(resource_id)

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

