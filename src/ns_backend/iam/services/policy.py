# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.constants import to_storage_data_scope
from ns_backend.iam.repositories import PolicyRepository, ResourceRepository
from ns_backend.iam.services.authorization_context import AuthorizationContextService
from ns_backend.iam.services.resource_acl import ResourceAclService
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class PolicyService:
    """Service for policy and policy-rule management APIs."""

    EFFECT_ALLOW = "ALLOW"
    EFFECT_DENY = "DENY"
    ACTION_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")

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
    def _normalize_positive_int(value: Any, field_name: str) -> int:
        try:
            normalized_value = int(value)
        except (TypeError, ValueError) as exc:
            raise BusinessError(f"{field_name} is invalid", NsErrorCode.INVALID_VALUE) from exc

        if normalized_value <= 0:
            raise BusinessError(f"{field_name} is invalid", NsErrorCode.INVALID_VALUE)

        return normalized_value

    @staticmethod
    def _normalize_optional_positive_int(value: Any, field_name: str) -> int | None:
        if value in (None, ""):
            return None
        return PolicyService._normalize_positive_int(value, field_name)

    @staticmethod
    def _normalize_status(value: Any, *, default: int = 1) -> int:
        if value in (None, ""):
            return default

        try:
            status = int(value)
        except (TypeError, ValueError) as exc:
            raise BusinessError("status is invalid", NsErrorCode.INVALID_VALUE) from exc

        if status not in (0, 1):
            raise BusinessError("status is invalid", NsErrorCode.INVALID_VALUE)

        return status

    @staticmethod
    def _normalize_priority(value: Any, *, default: int = 0) -> int:
        if value in (None, ""):
            return default

        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise BusinessError("priority is invalid", NsErrorCode.INVALID_VALUE) from exc

    @staticmethod
    def _normalize_optional_text(value: Any) -> str | None:
        if value in (None, ""):
            return None
        return str(value).strip() or None

    @classmethod
    def _normalize_subject_type(cls, value: Any) -> str | None:
        if value in (None, ""):
            return None
        subject_type: str = str(value).strip().upper()
        if subject_type not in ResourceAclService.SUBJECT_TYPES:
            raise BusinessError("subject_type is invalid", NsErrorCode.INVALID_VALUE)
        return subject_type

    @classmethod
    def _normalize_action_code(cls, value: Any) -> str:
        action_code: str = cls._normalize_required_text(value, "action_code").lower()
        if cls.ACTION_CODE_PATTERN.fullmatch(action_code) is None:
            raise BusinessError("action_code is invalid", NsErrorCode.PERMISSION_ACTION_INVALID)
        return action_code

    @classmethod
    def _normalize_optional_resource_type(cls, value: Any) -> str | None:
        if value in (None, ""):
            return None

        resource_type = str(value).strip().lower()
        if not resource_type or " " in resource_type:
            raise BusinessError("resource_type is invalid", NsErrorCode.INVALID_VALUE)
        return resource_type

    @classmethod
    def _normalize_effect(cls, value: Any, *, default: str) -> str:
        effect = str(default if value in (None, "") else value).strip().upper()
        if effect not in {cls.EFFECT_ALLOW, cls.EFFECT_DENY}:
            raise BusinessError("effect is invalid", NsErrorCode.INVALID_VALUE)
        return effect

    @staticmethod
    def _normalize_data_scope(value: Any) -> str | None:
        if value in (None, ""):
            return None

        storage_scope = to_storage_data_scope(str(value).strip())
        if storage_scope is None:
            raise BusinessError("data_scope is invalid", NsErrorCode.INVALID_VALUE)

        return storage_scope

    @staticmethod
    def _normalize_condition_json(value: Any) -> dict[str, Any] | None:
        if value in (None, ""):
            return None
        if not isinstance(value, dict):
            raise BusinessError("condition_json must be an object", NsErrorCode.INVALID_VALUE)
        return value

    @classmethod
    async def create_policy(cls, *, data: dict[str, Any], operator_id: int | None) -> dict[str, Any]:
        """Create one policy row."""
        request_data = cls._ensure_request_data(data)
        policy_code = cls._normalize_required_text(request_data.get("policy_code"), "policy_code").lower()
        policy_name = cls._normalize_required_text(request_data.get("policy_name"), "policy_name")
        priority = cls._normalize_priority(request_data.get("priority"), default=0)
        status = cls._normalize_status(request_data.get("status"), default=0)
        version = cls._normalize_priority(request_data.get("version"), default=1)

        existing = await PolicyRepository.get_policy_by_code(policy_code)
        if existing is not None:
            raise BusinessError("policy_code already exists", NsErrorCode.INVALID_VALUE)

        return await PolicyRepository.create_policy(
            policy_code=policy_code,
            policy_name=policy_name,
            priority=priority,
            status=status,
            version=version,
            operator_id=operator_id,
        )

    @classmethod
    async def update_policy(cls, *, data: dict[str, Any], operator_id: int | None) -> dict[str, Any]:
        """Update one policy row."""
        request_data = cls._ensure_request_data(data)
        policy_id = cls._normalize_optional_positive_int(request_data.get("policy_id"), "policy_id")
        policy_code = cls._normalize_optional_text(request_data.get("policy_code"))

        policy = None
        if policy_id is not None:
            policy = await PolicyRepository.get_policy_by_id(policy_id)
        elif policy_code is not None:
            policy = await PolicyRepository.get_policy_by_code(policy_code.lower())

        if policy is None:
            raise BusinessError("policy not found", NsErrorCode.DATA_NOT_FOUND)

        update_data: dict[str, Any] = {}
        if request_data.get("policy_name") not in (None, ""):
            update_data["policy_name"] = cls._normalize_required_text(request_data.get("policy_name"), "policy_name")
        if request_data.get("priority") not in (None, ""):
            update_data["priority"] = cls._normalize_priority(request_data.get("priority"))

        if not update_data:
            return {"id": policy.id}

        await PolicyRepository.update_policy(item=policy, data=update_data, operator_id=operator_id)
        AuthorizationContextService.invalidate_all()
        return {"id": policy.id}

    @classmethod
    async def publish_policy(cls, *, data: dict[str, Any], operator_id: int | None) -> dict[str, Any]:
        """Publish one policy by setting status=1 and increasing version."""
        request_data = cls._ensure_request_data(data)
        policy_id = cls._normalize_positive_int(request_data.get("policy_id"), "policy_id")
        policy = await PolicyRepository.get_policy_by_id(policy_id)
        if policy is None:
            raise BusinessError("policy not found", NsErrorCode.DATA_NOT_FOUND)

        await PolicyRepository.update_policy(
            item=policy,
            data={
                "status": 1,
                "version": int(getattr(policy, "version", 0) or 0) + 1,
            },
            operator_id=operator_id,
        )
        AuthorizationContextService.invalidate_all()
        return {"id": policy.id}

    @classmethod
    async def disable_policy(cls, *, data: dict[str, Any], operator_id: int | None) -> dict[str, Any]:
        """Disable one policy by setting status=0."""
        request_data = cls._ensure_request_data(data)
        policy_id = cls._normalize_positive_int(request_data.get("policy_id"), "policy_id")
        policy = await PolicyRepository.get_policy_by_id(policy_id)
        if policy is None:
            raise BusinessError("policy not found", NsErrorCode.DATA_NOT_FOUND)

        await PolicyRepository.update_policy(item=policy, data={"status": 0}, operator_id=operator_id)
        AuthorizationContextService.invalidate_all()
        return {"id": policy.id}

    @classmethod
    async def add_rule(cls, *, data: dict[str, Any], operator_id: int | None) -> dict[str, Any]:
        """Create one policy rule."""
        request_data = cls._ensure_request_data(data)
        policy_id = cls._normalize_positive_int(request_data.get("policy_id"), "policy_id")

        policy = await PolicyRepository.get_policy_by_id(policy_id)
        if policy is None:
            raise BusinessError("policy not found", NsErrorCode.DATA_NOT_FOUND)

        subject_type = cls._normalize_subject_type(request_data.get("subject_type"))
        subject_id = cls._normalize_optional_positive_int(request_data.get("subject_id"), "subject_id")
        resource_type = cls._normalize_optional_resource_type(request_data.get("resource_type"))
        resource_id = cls._normalize_optional_text(request_data.get("resource_id"))
        action_code = cls._normalize_action_code(request_data.get("action_code"))
        effect = cls._normalize_effect(request_data.get("effect"), default=cls.EFFECT_DENY)
        data_scope = cls._normalize_data_scope(request_data.get("data_scope"))
        condition_json = cls._normalize_condition_json(request_data.get("condition_json"))
        priority = cls._normalize_priority(request_data.get("priority"), default=0)
        status = cls._normalize_status(request_data.get("status"), default=1)

        if resource_type is not None:
            resource = await ResourceRepository.get_active_resource_by_type(resource_type)
            if resource is None:
                raise BusinessError("resource_type does not exist", NsErrorCode.DATA_NOT_FOUND)

            has_action = await ResourceRepository.has_action_for_resource_type(
                resource_type=resource_type,
                action_code=action_code,
            )
            if not has_action:
                raise BusinessError("action_code does not exist under resource_type", NsErrorCode.DATA_NOT_FOUND)
        else:
            has_global_action = await ResourceRepository.action_exists_globally(action_code=action_code)
            if not has_global_action:
                raise BusinessError("action_code is not registered", NsErrorCode.DATA_NOT_FOUND)

        created = await PolicyRepository.create_rule(
            policy_id=policy_id,
            subject_type=subject_type,
            subject_id=subject_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action_code=action_code,
            effect=effect,
            data_scope=data_scope,
            condition_json=condition_json,
            priority=priority,
            status=status,
            operator_id=operator_id,
        )
        AuthorizationContextService.invalidate_all()
        return created

    @classmethod
    async def remove_rule(cls, *, data: dict[str, Any]) -> dict[str, bool]:
        """Remove one policy rule by id."""
        request_data = cls._ensure_request_data(data)
        rule_id = cls._normalize_positive_int(request_data.get("rule_id"), "rule_id")
        rule = await PolicyRepository.get_rule_by_id(rule_id)
        if rule is None:
            return {"removed": False}

        await PolicyRepository.delete_rule(rule)
        AuthorizationContextService.invalidate_all()
        return {"removed": True}

    @classmethod
    async def list_rules(cls, *, data: dict[str, Any]) -> dict[str, Any]:
        """List policy rules with optional filters."""
        request_data = cls._ensure_request_data(data)
        page = request_data.get("page", 1)
        page_size = request_data.get("page_size", 20)

        filters: dict[str, Any] = {}
        raw_filters = request_data.get("filters")
        if isinstance(raw_filters, dict):
            filters.update(raw_filters)

        if request_data.get("policy_id") not in (None, ""):
            filters["policy_id"] = cls._normalize_positive_int(request_data.get("policy_id"), "policy_id")

        if request_data.get("status") not in (None, ""):
            filters["status"] = cls._normalize_status(request_data.get("status"))

        if request_data.get("action_code") not in (None, ""):
            filters["action_code"] = cls._normalize_action_code(request_data.get("action_code"))

        return await PolicyRepository.list_rules(page=page, page_size=page_size, filters=filters or None)

