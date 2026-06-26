# -*- coding: utf-8 -*-
from __future__ import annotations

import hmac
from typing import (
    Any,
    TYPE_CHECKING,
)

from django.conf import settings

from ns_backend.iam.errors import (
    IamRuntimeRequestInvalidError,
    IamUserDisabledOrNotFoundError,
    IamUserNotLoggedInOrSessionExpiredError,
)
from ns_backend.iam.repositories import AuthUserRepository
from ns_backend.iam.services.access_decision import AccessDecisionService
from ns_backend.iam.services.auth import AuthService
from ns_backend.iam.services.resource_access_filter import ResourceAccessFilterService

if TYPE_CHECKING:
    pass


class InternalIamService:
    PRINCIPAL_TYPE_FRONTEND_USER = "FRONTEND_USER"

    @classmethod
    def verify_internal_service_token(cls, token: str | None) -> bool:
        expected_token = str(getattr(settings, "IAM_INTERNAL_TOKEN", "") or "").strip()

        if not expected_token:
            return False

        normalized_token = str(token or "").strip()

        if not normalized_token:
            return False

        return hmac.compare_digest(
            normalized_token,
            expected_token,
        )

    @classmethod
    async def introspect_token(cls, data: dict[str, Any]) -> dict[str, Any]:
        request_data = cls.ensure_dict(data)
        token = cls.normalize_required_text(
            request_data.get("token"),
            "token",
        )
        token_type = str(request_data.get("token_type") or "access").strip().lower()

        if token_type != "access":
            return {
                "active": False,
                "reason": "UNSUPPORTED_TOKEN_TYPE",
                "principal": None,
            }

        try:
            user, _ = await AuthService.resolve_user_from_access_token(token)
        except (
                IamUserNotLoggedInOrSessionExpiredError,
                IamUserDisabledOrNotFoundError,
        ):
            return {
                "active": False,
                "reason": "TOKEN_INVALID_OR_EXPIRED",
                "principal": None,
            }

        user_id = getattr(user, "id", None)

        principal = {
            "principal_type": cls.PRINCIPAL_TYPE_FRONTEND_USER,
            "principal_id": str(user_id),
            "authenticated": True,
            "display_name": str(getattr(user, "display_name", None) or getattr(user, "username", None) or user_id),
            "user_id": str(user_id),
            "client_id": cls.normalize_optional(request_data.get("client_id")),
            "session_id": cls.normalize_optional(request_data.get("session_id")),
            "claims": {
                "username": getattr(user, "username", None),
                "user_type": getattr(user, "user_type", None),
                "company_id": cls.normalize_optional(getattr(user, "company_id", None)),
                "subsidiary_id": cls.normalize_optional(getattr(user, "subsidiary_id", None)),
                "department_id": cls.normalize_optional(getattr(user, "department_id", None)),
                "is_superuser": bool(getattr(user, "is_superuser", False)),
                "is_staff": bool(getattr(user, "is_staff", False)),
            },
            "expires_at_epoch_ms": None,
        }

        return {
            "active": True,
            "reason": "TOKEN_ACTIVE",
            "principal": principal,
            "user": cls.serialize_user(user),
        }

    @classmethod
    async def access_check(cls, data: dict[str, Any], *, trace_id: str | None = None) -> dict[str, Any]:
        request_data = cls.ensure_dict(data)
        principal = cls.ensure_principal(request_data.get("principal"))

        user_id = cls.resolve_user_id_from_principal(principal)

        user = await AuthUserRepository.get_user_by_id(user_id)
        if user is None or not bool(getattr(user, "is_active", False)):
            return cls.deny_decision(
                reason="USER_INACTIVE",
                request_data=request_data,
                principal=principal,
                trace_id=trace_id,
            )

        access_data = cls.attach_runtime_context(
            request_data=request_data,
            principal=principal,
        )

        return await AccessDecisionService.check_with_audit(
            user=user,
            data=access_data,
            trace_id=trace_id,
        )

    @classmethod
    async def batch_access_check(cls, data: dict[str, Any], *, trace_id: str | None = None) -> dict[str, Any]:
        request_data = cls.ensure_dict(data)
        items = request_data.get("items") or request_data.get("requests") or []
        principal = request_data.get("principal")

        if not isinstance(items, list):
            raise IamRuntimeRequestInvalidError(
                "items must be a list.",
            )

        results = []

        for item in items:
            if not isinstance(item, dict):
                results.append(
                    cls.deny_decision(
                        reason="REQUEST_ITEM_INVALID",
                        request_data={},
                        principal={},
                        trace_id=trace_id,
                    )
                )
                continue

            item_data = dict(item)
            if "principal" not in item_data and isinstance(principal, dict):
                item_data["principal"] = dict(principal)

            results.append(
                await cls.access_check(
                    item_data,
                    trace_id=trace_id,
                )
            )

        return {
            "items": results,
            "total": len(results),
        }

    @classmethod
    async def resolve_resource_filter(cls, data: dict[str, Any], *, trace_id: str | None = None) -> dict[str, Any]:
        request_data = cls.ensure_dict(data)
        principal = cls.ensure_principal(request_data.get("principal"))

        user_id = cls.resolve_user_id_from_principal(principal)

        user = await AuthUserRepository.get_user_by_id(user_id)
        if user is None or not bool(getattr(user, "is_active", False)):
            result = ResourceAccessFilterService.build_deny_all_filter(
                reason="USER_INACTIVE",
            )
            result["trace_id"] = trace_id
            return result

        raw_field_map = request_data.get("field_map")
        field_map = raw_field_map if isinstance(raw_field_map, dict) else None

        result = await ResourceAccessFilterService.resolve_retrieval_filter(
            user=user,
            resource_type=request_data.get("resource_type"),
            action_code=request_data.get("action_code"),
            permission_code=cls.normalize_optional(request_data.get("permission_code")),
            field_map=field_map,
        )

        result["trace_id"] = trace_id
        return result

    @classmethod
    def attach_runtime_context(cls, *, request_data: dict[str, Any], principal: dict[str, Any]) -> dict[str, Any]:
        access_data = dict(request_data)

        raw_context = access_data.get("context")
        if isinstance(raw_context, dict):
            context = dict(raw_context)
        else:
            context = {}

        context.setdefault(
            "runtime_principal",
            dict(principal),
        )
        context.setdefault(
            "runtime_principal_type",
            cls.normalize_optional(principal.get("principal_type")),
        )
        context.setdefault(
            "runtime_principal_id",
            cls.normalize_optional(principal.get("principal_id")),
        )
        context.setdefault(
            "runtime_client_id",
            cls.normalize_optional(principal.get("client_id")),
        )
        context.setdefault(
            "runtime_session_id",
            cls.normalize_optional(principal.get("session_id")),
        )

        access_data["context"] = context
        return access_data

    @classmethod
    def resolve_user_id_from_principal(cls, principal: dict[str, Any]) -> int:
        principal_type = str(principal.get("principal_type") or "").strip()

        if principal_type != cls.PRINCIPAL_TYPE_FRONTEND_USER:
            raise IamRuntimeRequestInvalidError(
                "Unsupported runtime principal type.",
                details={
                    "principal_type": principal_type,
                },
            )

        user_id_text = cls.normalize_required_text(
            principal.get("user_id") or principal.get("principal_id"),
            "principal.user_id",
        )

        try:
            user_id = int(user_id_text)
        except (TypeError, ValueError) as exc:
            raise IamRuntimeRequestInvalidError(
                "principal.user_id is invalid.",
                details={
                    "user_id": user_id_text,
                },
            ) from exc

        if user_id <= 0:
            raise IamRuntimeRequestInvalidError(
                "principal.user_id is invalid.",
                details={
                    "user_id": user_id,
                },
            )

        return user_id

    @classmethod
    def deny_decision(cls, *, reason: str, request_data: dict[str, Any], principal: dict[str, Any], trace_id: str | None) -> dict[str, Any]:
        return {
            "allowed": False,
            "effect": "deny",
            "reason": reason,
            "matched_source": "runtime_iam_internal",
            "resource_type": cls.normalize_optional(request_data.get("resource_type")),
            "resource_id": cls.normalize_optional(request_data.get("resource_id")),
            "action_code": cls.normalize_optional(request_data.get("action_code")),
            "permission_code": cls.normalize_optional(request_data.get("permission_code")),
            "filters": {},
            "hit_details": {
                "principal": dict(principal or {}),
            },
            "decision_chain": [
                {
                    "source": "runtime_iam_internal",
                    "effect": "deny",
                    "reason": reason,
                }
            ],
            "trace_id": trace_id,
        }

    @staticmethod
    def ensure_dict(data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise IamRuntimeRequestInvalidError(
                "Request payload must be an object.",
            )

        return dict(data)

    @staticmethod
    def ensure_principal(value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise IamRuntimeRequestInvalidError(
                "principal must be an object.",
            )

        return dict(value)

    @staticmethod
    def normalize_required_text(value: Any, field_name: str) -> str:
        normalized = str(value or "").strip()

        if not normalized:
            raise IamRuntimeRequestInvalidError(
                f"{field_name} is required.",
                details={
                    "field": field_name,
                },
            )

        return normalized

    @staticmethod
    def normalize_optional(value: Any) -> str | None:
        if value is None:
            return None

        normalized = str(value).strip()
        return normalized or None

    @staticmethod
    def serialize_user(user: Any) -> dict[str, Any]:
        return {
            "id": getattr(user, "id", None),
            "username": getattr(user, "username", None),
            "display_name": getattr(user, "display_name", None),
            "user_type": getattr(user, "user_type", None),
            "is_active": bool(getattr(user, "is_active", False)),
            "is_staff": bool(getattr(user, "is_staff", False)),
            "is_superuser": bool(getattr(user, "is_superuser", False)),
            "company_id": getattr(user, "company_id", None),
            "subsidiary_id": getattr(user, "subsidiary_id", None),
            "department_id": getattr(user, "department_id", None),
        }
