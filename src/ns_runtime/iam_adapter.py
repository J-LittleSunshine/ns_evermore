# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import (
    dataclass,
    field,
)
from typing import (
    Any,
    Mapping,
)

from ns_common.config import ns_config
from ns_common.exceptions import (
    NsDependencyError,
    NsRuntimeAuthError,
    NsRuntimeCodecError,
)
from ns_common.http_client import (
    NsAsyncHttpClient,
    get_async_http_client,
)
from ns_common.logger import get_ns_logger
from ns_common.runtime_config import NsRuntimeConfig


@dataclass(slots=True, kw_only=True)
class NsRuntimeIamIntrospectionResult:
    active: bool
    reason: str
    principal: dict[str, Any] | None = None
    user: dict[str, Any] | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "NsRuntimeIamIntrospectionResult":
        data = _ensure_mapping(value, "introspection_response")

        active = _ensure_bool(data.get("active", False), "introspection_response.active")
        reason = _normalize_optional_text(data.get("reason")) or ("TOKEN_ACTIVE" if active else "TOKEN_INACTIVE")

        principal_raw = data.get("principal")
        if principal_raw is not None and not isinstance(principal_raw, Mapping):
            raise NsRuntimeCodecError(
                "introspection_response.principal must be a JSON object or null.",
                details={
                    "field": "introspection_response.principal",
                    "actual_type": type(principal_raw).__name__,
                },
            )

        user_raw = data.get("user")
        if user_raw is not None and not isinstance(user_raw, Mapping):
            raise NsRuntimeCodecError(
                "introspection_response.user must be a JSON object or null.",
                details={
                    "field": "introspection_response.user",
                    "actual_type": type(user_raw).__name__,
                },
            )

        return cls(
            active=active,
            reason=reason,
            principal=dict(principal_raw) if isinstance(principal_raw, Mapping) else None,
            user=dict(user_raw) if isinstance(user_raw, Mapping) else None,
            raw=dict(data),
        )


@dataclass(slots=True, kw_only=True)
class NsRuntimeIamAccessDecision:
    allowed: bool
    effect: str
    reason: str | None = None

    resource_type: str | None = None
    resource_id: str | None = None
    action_code: str | None = None
    permission_code: str | None = None

    filters: dict[str, Any] = field(default_factory=dict)
    hit_details: dict[str, Any] = field(default_factory=dict)
    decision_chain: list[dict[str, Any]] = field(default_factory=list)
    trace_id: str | None = None

    raw: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "NsRuntimeIamAccessDecision":
        data = _ensure_mapping(value, "access_decision")

        allowed = _ensure_bool(data.get("allowed", False), "access_decision.allowed")
        effect = _normalize_optional_text(data.get("effect")) or ("allow" if allowed else "deny")

        filters_raw = data.get("filters", {})
        if filters_raw is None:
            filters_raw = {}
        if not isinstance(filters_raw, Mapping):
            raise NsRuntimeCodecError(
                "access_decision.filters must be a JSON object.",
                details={
                    "field": "access_decision.filters",
                    "actual_type": type(filters_raw).__name__,
                },
            )

        hit_details_raw = data.get("hit_details", {})
        if hit_details_raw is None:
            hit_details_raw = {}
        if not isinstance(hit_details_raw, Mapping):
            raise NsRuntimeCodecError(
                "access_decision.hit_details must be a JSON object.",
                details={
                    "field": "access_decision.hit_details",
                    "actual_type": type(hit_details_raw).__name__,
                },
            )

        decision_chain_raw = data.get("decision_chain", [])
        if decision_chain_raw is None:
            decision_chain_raw = []
        if not isinstance(decision_chain_raw, list):
            raise NsRuntimeCodecError(
                "access_decision.decision_chain must be a list.",
                details={
                    "field": "access_decision.decision_chain",
                    "actual_type": type(decision_chain_raw).__name__,
                },
            )

        decision_chain: list[dict[str, Any]] = []
        for index, item in enumerate(decision_chain_raw):
            if not isinstance(item, Mapping):
                raise NsRuntimeCodecError(
                    "access_decision.decision_chain item must be a JSON object.",
                    details={
                        "field": "access_decision.decision_chain",
                        "index": index,
                        "actual_type": type(item).__name__,
                    },
                )
            decision_chain.append(dict(item))

        return cls(
            allowed=allowed,
            effect=effect,
            reason=_normalize_optional_text(data.get("reason")),
            resource_type=_normalize_optional_text(data.get("resource_type")),
            resource_id=_normalize_optional_text(data.get("resource_id")),
            action_code=_normalize_optional_text(data.get("action_code")),
            permission_code=_normalize_optional_text(data.get("permission_code")),
            filters=dict(filters_raw),
            hit_details=dict(hit_details_raw),
            decision_chain=decision_chain,
            trace_id=_normalize_optional_text(data.get("trace_id")),
            raw=dict(data),
        )


class NsRuntimeIamAdapter:
    INTROSPECT_TOKEN_PATH = "/internal/introspect_token/"
    ACCESS_CHECK_PATH = "/internal/access_check/"
    BATCH_ACCESS_CHECK_PATH = "/internal/batch_access_check/"
    RESOLVE_RESOURCE_FILTER_PATH = "/internal/resolve_resource_filter/"

    def __init__(self, *, runtime_config: NsRuntimeConfig | None = None, http_client: NsAsyncHttpClient | None = None) -> None:
        self.runtime_config: NsRuntimeConfig = runtime_config or ns_config.runtime
        self.iam_config = self.runtime_config.iam
        self.logger = get_ns_logger("ns_runtime.iam_adapter")
        self.http_client: NsAsyncHttpClient = http_client or get_async_http_client(
            name=f"runtime_iam.{self.runtime_config.runtime_id}",
            base_url="",
        )

    async def introspect_token(self, token: str, *, token_type: str = "access", client_id: str | None = None, session_id: str | None = None, trace_id: str | None = None) -> NsRuntimeIamIntrospectionResult:
        request_data: dict[str, Any] = {
            "token": _normalize_required_text(token, "token"),
            "token_type": _normalize_required_text(token_type, "token_type").lower(),
        }

        if client_id is not None:
            request_data["client_id"] = _normalize_required_text(client_id, "client_id")

        if session_id is not None:
            request_data["session_id"] = _normalize_required_text(session_id, "session_id")

        try:
            response_data = await self._post_json(
                self.INTROSPECT_TOKEN_PATH,
                request_data,
                trace_id=trace_id,
            )
            result = NsRuntimeIamIntrospectionResult.from_mapping(response_data)

            self.logger.info(
                "Runtime IAM token introspection completed.",
                extra={
                    "runtime_id": self.runtime_config.runtime_id,
                    "active": result.active,
                    "reason": result.reason,
                    "principal_type": (result.principal or {}).get("principal_type"),
                    "principal_id": (result.principal or {}).get("principal_id"),
                    "trace_id": trace_id,
                },
            )

            return result
        except NsDependencyError as exc:
            return self._handle_introspection_dependency_error(exc, trace_id=trace_id)

    async def access_check(
            self,
            *,
            principal: Mapping[str, Any],
            resource_type: str,
            resource_id: str,
            action_code: str,
            permission_code: str | None = None,
            context: Mapping[str, Any] | None = None,
            trace_id: str | None = None,
            extra: Mapping[str, Any] | None = None,
    ) -> NsRuntimeIamAccessDecision:
        request_data: dict[str, Any] = {
            "principal": _ensure_mapping(principal, "principal"),
            "resource_type": _normalize_required_text(resource_type, "resource_type"),
            "resource_id": _normalize_required_text(resource_id, "resource_id"),
            "action_code": _normalize_required_text(action_code, "action_code"),
            "context": dict(context or {}),
        }

        if permission_code is not None:
            request_data["permission_code"] = _normalize_required_text(permission_code, "permission_code")

        if extra:
            for key, value in extra.items():
                if key not in request_data:
                    request_data[str(key)] = value

        try:
            response_data = await self._post_json(
                self.ACCESS_CHECK_PATH,
                request_data,
                trace_id=trace_id,
            )
            decision = NsRuntimeIamAccessDecision.from_mapping(response_data)

            self.logger.info(
                "Runtime IAM access check completed.",
                extra={
                    "runtime_id": self.runtime_config.runtime_id,
                    "allowed": decision.allowed,
                    "effect": decision.effect,
                    "reason": decision.reason,
                    "resource_type": decision.resource_type,
                    "resource_id": decision.resource_id,
                    "action_code": decision.action_code,
                    "trace_id": decision.trace_id or trace_id,
                },
            )

            return decision
        except NsDependencyError as exc:
            return self._handle_access_check_dependency_error(
                exc,
                request_data=request_data,
                trace_id=trace_id,
            )

    async def batch_access_check(
            self,
            *,
            principal: Mapping[str, Any] | None = None,
            items: list[Mapping[str, Any]],
            trace_id: str | None = None,
    ) -> list[NsRuntimeIamAccessDecision]:
        if not isinstance(items, list):
            raise NsRuntimeAuthError(
                "batch access check items must be a list.",
                details={
                    "field": "items",
                    "actual_type": type(items).__name__,
                },
            )

        request_items: list[dict[str, Any]] = []
        for index, item in enumerate(items):
            if not isinstance(item, Mapping):
                raise NsRuntimeAuthError(
                    "batch access check item must be a JSON object.",
                    details={
                        "field": "items",
                        "index": index,
                        "actual_type": type(item).__name__,
                    },
                )

            request_items.append(dict(item))

        request_data: dict[str, Any] = {
            "items": request_items,
        }

        if principal is not None:
            request_data["principal"] = _ensure_mapping(principal, "principal")

        try:
            response_data = await self._post_json(
                self.BATCH_ACCESS_CHECK_PATH,
                request_data,
                trace_id=trace_id,
            )
        except NsDependencyError as exc:
            return [
                self._handle_access_check_dependency_error(
                    exc,
                    request_data=dict(item),
                    trace_id=trace_id,
                )
                for item in request_items
            ]

        raw_items = response_data.get("items")
        if not isinstance(raw_items, list):
            raise NsRuntimeCodecError(
                "batch_access_check response.items must be a list.",
                details={
                    "field": "batch_access_check.response.items",
                    "actual_type": type(raw_items).__name__,
                },
            )

        return [
            NsRuntimeIamAccessDecision.from_mapping(item)
            for item in raw_items
        ]

    async def resolve_resource_filter(
            self,
            *,
            principal: Mapping[str, Any],
            resource_type: str,
            action_code: str,
            permission_code: str | None = None,
            field_map: Mapping[str, str] | None = None,
            trace_id: str | None = None,
            extra: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        request_data: dict[str, Any] = {
            "principal": _ensure_mapping(principal, "principal"),
            "resource_type": _normalize_required_text(resource_type, "resource_type"),
            "action_code": _normalize_required_text(action_code, "action_code"),
        }

        if permission_code is not None:
            request_data["permission_code"] = _normalize_required_text(permission_code, "permission_code")

        if field_map is not None:
            request_data["field_map"] = dict(field_map)

        if extra:
            for key, value in extra.items():
                if key not in request_data:
                    request_data[str(key)] = value

        try:
            return await self._post_json(
                self.RESOLVE_RESOURCE_FILTER_PATH,
                request_data,
                trace_id=trace_id,
            )
        except NsDependencyError as exc:
            if self.iam_config.fail_policy == "fail_open":
                return {
                    "allowed": True,
                    "effect": "allow",
                    "reason": "IAM_UNAVAILABLE_FAIL_OPEN",
                    "filters": {},
                    "trace_id": trace_id,
                    "hit_details": {
                        "error": exc.to_dict(),
                    },
                }

            raise NsRuntimeAuthError(
                "Runtime IAM resource filter resolution failed.",
                details={
                    "runtime_id": self.runtime_config.runtime_id,
                    "base_url": self.iam_config.base_url,
                    "fail_policy": self.iam_config.fail_policy,
                    "trace_id": trace_id,
                    "error": exc.to_dict(),
                },
            ) from exc

    async def check_connection_access(
            self,
            *,
            principal: Mapping[str, Any],
            client_type: str,
            client_id: str | None = None,
            node_id: str | None = None,
            node_group: str | None = None,
            trace_id: str | None = None,
            extra_context: Mapping[str, Any] | None = None,
    ) -> NsRuntimeIamAccessDecision:
        check_config = self.iam_config.connection_access_check
        if not check_config.enabled:
            return NsRuntimeIamAccessDecision(
                allowed=True,
                effect="allow",
                reason="CONNECTION_ACCESS_CHECK_DISABLED",
                resource_type="ns_runtime_connection",
                resource_id=client_type,
                action_code="connect",
                trace_id=trace_id,
                raw={
                    "allowed": True,
                    "effect": "allow",
                    "reason": "CONNECTION_ACCESS_CHECK_DISABLED",
                    "trace_id": trace_id,
                },
            )

        template_values = {
            "runtime_id": self.runtime_config.runtime_id,
            "cluster_id": self.runtime_config.cluster_id,
            "mode": self.runtime_config.mode,
            "client_type": client_type,
            "client_id": client_id,
            "node_id": node_id,
            "node_group": node_group,
        }

        template = check_config.template

        context = self._render_template_mapping(
            template.context,
            template_values,
        )

        if extra_context:
            context.update(dict(extra_context))

        return await self.access_check(
            principal=principal,
            resource_type=self._render_template_text(template.resource_type, template_values),
            resource_id=self._render_template_text(template.resource_id, template_values),
            action_code=self._render_template_text(template.action_code, template_values),
            context=context,
            trace_id=trace_id,
        )

    async def _post_json(
            self,
            path: str,
            data: Mapping[str, Any],
            *,
            trace_id: str | None = None,
    ) -> dict[str, Any]:
        response = await self.http_client.post(
            self._build_url(path),
            json_data=dict(data),
            bearer_token=self.iam_config.internal_token,
            trace_id=trace_id,
            expected_statuses={
                200,
            },
        )

        response_data = response.json()
        if not isinstance(response_data, Mapping):
            raise NsRuntimeCodecError(
                "Runtime IAM response must be a JSON object.",
                details={
                    "path": path,
                    "status_code": response.status_code,
                    "actual_type": type(response_data).__name__,
                },
            )

        response_mapping = dict(response_data)

        if "success" in response_mapping or "data" in response_mapping or "code" in response_mapping:
            success = response_mapping.get("success")
            if success is not True:
                raise NsRuntimeCodecError(
                    "Runtime IAM response indicates failure.",
                    details={
                        "path": path,
                        "status_code": response.status_code,
                        "success": success,
                        "code": response_mapping.get("code"),
                        "error": response_mapping.get("error"),
                        "message": response_mapping.get("message"),
                        "details": response_mapping.get("details"),
                        "request_id": response_mapping.get("request_id"),
                    },
                )

            payload = response_mapping.get("data")
            if not isinstance(payload, Mapping):
                raise NsRuntimeCodecError(
                    "Runtime IAM response.data must be a JSON object.",
                    details={
                        "path": path,
                        "status_code": response.status_code,
                        "actual_type": type(payload).__name__,
                        "request_id": response_mapping.get("request_id"),
                    },
                )

            return dict(payload)

        return response_mapping

    def _build_url(self, path: str) -> str:
        base_url = self.iam_config.base_url.rstrip("/")
        normalized_path = path if path.startswith("/") else f"/{path}"
        return f"{base_url}{normalized_path}"

    def _handle_introspection_dependency_error(
            self,
            exc: NsDependencyError,
            *,
            trace_id: str | None,
    ) -> NsRuntimeIamIntrospectionResult:
        if self.iam_config.fail_policy == "fail_open":
            return NsRuntimeIamIntrospectionResult(
                active=False,
                reason="IAM_UNAVAILABLE",
                principal=None,
                user=None,
                raw={
                    "active": False,
                    "reason": "IAM_UNAVAILABLE",
                    "trace_id": trace_id,
                    "fail_policy": self.iam_config.fail_policy,
                    "error": exc.to_dict(),
                },
            )

        raise NsRuntimeAuthError(
            "Runtime IAM token introspection failed.",
            details={
                "runtime_id": self.runtime_config.runtime_id,
                "base_url": self.iam_config.base_url,
                "fail_policy": self.iam_config.fail_policy,
                "trace_id": trace_id,
                "error": exc.to_dict(),
            },
        ) from exc

    def _handle_access_check_dependency_error(
            self,
            exc: NsDependencyError,
            *,
            request_data: Mapping[str, Any],
            trace_id: str | None,
    ) -> NsRuntimeIamAccessDecision:
        if self.iam_config.fail_policy == "fail_open":
            return NsRuntimeIamAccessDecision(
                allowed=True,
                effect="allow",
                reason="IAM_UNAVAILABLE_FAIL_OPEN",
                resource_type=_normalize_optional_text(request_data.get("resource_type")),
                resource_id=_normalize_optional_text(request_data.get("resource_id")),
                action_code=_normalize_optional_text(request_data.get("action_code")),
                permission_code=_normalize_optional_text(request_data.get("permission_code")),
                filters={},
                hit_details={
                    "error": exc.to_dict(),
                },
                decision_chain=[
                    {
                        "source": "runtime_iam_adapter",
                        "effect": "allow",
                        "reason": "IAM_UNAVAILABLE_FAIL_OPEN",
                    },
                ],
                trace_id=trace_id,
                raw={
                    "allowed": True,
                    "effect": "allow",
                    "reason": "IAM_UNAVAILABLE_FAIL_OPEN",
                    "trace_id": trace_id,
                },
            )

        raise NsRuntimeAuthError(
            "Runtime IAM access check failed.",
            details={
                "runtime_id": self.runtime_config.runtime_id,
                "base_url": self.iam_config.base_url,
                "fail_policy": self.iam_config.fail_policy,
                "trace_id": trace_id,
                "resource_type": request_data.get("resource_type"),
                "resource_id": request_data.get("resource_id"),
                "action_code": request_data.get("action_code"),
                "error": exc.to_dict(),
            },
        ) from exc

    @staticmethod
    def _render_template_text(template: str, values: Mapping[str, Any]) -> str:
        result = str(template)

        for key, value in values.items():
            token = "{{ " + key + " }}"
            result = result.replace(token, "" if value is None else str(value))

        return result

    @classmethod
    def _render_template_mapping(cls, template: Mapping[str, Any], values: Mapping[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for key, value in template.items():
            if isinstance(value, str):
                result[key] = cls._render_template_text(value, values)
            elif isinstance(value, Mapping):
                result[key] = cls._render_template_mapping(value, values)
            elif isinstance(value, list):
                result[key] = [
                    cls._render_template_text(item, values) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                result[key] = value

        return result


def get_runtime_iam_adapter(runtime_config: NsRuntimeConfig | None = None) -> NsRuntimeIamAdapter:
    return NsRuntimeIamAdapter(
        runtime_config=runtime_config,
    )


def _ensure_mapping(value: Any, field_name: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise NsRuntimeAuthError(
            f"{field_name} must be a JSON object.",
            details={
                "field": field_name,
                "actual_type": type(value).__name__,
            },
        )

    return dict(value)


def _normalize_required_text(value: Any, field_name: str) -> str:
    normalized = str(value or "").strip()

    if not normalized:
        raise NsRuntimeAuthError(
            f"{field_name} is required.",
            details={
                "field": field_name,
            },
        )

    return normalized


def _normalize_optional_text(value: Any) -> str | None:
    if value is None:
        return None

    normalized = str(value).strip()
    return normalized or None


def _ensure_bool(value: Any, field_name: str) -> bool:
    if not isinstance(value, bool):
        raise NsRuntimeCodecError(
            f"{field_name} must be a boolean.",
            details={
                "field": field_name,
                "actual_type": type(value).__name__,
            },
        )

    return value
