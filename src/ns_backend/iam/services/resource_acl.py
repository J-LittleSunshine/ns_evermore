# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.utils import timezone

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.constants import normalize_data_scope, to_storage_data_scope
from ns_backend.iam.repositories import ResourceAclRepository, ResourceRepository
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class ResourceAclService:
    """Service for IAM resource ACL grant/revoke/list and effect resolution."""

    SUBJECT_TYPES: set[str] = {
        "USER",
        "ROLE",
        "DEPARTMENT",
        "ORGANIZATION",
        "SUBSIDIARY",
    }

    EFFECT_ALLOW = "ALLOW"
    EFFECT_DENY = "DENY"

    ALLOWED_ACTION_CODES: set[str] = {
        "add",
        "approve",
        "batch_check",
        "bind",
        "check",
        "create",
        "current_user",
        "data_scopes",
        "delete",
        "detail",
        "disable",
        "execute",
        "grant",
        "list",
        "login",
        "logout",
        "manage",
        "menus",
        "permissions",
        "profile",
        "publish",
        "read",
        "refresh",
        "register",
        "remove",
        "reset_password",
        "revoke",
        "share",
        "sync",
        "unbind",
        "update",
        "update_staff",
        "update_superuser",
        "write",
    }

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
            normalized_value: int = int(value)
        except (TypeError, ValueError) as exc:
            raise BusinessError(f"{field_name} is invalid", NsErrorCode.INVALID_VALUE) from exc

        if normalized_value <= 0:
            raise BusinessError(f"{field_name} is invalid", NsErrorCode.INVALID_VALUE)

        return normalized_value

    @classmethod
    def _normalize_subject_type(cls, value: Any) -> str:
        subject_type: str = cls._normalize_required_text(value, "subject_type").upper()
        if subject_type not in cls.SUBJECT_TYPES:
            raise BusinessError("subject_type is invalid", NsErrorCode.INVALID_VALUE)
        return subject_type

    @classmethod
    def _normalize_resource_type(cls, value: Any) -> str:
        resource_type: str = cls._normalize_required_text(value, "resource_type").lower()
        if " " in resource_type:
            raise BusinessError("resource_type is invalid", NsErrorCode.INVALID_VALUE)
        return resource_type

    @classmethod
    def _normalize_action_code(cls, value: Any) -> str:
        action_code: str = cls._normalize_required_text(value, "action_code").lower()
        if action_code not in cls.ALLOWED_ACTION_CODES:
            raise BusinessError("action_code is invalid", NsErrorCode.PERMISSION_ACTION_INVALID)
        return action_code

    @classmethod
    def _normalize_effect(cls, value: Any, *, default: str) -> str:
        effect: str = str(default if value in (None, "") else value).strip().upper()
        if effect not in {cls.EFFECT_ALLOW, cls.EFFECT_DENY}:
            raise BusinessError("effect is invalid", NsErrorCode.INVALID_VALUE)
        return effect

    @staticmethod
    def _normalize_resource_id(value: Any) -> str:
        resource_id: str = str(value or "").strip()
        if not resource_id:
            raise BusinessError("resource_id is required", NsErrorCode.INVALID_VALUE)
        return resource_id

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

    @staticmethod
    def _normalize_data_scope(value: Any) -> str | None:
        if value in (None, ""):
            return None

        storage_scope: str | None = to_storage_data_scope(str(value).strip())
        if storage_scope is None:
            raise BusinessError("data_scope is invalid", NsErrorCode.INVALID_VALUE)

        return storage_scope

    @classmethod
    async def grant_acl(cls, *, data: dict[str, Any], operator_id: int | None) -> dict[str, Any]:
        """Grant or update one ACL record idempotently."""
        request_data: dict[str, Any] = cls._ensure_request_data(data)
        subject_type: str = cls._normalize_subject_type(request_data.get("subject_type"))
        subject_id: int = cls._normalize_positive_int(request_data.get("subject_id"), "subject_id")
        resource_type: str = cls._normalize_resource_type(request_data.get("resource_type"))
        resource_id: str = cls._normalize_resource_id(request_data.get("resource_id"))
        action_code: str = cls._normalize_action_code(request_data.get("action_code"))
        effect: str = cls._normalize_effect(request_data.get("effect"), default=cls.EFFECT_ALLOW)
        data_scope: str | None = cls._normalize_data_scope(request_data.get("data_scope"))
        expired_at = request_data.get("expired_at")

        resource_item = await ResourceRepository.get_resource_by_type(resource_type)
        if resource_item is None:
            raise BusinessError("resource_type does not exist", NsErrorCode.DATA_NOT_FOUND)

        resource_action = await ResourceRepository.get_resource_action(resource_id=resource_item.id, action_code=action_code)
        if resource_action is None:
            raise BusinessError("action_code does not exist under resource_type", NsErrorCode.DATA_NOT_FOUND)

        existing = await ResourceAclRepository.get_acl(
            subject_type=subject_type,
            subject_id=subject_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action_code=action_code,
        )
        if existing is None:
            return await ResourceAclRepository.create_acl(
                subject_type=subject_type,
                subject_id=subject_id,
                resource_type=resource_type,
                resource_id=resource_id,
                action_code=action_code,
                effect=effect,
                data_scope=data_scope,
                expired_at=expired_at,
                operator_id=operator_id,
            )

        has_changes: bool = any(
            (
                existing.effect != effect,
                existing.data_scope != data_scope,
                existing.expired_at != expired_at,
            )
        )
        if has_changes:
            await ResourceAclRepository.update_acl(
                item=existing,
                effect=effect,
                data_scope=data_scope,
                expired_at=expired_at,
                operator_id=operator_id,
            )

        return {"id": existing.id}

    @classmethod
    async def revoke_acl(cls, *, data: dict[str, Any]) -> dict[str, bool]:
        """Revoke one ACL record by unique subject-resource-action key."""
        request_data: dict[str, Any] = cls._ensure_request_data(data)
        subject_type: str = cls._normalize_subject_type(request_data.get("subject_type"))
        subject_id: int = cls._normalize_positive_int(request_data.get("subject_id"), "subject_id")
        resource_type: str = cls._normalize_resource_type(request_data.get("resource_type"))
        resource_id: str = cls._normalize_resource_id(request_data.get("resource_id"))
        action_code: str = cls._normalize_action_code(request_data.get("action_code"))

        existing = await ResourceAclRepository.get_acl(
            subject_type=subject_type,
            subject_id=subject_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action_code=action_code,
        )
        if existing is None:
            return {"revoked": False}

        await ResourceAclRepository.delete_acl(existing)
        return {"revoked": True}

    @classmethod
    async def list_acls(cls, *, data: dict[str, Any]) -> dict[str, Any]:
        """List ACL records with subject/resource/action filters."""
        request_data: dict[str, Any] = cls._ensure_request_data(data)
        page: int | str | None = request_data.get("page", 1)
        page_size: int | str | None = request_data.get("page_size", 20)

        filters: dict[str, Any] = {}
        raw_filters: Any = request_data.get("filters")
        if isinstance(raw_filters, dict):
            filters.update(raw_filters)

        if request_data.get("subject_type") not in (None, ""):
            filters["subject_type"] = cls._normalize_subject_type(request_data.get("subject_type"))

        if request_data.get("subject_id") not in (None, ""):
            filters["subject_id"] = cls._normalize_positive_int(request_data.get("subject_id"), "subject_id")

        if request_data.get("resource_type") not in (None, ""):
            filters["resource_type"] = cls._normalize_resource_type(request_data.get("resource_type"))

        if request_data.get("resource_id") not in (None, ""):
            filters["resource_id"] = cls._normalize_resource_id(request_data.get("resource_id"))

        if request_data.get("action_code") not in (None, ""):
            filters["action_code"] = cls._normalize_action_code(request_data.get("action_code"))

        if request_data.get("effect") not in (None, ""):
            filters["effect"] = cls._normalize_effect(request_data.get("effect"), default=cls.EFFECT_ALLOW)

        if request_data.get("data_scope") not in (None, ""):
            filters["data_scope"] = cls._normalize_data_scope(request_data.get("data_scope"))

        result: dict[str, Any] = await ResourceAclRepository.list_acls(page=page, page_size=page_size, filters=filters or None)
        items: list[dict[str, Any]] = result.get("items", [])
        for item in items:
            item["normalized_scope"] = normalize_data_scope(item.get("data_scope"))

        return result

    @classmethod
    async def resolve_acl_effect(
        cls,
        *,
        subject_bindings: list[tuple[str, int]],
        resource_type: str,
        resource_id: str,
        action_code: str,
    ) -> dict[str, Any] | None:
        """Resolve ACL effect with deny-first precedence for one resource action."""
        normalized_bindings: list[tuple[str, int]] = []
        for subject_type, subject_id in subject_bindings:
            normalized_bindings.append((cls._normalize_subject_type(subject_type), cls._normalize_positive_int(subject_id, "subject_id")))

        now = timezone.now()
        effect_rows: list[dict[str, Any]] = await ResourceAclRepository.list_active_effects(
            subject_bindings=normalized_bindings,
            resource_type=cls._normalize_resource_type(resource_type),
            resource_id=cls._normalize_resource_id(resource_id),
            action_code=cls._normalize_action_code(action_code),
            now=now,
        )

        if not effect_rows:
            return None

        deny_rows: list[dict[str, Any]] = [row for row in effect_rows if str(row.get("effect", "")).upper() == cls.EFFECT_DENY]
        if deny_rows:
            deny_item: dict[str, Any] = deny_rows[0]
            return {
                "effect": cls.EFFECT_DENY,
                "matched_acl_id": deny_item.get("id"),
                "reason": "ACL_DENY",
            }

        allow_rows: list[dict[str, Any]] = [row for row in effect_rows if str(row.get("effect", "")).upper() == cls.EFFECT_ALLOW]
        if allow_rows:
            allow_item: dict[str, Any] = allow_rows[0]
            return {
                "effect": cls.EFFECT_ALLOW,
                "matched_acl_id": allow_item.get("id"),
                "reason": "ACL_ALLOW",
            }

        return None

