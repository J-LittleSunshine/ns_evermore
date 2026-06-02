# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.constants import RECOMMENDED_ACTION_CODES
from ns_backend.iam.models import IamResourceRelation
from ns_backend.iam.repositories import ResourceRelationRepository, ResourceRepository
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class ResourceRegistryService:
    """Service for IAM resource/action registration APIs."""

    ACTION_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
    RECOMMENDED_ACTION_CODE_SET: set[str] = set(RECOMMENDED_ACTION_CODES)

    @staticmethod
    def _ensure_request_data(data: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise BusinessError("request data must be an object", NsErrorCode.INVALID_VALUE)
        return data

    @staticmethod
    def _normalize_required_text(value: Any, field_name: str) -> str:
        text_value: str = str(value or "").strip()
        if not text_value:
            raise BusinessError(f"{field_name} is required", NsErrorCode.INVALID_VALUE)
        return text_value

    @staticmethod
    def _normalize_status(value: Any) -> int:
        if value in (None, ""):
            return 1

        try:
            status: int = int(value)
        except (TypeError, ValueError) as exc:
            raise BusinessError("status is invalid", NsErrorCode.INVALID_VALUE) from exc

        if status not in (0, 1):
            raise BusinessError("status is invalid", NsErrorCode.INVALID_VALUE)

        return status

    @classmethod
    def _normalize_resource_type(cls, value: Any) -> str:
        resource_type: str = cls._normalize_required_text(value, "resource_type").lower()
        if " " in resource_type:
            raise BusinessError("resource_type is invalid", NsErrorCode.INVALID_VALUE)
        return resource_type

    @classmethod
    def _normalize_module_code(cls, *, value: Any, resource_type: str) -> str:
        raw_module: str = str(value or "").strip().lower()
        if raw_module:
            if " " in raw_module:
                raise BusinessError("module_code is invalid", NsErrorCode.INVALID_VALUE)
            return raw_module

        if "." in resource_type:
            return resource_type.split(".", 1)[0]

        if ":" in resource_type:
            return resource_type.split(":", 1)[0]

        return resource_type

    @classmethod
    def _normalize_action_code(cls, value: Any) -> str:
        action_code: str = cls._normalize_required_text(value, "action_code").lower()
        if cls.ACTION_CODE_PATTERN.fullmatch(action_code) is None:
            raise BusinessError(f"Invalid action code: {action_code}", NsErrorCode.PERMISSION_ACTION_INVALID)
        return action_code

    @classmethod
    def _normalize_relation_type(cls, value: Any) -> str:
        relation_type = str(value or IamResourceRelation.RELATION_PARENT).strip().upper()
        if relation_type != IamResourceRelation.RELATION_PARENT:
            raise BusinessError("relation_type is invalid", NsErrorCode.INVALID_VALUE)
        return relation_type

    @classmethod
    async def register_resource(cls, *, data: dict[str, Any], operator_id: int | None) -> dict[str, Any]:
        """Register or update one resource type."""
        request_data: dict[str, Any] = cls._ensure_request_data(data)
        resource_type: str = cls._normalize_resource_type(request_data.get("resource_type"))
        resource_name: str = cls._normalize_required_text(request_data.get("resource_name"), "resource_name")
        module_code: str = cls._normalize_module_code(value=request_data.get("module_code"), resource_type=resource_type)
        status: int = cls._normalize_status(request_data.get("status"))

        existing = await ResourceRepository.get_resource_by_type(resource_type)
        if existing is None:
            return await ResourceRepository.create_resource(
                resource_type=resource_type,
                resource_name=resource_name,
                module_code=module_code,
                status=status,
                operator_id=operator_id,
            )

        has_changes: bool = any(
            (
                existing.resource_name != resource_name,
                existing.module_code != module_code,
                existing.status != status,
            )
        )
        if has_changes:
            await ResourceRepository.update_resource(
                item=existing,
                resource_name=resource_name,
                module_code=module_code,
                status=status,
                operator_id=operator_id,
            )

        return {"id": existing.id}

    @classmethod
    async def register_resource_action(cls, *, data: dict[str, Any], operator_id: int | None) -> dict[str, Any]:
        """Register or update one action under one resource type."""
        request_data: dict[str, Any] = cls._ensure_request_data(data)
        resource_type: str = cls._normalize_resource_type(request_data.get("resource_type"))
        action_code: str = cls._normalize_action_code(request_data.get("action_code"))
        action_name: str = cls._normalize_required_text(request_data.get("action_name"), "action_name")
        status: int = cls._normalize_status(request_data.get("status"))

        resource = await ResourceRepository.get_resource_by_type(resource_type)
        if resource is None:
            raise BusinessError("resource_type does not exist", NsErrorCode.DATA_NOT_FOUND)

        existing = await ResourceRepository.get_resource_action(resource_id=resource.id, action_code=action_code)
        if existing is None:
            return await ResourceRepository.create_resource_action(
                resource_id=resource.id,
                action_code=action_code,
                action_name=action_name,
                status=status,
                operator_id=operator_id,
            )

        has_changes: bool = any((existing.action_name != action_name, existing.status != status))
        if has_changes:
            await ResourceRepository.update_resource_action(
                item=existing,
                action_name=action_name,
                status=status,
                operator_id=operator_id,
            )

        return {"id": existing.id}

    @classmethod
    async def register_resource_relation(cls, *, data: dict[str, Any], operator_id: int | None) -> dict[str, Any]:
        """Register one parent-child relation for resource inheritance."""
        request_data: dict[str, Any] = cls._ensure_request_data(data)
        resource_type: str = cls._normalize_resource_type(request_data.get("resource_type"))
        resource_id: str = cls._normalize_required_text(request_data.get("resource_id"), "resource_id")
        parent_resource_type: str = cls._normalize_resource_type(request_data.get("parent_resource_type"))
        parent_resource_id: str = cls._normalize_required_text(request_data.get("parent_resource_id"), "parent_resource_id")
        relation_type: str = cls._normalize_relation_type(request_data.get("relation_type"))

        if resource_type == parent_resource_type and resource_id == parent_resource_id:
            raise BusinessError("resource cannot inherit from itself", NsErrorCode.INVALID_VALUE)

        resource = await ResourceRepository.get_resource_by_type(resource_type)
        if resource is None:
            raise BusinessError("resource_type does not exist", NsErrorCode.DATA_NOT_FOUND)

        parent_resource = await ResourceRepository.get_resource_by_type(parent_resource_type)
        if parent_resource is None:
            raise BusinessError("parent_resource_type does not exist", NsErrorCode.DATA_NOT_FOUND)

        return await ResourceRelationRepository.upsert_parent_relation(
            resource_type=resource_type,
            resource_id=resource_id,
            parent_resource_type=parent_resource_type,
            parent_resource_id=parent_resource_id,
            relation_type=relation_type,
            operator_id=operator_id,
        )

    @classmethod
    async def list_resources(cls, *, data: dict[str, Any]) -> dict[str, Any]:
        """List resource registrations with action rows."""
        request_data: dict[str, Any] = cls._ensure_request_data(data)
        page: int | str | None = request_data.get("page", 1)
        page_size: int | str | None = request_data.get("page_size", 20)

        filters: dict[str, Any] = {}
        raw_filters: Any = request_data.get("filters")
        if isinstance(raw_filters, dict):
            filters.update(raw_filters)

        if request_data.get("resource_type") not in (None, ""):
            filters["resource_type"] = cls._normalize_resource_type(request_data.get("resource_type"))

        if request_data.get("module_code") not in (None, ""):
            filters["module_code"] = cls._normalize_required_text(request_data.get("module_code"), "module_code").lower()

        if request_data.get("status") not in (None, ""):
            filters["status"] = cls._normalize_status(request_data.get("status"))

        list_result: dict[str, Any] = await ResourceRepository.list_resources(page=page, page_size=page_size, filters=filters or None)
        items: list[dict[str, Any]] = list_result.get("items", [])
        resource_ids: list[int] = [int(item["id"]) for item in items]
        action_rows: list[dict[str, Any]] = await ResourceRepository.list_actions_by_resource_ids(resource_ids)

        action_group: dict[int, list[dict[str, Any]]] = {}
        for action_item in action_rows:
            resource_id: int = int(action_item["resource_id"])
            action_group.setdefault(resource_id, []).append(
                {
                    "id": action_item["id"],
                    "action_code": action_item["action_code"],
                    "action_name": action_item["action_name"],
                    "status": action_item["status"],
                }
            )

        for item in items:
            item["actions"] = action_group.get(int(item["id"]), [])
            item["recommended_actions"] = sorted(cls.RECOMMENDED_ACTION_CODE_SET)

        return list_result

