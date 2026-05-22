# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from django.http import JsonResponse
from iam.services.audit import AuditService
from iam.schemas import TenantContext
from iam.policies.tenant import TenantPolicy
from iam.repositories.crud import CrudRepository
from iam.services.auth import VerifyService
from iam.services.permission import PermissionService
from iam.services.tenant import TenantService
from ns_backend.auth import AuthenticatedRequestViewSet
from ns_backend.exceptions import BusinessError
from ns_backend.exceptions import ValidateError
from ns_backend.logger import get_logger

if TYPE_CHECKING:
    pass

_logger = get_logger("iam.audit")


class IamRequestViewSet(AuthenticatedRequestViewSet):
    verify_service = VerifyService
    permission_service = PermissionService

    audit_enabled = True
    audit_resource_type: str | None = None
    audit_include_response_data = False
    audit_resource_id_fields = (
        "id",
        "user_id",
        "role_id",
        "permission_id",
        "company_id",
        "subsidiary_id",
        "department_id",
    )

    async def dispatch(self, request, *args, **kwargs):
        response = await super().dispatch(request, *args, **kwargs)  # noqa

        if self.audit_enabled:
            await self.record_operation_audit(request=request, response=response)

        return response

    def get_audit_action_name(self, request) -> str:
        action = getattr(self, "action", None)
        if action:
            return str(action)

        resolver_match = getattr(request, "resolver_match", None)
        url_name = getattr(resolver_match, "url_name", None)
        if url_name:
            return str(url_name)

        path = getattr(request, "path", None)
        if path:
            normalized_path = str(path).strip("/")
            if normalized_path:
                return normalized_path.replace("/", ":")

        return str(getattr(request, "method", "unknown")).lower()

    def get_audit_resource_type(self) -> str:
        if self.audit_resource_type:
            return self.audit_resource_type

        model_class = getattr(self, "model_class", None)
        if model_class is not None:
            return model_class._meta.db_table

        return self.__class__.__name__

    def get_audit_operation_type(self, request) -> str:
        resource_type = self.get_audit_resource_type()
        action = self.get_audit_action_name(request)
        return f"{resource_type}:{action}"

    @staticmethod
    def parse_response_payload(response) -> dict:
        if not isinstance(response, JsonResponse):
            return {}

        try:
            content = getattr(response, "content", b"")
            if not content:
                return {}
            parsed = json.loads(content.decode("utf-8"))
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}

    @staticmethod
    def get_response_code_and_msg(response_payload: dict) -> tuple[int, str | None]:
        raw_code = response_payload.get("code", 0)
        msg = response_payload.get("msg")

        try:
            code = int(raw_code)
        except (TypeError, ValueError):
            code = 50000

        return code, None if msg is None else str(msg)

    def get_audit_resource_id(self, request, response_payload: dict) -> int | None:
        response_data = response_payload.get("data")
        if isinstance(response_data, dict):
            value = response_data.get("id")
            try:
                return int(value)
            except (TypeError, ValueError):
                pass

        request_data = self.get_audit_request_data(request)
        if not isinstance(request_data, dict):
            return None

        for field in self.audit_resource_id_fields:
            value = request_data.get(field)
            try:
                return int(value)
            except (TypeError, ValueError):
                continue

        return None

    @staticmethod
    def get_audit_request_data(request) -> dict | None:
        try:
            data = request.data
        except Exception:
            return None

        if isinstance(data, dict):
            return dict(data)

        return {"raw": data}

    def get_audit_after_data(self, response_payload: dict) -> dict:
        code, msg = self.get_response_code_and_msg(response_payload)
        after_data: dict[str, Any] = {
            "code": code,
            "msg": msg,
        }

        if self.audit_include_response_data:
            after_data["data"] = response_payload.get("data")

        return after_data

    def get_audit_extra_data(self, request, response_payload: dict) -> dict:
        action = self.get_audit_action_name(request)
        code, msg = self.get_response_code_and_msg(response_payload)

        return {
            "view": self.__class__.__name__,
            "action": action,
            "required_permissions": list(getattr(self, "required_permissions", ()) or ()),
            "response_code": code,
            "response_msg": msg,
        }

    async def record_operation_audit(self, request, response) -> None:
        try:
            response_payload = self.parse_response_payload(response)
            code, msg = self.get_response_code_and_msg(response_payload)
            status = "SUCCESS" if code == 0 else "FAILED"

            event = AuditService.build_event_from_request(
                request=request,
                operation_type=self.get_audit_operation_type(request),
                resource_type=self.get_audit_resource_type(),
                resource_id=self.get_audit_resource_id(request, response_payload),
                request_data=self.get_audit_request_data(request),
                after_data=self.get_audit_after_data(response_payload),
                extra_data=self.get_audit_extra_data(request, response_payload),
                status=status,
                error_code=None if code == 0 else code,
                error_message=None if code == 0 else msg,
            )
            await AuditService.record_event(event)
        except Exception:
            _logger.exception("failed to record operation audit")


class BaseIamViewSet(IamRequestViewSet):
    model_class = None
    validator_class = None
    tenant_scope_field: str | None = None
    tenant_create_field: str | None = None
    enterprise_resource_required: bool = False

    list_fields: tuple[str, ...] = ()
    detail_fields: tuple[str, ...] = ()
    update_fields: tuple[str, ...] = ()

    async def list_item(self, request, *args, **kwargs):
        page = request.data.get("page", 1)
        page_size = request.data.get("page_size", 20)
        tenant_filter = self.get_tenant_filter(request)

        data = await CrudRepository.list_items(
            model_class=self.model_class,
            fields=self.list_fields,
            page=page,
            page_size=page_size,
            tenant_filter=tenant_filter,
        )

        return self.success_response(data)

    async def detail_item(self, request, *args, **kwargs):
        item_id = request.data.get("id")
        tenant_filter = self.get_tenant_filter(request)

        data = await CrudRepository.detail_item(
            model_class=self.model_class,
            item_id=item_id,
            fields=self.detail_fields,
            tenant_filter=tenant_filter,
        )

        return self.success_response(data)

    async def create_item(self, request, *args, **kwargs):
        data = self.validate_create_data(request.data)
        operator_id = self.get_operator_id(request)
        tenant_create_values = self.get_tenant_create_values(request)

        result = await CrudRepository.create_item_with_audit(
            model_class=self.model_class,
            data=data,
            operator_id=operator_id,
            tenant_create_values=tenant_create_values,
        )

        return self.success_response(result)

    async def update_item(self, request, *args, **kwargs):
        item_id = request.data.get("id")
        data = self.validate_update_data(request.data)
        operator_id = self.get_operator_id(request)
        tenant_filter = self.get_tenant_filter(request)

        await CrudRepository.update_item_with_audit(
            model_class=self.model_class,
            item_id=item_id,
            data=data,
            operator_id=operator_id,
            tenant_filter=tenant_filter,
        )

        return self.success_response()

    async def delete_item(self, request, *args, **kwargs):
        item_id = request.data.get("id")
        tenant_filter = self.get_tenant_filter(request)

        await CrudRepository.delete_item_by_id(
            model_class=self.model_class,
            item_id=item_id,
            tenant_filter=tenant_filter,
        )

        return self.success_response()

    def validate_create_data(self, data: dict[str, Any]) -> dict[str, Any]:
        if self.validator_class:
            return self.validator_class.validate_create(data)

        return data

    def validate_update_data(self, data: dict[str, Any]) -> dict[str, Any]:
        for field in data.keys():
            if field == "id":
                continue

            if field not in self.update_fields:
                raise ValidateError(f"Updating field is not allowed: {field}", 12005)

        if self.validator_class:
            return self.validator_class.validate_update(data)

        return {
            field: data[field]
            for field in self.update_fields
            if field in data
        }

    @staticmethod
    def get_operator_id(request) -> int | None:
        current_user = getattr(request, "current_user", None)
        return getattr(current_user, "id", None)

    @staticmethod
    def get_tenant_context(request) -> TenantContext | None:
        current_user = getattr(request, "current_user", None)

        if not current_user:
            return None

        return TenantService.from_user(current_user)

    def get_tenant_filter(self, request) -> dict[str, Any] | None:
        if self.tenant_scope_field is None:
            return None

        context = self.get_tenant_context(request)

        if context is None:
            return None

        if TenantPolicy.is_platform_admin(context):
            return None

        if self.enterprise_resource_required:
            TenantPolicy.ensure_enterprise_context(context)

        if TenantPolicy.is_enterprise_user(context):
            company_id = context.company_id

            if company_id is None:
                raise BusinessError("Enterprise user is not bound to a company", 14001)

            return {self.tenant_scope_field: company_id}

        raise BusinessError("Personal users cannot access enterprise organization resources", 14002)

    def get_tenant_create_values(self, request) -> dict[str, Any] | None:
        if self.tenant_create_field is None:
            return None

        context = self.get_tenant_context(request)

        if context is None:
            return None

        if TenantPolicy.is_platform_admin(context):
            return None

        if self.enterprise_resource_required:
            TenantPolicy.ensure_enterprise_context(context)

        if TenantPolicy.is_enterprise_user(context):
            company_id = context.company_id

            if company_id is None:
                raise BusinessError("Enterprise user is not bound to a company", 14001)

            return {self.tenant_create_field: company_id}

        raise BusinessError("Personal users cannot access enterprise organization resources", 14002)


