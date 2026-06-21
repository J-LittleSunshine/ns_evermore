# -*- coding: utf-8 -*-
from __future__ import annotations

import hmac
from typing import Any

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.repositories import AuthUserRepository
from ns_backend.iam.services.authorize import AuthorizeService
from ns_backend.iam.services.verify import VerifyService
from ns_common.config import ns_config
from ns_common.error_codes import NsErrorCode
from ns_common.runtime.permissions import (
    RUNTIME_PRINCIPAL_FRONTEND_USER,
)


class RuntimeIamInternalAuthService:
    """Internal IAM service for ns_runtime authentication and authorization.

    This service is intentionally HTTP-facing through an internal API. ns_runtime
    must not import Django ORM or IAM repositories directly.
    """

    @classmethod
    def verify_internal_service_token(cls, token: str | None) -> bool:
        """Verify internal service bearer token for ns_runtime -> ns_backend IAM calls."""
        expected_token = cls._expected_internal_service_token()
        if not expected_token:
            return False

        normalized_token = str(token or "").strip()
        if not normalized_token:
            return False

        return hmac.compare_digest(normalized_token, expected_token)

    @classmethod
    async def introspect_token(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Introspect a frontend access token and return runtime principal payload."""
        request_data = cls._ensure_request_data(data)
        token = cls._normalize_required_text(request_data.get("token"), "token")
        token_type = str(request_data.get("token_type") or "access").strip().lower()

        if token_type != "access":
            return {
                "active": False,
                "reason": "UNSUPPORTED_TOKEN_TYPE",
                "principal": None,
            }

        user = await VerifyService.get_user_by_access_token(token)
        if user is None:
            return {
                "active": False,
                "reason": "TOKEN_INVALID_OR_EXPIRED",
                "principal": None,
            }

        user_id = getattr(user, "id", None)
        principal = {
            "principal_type": RUNTIME_PRINCIPAL_FRONTEND_USER,
            "principal_id": str(user_id),
            "authenticated": True,
            "display_name": str(getattr(user, "nickname", None) or getattr(user, "username", None) or user_id),
            "user_id": str(user_id),
            "service_id": None,
            "backend_id": None,
            "node_id": None,
            "client_id": cls._normalize_optional(request_data.get("client_id")),
            "session_id": cls._normalize_optional(request_data.get("session_id")),
            "claims": {
                "username": getattr(user, "username", None),
                "company_id": cls._normalize_optional(getattr(user, "company_id", None)),
                "subsidiary_id": cls._normalize_optional(getattr(user, "subsidiary_id", None)),
                "department_id": cls._normalize_optional(getattr(user, "department_id", None)),
                "is_superuser": bool(getattr(user, "is_superuser", False)),
                "is_staff": bool(getattr(user, "is_staff", False)),
            },
            "expires_at_epoch_ms": None,
        }

        return {
            "active": True,
            "reason": "TOKEN_ACTIVE",
            "principal": principal,
            "user": cls._serialize_user(user),
        }

    @classmethod
    async def authorize(cls, data: dict[str, Any], *, trace_id: str | None = None) -> dict[str, Any]:
        """Authorize one runtime IAM action."""
        request_data = cls._ensure_request_data(data)
        principal = cls._ensure_principal(request_data.get("principal"))
        principal_type = str(principal.get("principal_type") or "").strip()

        if principal_type != RUNTIME_PRINCIPAL_FRONTEND_USER:
            return cls._deny_decision(
                reason="UNSUPPORTED_RUNTIME_PRINCIPAL_TYPE",
                resource_type=request_data.get("resource_type"),
                resource_id=request_data.get("resource_id"),
                action_code=request_data.get("action_code"),
                principal=principal,
            )

        user_id_text = cls._normalize_required_text(principal.get("user_id") or principal.get("principal_id"), "principal.user_id")
        try:
            user_id = int(user_id_text)
        except (
                TypeError,
                ValueError
        ):
            return cls._deny_decision(
                reason="INVALID_RUNTIME_USER_ID",
                resource_type=request_data.get("resource_type"),
                resource_id=request_data.get("resource_id"),
                action_code=request_data.get("action_code"),
                principal=principal,
            )

        user = await AuthUserRepository.get_user_by_id(user_id)
        if user is None or not bool(getattr(user, "is_active", False)):
            return cls._deny_decision(
                reason="USER_INACTIVE",
                resource_type=request_data.get("resource_type"),
                resource_id=request_data.get("resource_id"),
                action_code=request_data.get("action_code"),
                principal=principal,
            )

        iam_payload = cls._build_authorize_payload(request_data=request_data, principal=principal)
        decision = await AuthorizeService.check(user=user, data=iam_payload, trace_id=trace_id)
        return {
            "allowed": bool(decision.get("allowed")),
            "effect": str(decision.get("effect") or ("allow" if bool(decision.get("allowed")) else "deny")),
            "reason": str(decision.get("reason") or ""),
            "matched_source": decision.get("matched_source"),
            "resource_type": iam_payload["resource_type"],
            "resource_id": iam_payload["resource_id"],
            "action_code": iam_payload["action_code"],
            "permission_code": iam_payload.get("permission_code"),
            "hit_details": dict(decision.get("hit_details") or {}),
            "decision_chain": list(decision.get("decision_chain") or []),
            "raw_decision": dict(decision),
        }

    @classmethod
    async def batch_authorize(cls, data: dict[str, Any], *, trace_id: str | None = None) -> dict[str, Any]:
        """Authorize multiple runtime IAM actions."""
        request_data = cls._ensure_request_data(data)
        items = request_data.get("items") or request_data.get("requests") or []
        if not isinstance(items, list):
            raise BusinessError("items must be a list", NsErrorCode.INVALID_VALUE)

        results: list[dict[str, Any]] = []
        for item in items:
            if not isinstance(item, dict):
                results.append(cls._deny_decision(reason="REQUEST_ITEM_INVALID"))
                continue
            results.append(await cls.authorize(item, trace_id=trace_id))

        return {
            "results": results,
        }

    @classmethod
    def _build_authorize_payload(cls, *, request_data: dict[str, Any], principal: dict[str, Any]) -> dict[str, Any]:
        """Build payload accepted by AuthorizeService.check()."""
        resource_type = cls._normalize_required_text(request_data.get("resource_type"), "resource_type").lower()
        resource_id = cls._normalize_required_text(request_data.get("resource_id"), "resource_id")
        action_code = cls._normalize_required_text(request_data.get("action_code"), "action_code").lower()

        context = request_data.get("context") or {}
        if not isinstance(context, dict):
            context = {}

        merged_context = dict(context)
        merged_context["runtime_principal"] = dict(principal)

        payload = {
            "resource_type": resource_type,
            "resource_id": resource_id,
            "action_code": action_code,
            "context": merged_context,
        }

        permission_code = cls._normalize_optional(request_data.get("permission_code"))
        if permission_code is not None:
            payload["permission_code"] = permission_code

        return payload

    @classmethod
    def _deny_decision(
            cls,
            *,
            reason: str,
            resource_type: Any = None,
            resource_id: Any = None,
            action_code: Any = None,
            principal: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Build normalized deny decision without calling IAM engine."""
        return {
            "allowed": False,
            "effect": "deny",
            "reason": str(reason or "DENY"),
            "matched_source": "runtime_iam_internal",
            "resource_type": cls._normalize_optional(resource_type),
            "resource_id": cls._normalize_optional(resource_id),
            "action_code": cls._normalize_optional(action_code),
            "permission_code": None,
            "hit_details": {
                "principal": dict(principal or {}),
            },
            "decision_chain": [
                {
                    "source": "runtime_iam_internal",
                    "effect": "deny",
                    "reason": str(reason or "DENY"),
                }
            ],
            "raw_decision": {},
        }

    @staticmethod
    def _ensure_request_data(data: dict[str, Any] | None) -> dict[str, Any]:
        """Validate request payload object."""
        if not isinstance(data, dict):
            raise BusinessError("request data must be an object", NsErrorCode.INVALID_VALUE)
        return data

    @staticmethod
    def _ensure_principal(value: Any) -> dict[str, Any]:
        """Validate runtime principal payload."""
        if not isinstance(value, dict):
            raise BusinessError("principal must be an object", NsErrorCode.INVALID_VALUE)
        return dict(value)

    @staticmethod
    def _normalize_required_text(value: Any, field_name: str) -> str:
        """Normalize required text field."""
        normalized = str(value or "").strip()
        if not normalized:
            raise BusinessError(f"{field_name} is required", NsErrorCode.INVALID_VALUE)
        return normalized

    @staticmethod
    def _normalize_optional(value: Any) -> str | None:
        """Normalize optional text field."""
        if value is None:
            return None

        normalized = str(value).strip()
        return normalized or None

    @staticmethod
    def _serialize_user(user: Any) -> dict[str, Any]:
        """Serialize IAM user for runtime token introspection response."""
        user_id = getattr(user, "id", None)
        return {
            "id": user_id,
            "username": getattr(user, "username", None),
            "nickname": getattr(user, "nickname", None),
            "is_active": bool(getattr(user, "is_active", False)),
            "is_staff": bool(getattr(user, "is_staff", False)),
            "is_superuser": bool(getattr(user, "is_superuser", False)),
            "company_id": getattr(user, "company_id", None),
            "subsidiary_id": getattr(user, "subsidiary_id", None),
            "department_id": getattr(user, "department_id", None),
        }

    @staticmethod
    def _expected_internal_service_token() -> str:
        """Return internal service token for ns_runtime -> ns_backend IAM calls."""
        runtime_config = ns_config.runtime_config
        return str(
            getattr(runtime_config, "iam_internal_service_token", "")
            or getattr(runtime_config, "service_token", "")
            or ""
        ).strip()
