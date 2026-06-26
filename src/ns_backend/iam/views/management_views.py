# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    ClassVar,
    TYPE_CHECKING,
)

from backend.common import NsViewSet
from ns_backend.iam.errors import (
    IamManagementAccessDeniedError,
    IamManagementRequestInvalidError,
)
from ns_backend.iam.services import (
    AuthService,
    CompanyManagementService,
    DepartmentManagementService,
    DepartmentPermissionManagementService,
    IamManagementService,
    OperationAuditService,
    PermissionManagementService,
    PermissionService,
    PolicyManagementService,
    PolicyRuleManagementService,
    ResourceAclManagementService,
    ResourceActionManagementService,
    ResourceManagementService,
    ResourceRelationManagementService,
    RoleManagementService,
    RolePermissionManagementService,
    SubsidiaryManagementService,
    SubsidiaryPermissionManagementService,
    UserManagementService,
    UserPermissionManagementService,
    UserRoleManagementService
)

if TYPE_CHECKING:
    from rest_framework.request import Request


class IamManagementViewSet(NsViewSet):
    logger_name = "ns_backend.iam.management.api"
    service_class: ClassVar[type[IamManagementService] | None] = None

    allowed_actions = {
        "list",
        "get_detail",
        "create",
        "update",
        "delete",
    }

    required_permissions: ClassVar[dict[str, tuple[str, ...]]] = {}
    audit_resource_type: ClassVar[str | None] = None

    async def list(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        operator = await self.get_operator(request)

        return await self.get_service_class().list_items(
            data=self.get_request_data(request),
            operator=operator,
        )

    async def get_detail(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        operator = await self.get_operator(request)

        return await self.get_service_class().detail_item(
            data=self.get_request_data(request),
            operator=operator,
        )

    async def create(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.execute_with_operation_audit(
            request=request,
            operation_type="create",
            handler=lambda operator, data: self.get_service_class().create_item(
                data=data,
                operator=operator,
            ),
        )

    async def update(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.execute_with_operation_audit(
            request=request,
            operation_type="update",
            handler=lambda operator, data: self.get_service_class().update_item(
                data=data,
                operator=operator,
            ),
        )

    async def delete(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.execute_with_operation_audit(
            request=request,
            operation_type="delete",
            handler=lambda operator, data: self.get_service_class().delete_item(
                data=data,
                operator=operator,
            ),
        )

    async def execute_with_operation_audit(self, *, request: "Request", operation_type: str, handler: Any) -> dict[str, Any]:
        request_data = self.get_request_data(request)
        operator = None
        before_data = None

        resource_type = self.resolve_operation_audit_resource_type()
        request_resource_id = OperationAuditService.extract_resource_id(
            request_data=request_data,
        )

        try:
            operator = await self.get_operator(request)

            before_data = await self.get_operation_audit_before_data(
                operator=operator,
                request_data=request_data,
                operation_type=operation_type,
            )

            result = await handler(
                operator,
                request_data,
            )

            await OperationAuditService.record_safe(
                operator=operator,
                operation_type=operation_type,
                resource_type=resource_type,
                request=request,
                request_data=request_data,
                before_data=before_data,
                after_data=result if isinstance(result, dict) else None,
                status=OperationAuditService.STATUS_SUCCESS,
                resource_id=OperationAuditService.extract_resource_id(
                    request_data=request_data,
                    result_data=result if isinstance(result, dict) else None,
                ),
                company_id=self.extract_company_id(
                    operator=operator,
                    request_data=request_data,
                    result_data=result if isinstance(result, dict) else None,
                    before_data=before_data,
                ),
            )

            return result

        except Exception as exc:
            await OperationAuditService.record_safe(
                operator=operator,
                operation_type=operation_type,
                resource_type=resource_type,
                request=request,
                request_data=request_data,
                before_data=before_data,
                after_data=None,
                status=OperationAuditService.STATUS_FAILED,
                error=exc,
                resource_id=request_resource_id,
                company_id=self.extract_company_id(
                    operator=operator,
                    request_data=request_data,
                    result_data=None,
                    before_data=before_data,
                ),
            )

            raise

    async def get_operation_audit_before_data(self, *, operator: Any, request_data: dict[str, Any], operation_type: str) -> dict[str, Any] | None:
        if operation_type not in (
                "update",
                "delete",
                "publish",
                "disable",
                "reset_password",
        ):
            return None

        item_id = OperationAuditService.extract_resource_id(
            request_data=request_data,
        )

        if item_id is None:
            return None

        service_class = self.get_service_class()
        model_class = getattr(service_class, "model_class", None)
        detail_fields = getattr(service_class, "detail_fields", ())

        if model_class is None or not detail_fields:
            return None

        try:
            await service_class.ensure_item_accessible(
                item_id=item_id,
                operator=operator,
            )

            return await service_class.repository_class.detail_item(
                model_class=model_class,
                item_id=item_id,
                fields=detail_fields,
            )
        except Exception:
            return None

    def resolve_operation_audit_resource_type(self) -> str:
        if self.audit_resource_type:
            return self.audit_resource_type

        service_class = self.get_service_class()
        model_class = getattr(service_class, "model_class", None)

        if model_class is not None:
            return str(model_class._meta.db_table).strip().lower()[:64]  # noqa

        return self.__class__.__name__.replace("ViewSet", "").lower()[:64]

    @staticmethod
    def extract_company_id(*, operator: Any | None, request_data: dict[str, Any] | None, result_data: dict[str, Any] | None, before_data: dict[str, Any] | None) -> int | None:
        for source in (
                result_data,
                before_data,
                request_data,
        ):
            if not isinstance(source, dict):
                continue

            value = source.get("company_id")
            if value in (None, ""):
                continue

            try:
                parsed = int(value)
            except (TypeError, ValueError):
                continue

            if parsed > 0:
                return parsed

        operator_company_id = getattr(operator, "company_id", None)
        if operator_company_id in (None, ""):
            return None

        try:
            parsed_operator_company_id = int(operator_company_id)
        except (TypeError, ValueError):
            return None

        return parsed_operator_company_id if parsed_operator_company_id > 0 else None

    async def get_operator(self, request: "Request") -> Any:
        user, _ = await AuthService.resolve_user_from_request(request)
        self.set_current_user(user)

        await self.enforce_required_permissions(
            operator=user,
        )

        return user

    async def enforce_required_permissions(self, *, operator: Any) -> None:
        action_name = str(getattr(self, "action", "") or "").strip()
        permissions = self.required_permissions.get(action_name, ())

        if not permissions:
            return

        if bool(getattr(operator, "is_superuser", False)):
            return

        for permission_code in permissions:
            if await PermissionService.has_permission(operator, permission_code):
                return

        raise IamManagementAccessDeniedError(
            details={
                "action": action_name,
                "required_permissions": list(permissions),
                "view_set": self.__class__.__name__,
            },
        )

    @classmethod
    def get_service_class(cls) -> type[IamManagementService]:
        if cls.service_class is None:
            raise IamManagementRequestInvalidError(
                "service_class is not configured.",
                details={
                    "view_set": cls.__name__,
                },
            )

        return cls.service_class


class CompanyViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.company.api"
    service_class = CompanyManagementService

    allowed_actions = IamManagementViewSet.allowed_actions | {
        "tree",
        "org_tree",
    }

    required_permissions = {
        "list": ("iam:company:read",),
        "get_detail": ("iam:company:read",),
        "create": ("iam:company:create",),
        "update": ("iam:company:update",),
        "delete": ("iam:company:delete",),
        "tree": ("iam:company:read",),
        "org_tree": ("iam:company:read",),
    }

    async def tree(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        operator = await self.get_operator(request)

        # noinspection PyUnresolvedReferences
        return await self.get_service_class().tree_items(
            data=self.get_request_data(request),
            operator=operator,
        )

    async def org_tree(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        operator = await self.get_operator(request)

        # noinspection PyUnresolvedReferences
        return await self.get_service_class().org_tree_items(
            data=self.get_request_data(request),
            operator=operator,
        )


class SubsidiaryViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.subsidiary.api"
    service_class = SubsidiaryManagementService

    allowed_actions = IamManagementViewSet.allowed_actions | {
        "tree",
    }

    required_permissions = {
        "list": ("iam:subsidiary:read",),
        "get_detail": ("iam:subsidiary:read",),
        "create": ("iam:subsidiary:create",),
        "update": ("iam:subsidiary:update",),
        "delete": ("iam:subsidiary:delete",),
        "tree": ("iam:subsidiary:read",),
    }

    async def tree(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        operator = await self.get_operator(request)

        # noinspection PyUnresolvedReferences
        return await self.get_service_class().tree_items(
            data=self.get_request_data(request),
            operator=operator,
        )


class DepartmentViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.department.api"
    service_class = DepartmentManagementService

    allowed_actions = IamManagementViewSet.allowed_actions | {
        "tree",
    }

    required_permissions = {
        "list": ("iam:department:read",),
        "get_detail": ("iam:department:read",),
        "create": ("iam:department:create",),
        "update": ("iam:department:update",),
        "delete": ("iam:department:delete",),
        "tree": ("iam:department:read",),
    }

    async def tree(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        operator = await self.get_operator(request)

        # noinspection PyUnresolvedReferences
        return await self.get_service_class().tree_items(
            data=self.get_request_data(request),
            operator=operator,
        )


class PermissionViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.permission.api"
    service_class = PermissionManagementService

    allowed_actions = IamManagementViewSet.allowed_actions | {
        "tree",
        "menu_tree",
        "action_list",
        "data_list",
    }

    required_permissions = {
        "list": ("iam:permission:read",),
        "get_detail": ("iam:permission:read",),
        "create": ("iam:permission:create",),
        "update": ("iam:permission:update",),
        "delete": ("iam:permission:delete",),
        "tree": ("iam:permission:read",),
        "menu_tree": ("iam:permission:read",),
        "action_list": ("iam:permission:read",),
        "data_list": ("iam:permission:read",),
    }

    async def tree(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        operator = await self.get_operator(request)

        # noinspection PyUnresolvedReferences
        return await self.get_service_class().tree_items(
            data=self.get_request_data(request),
            operator=operator,
        )

    async def menu_tree(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        operator = await self.get_operator(request)

        # noinspection PyUnresolvedReferences
        return await self.get_service_class().menu_tree_items(
            data=self.get_request_data(request),
            operator=operator,
        )

    async def action_list(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        operator = await self.get_operator(request)

        # noinspection PyUnresolvedReferences
        return await self.get_service_class().action_items(
            data=self.get_request_data(request),
            operator=operator,
        )

    async def data_list(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        operator = await self.get_operator(request)

        # noinspection PyUnresolvedReferences
        return await self.get_service_class().data_items(
            data=self.get_request_data(request),
            operator=operator,
        )


class PolicyViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.policy.api"
    service_class = PolicyManagementService

    allowed_actions = {
        "list",
        "get_detail",
        "create",
        "update",
        "delete",
        "publish",
        "disable",
    }

    required_permissions = {
        "list": ("iam:policy:read",),
        "get_detail": ("iam:policy:read",),
        "create": ("iam:policy:create",),
        "update": ("iam:policy:update",),
        "delete": ("iam:policy:delete",),
        "publish": ("iam:policy:publish",),
        "disable": ("iam:policy:disable",),
    }

    async def publish(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.execute_with_operation_audit(
            request=request,
            operation_type="publish",
            handler=lambda operator, data: self.get_service_class().publish_item(
                data=data,
                operator=operator,
            ),
        )

    async def disable(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.execute_with_operation_audit(
            request=request,
            operation_type="disable",
            handler=lambda operator, data: self.get_service_class().disable_item(
                data=data,
                operator=operator,
            ),
        )


class PolicyRuleViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.policy_rule.api"
    service_class = PolicyRuleManagementService

    required_permissions = {
        "list": ("iam:policy_rule:read",),
        "get_detail": ("iam:policy_rule:read",),
        "create": ("iam:policy_rule:create",),
        "update": ("iam:policy_rule:update",),
        "delete": ("iam:policy_rule:delete",),
    }


class ResourceViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.resource.api"
    service_class = ResourceManagementService

    required_permissions = {
        "list": ("iam:resource:read",),
        "get_detail": ("iam:resource:read",),
        "create": ("iam:resource:create",),
        "update": ("iam:resource:update",),
        "delete": ("iam:resource:delete",),
    }


class ResourceActionViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.resource_action.api"
    service_class = ResourceActionManagementService

    required_permissions = {
        "list": ("iam:resource_action:read",),
        "get_detail": ("iam:resource_action:read",),
        "create": ("iam:resource_action:create",),
        "update": ("iam:resource_action:update",),
        "delete": ("iam:resource_action:delete",),
    }


class ResourceAclViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.resource_acl.api"
    service_class = ResourceAclManagementService

    allowed_actions = {
        "list",
        "create",
        "delete",
    }

    required_permissions = {
        "list": ("iam:resource_acl:read",),
        "create": ("iam:resource_acl:create",),
        "delete": ("iam:resource_acl:delete",),
    }


class ResourceRelationViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.resource_relation.api"
    service_class = ResourceRelationManagementService

    allowed_actions = {
        "list",
        "create",
        "delete",
    }

    required_permissions = {
        "list": ("iam:resource_relation:read",),
        "create": ("iam:resource_relation:create",),
        "delete": ("iam:resource_relation:delete",),
    }


class RoleViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.role.api"
    service_class = RoleManagementService

    required_permissions = {
        "list": ("iam:role:read",),
        "get_detail": ("iam:role:read",),
        "create": ("iam:role:create",),
        "update": ("iam:role:update",),
        "delete": ("iam:role:delete",),
    }


class UserViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.user.api"
    service_class = UserManagementService

    allowed_actions = IamManagementViewSet.allowed_actions | {
        "reset_password",
    }

    required_permissions = {
        "list": ("iam:user:read",),
        "get_detail": ("iam:user:read",),
        "create": ("iam:user:create",),
        "update": ("iam:user:update",),
        "delete": ("iam:user:delete",),
        "reset_password": ("iam:user:reset_password",),
    }

    async def reset_password(self, request: "Request", *args: Any, **kwargs: Any) -> dict[str, Any]:
        return await self.execute_with_operation_audit(
            request=request,
            operation_type="reset_password",
            handler=lambda operator, data: self.get_service_class().reset_password(
                data=data,
                operator=operator,
            ),
        )

class UserRoleViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.user_role.api"
    service_class = UserRoleManagementService

    allowed_actions = {
        "list",
        "create",
        "delete",
    }

    required_permissions = {
        "list": ("iam:user_role:read",),
        "create": ("iam:user_role:create",),
        "delete": ("iam:user_role:delete",),
    }


class RolePermissionViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.role_permission.api"
    service_class = RolePermissionManagementService

    allowed_actions = {
        "list",
        "create",
        "delete",
    }

    required_permissions = {
        "list": ("iam:role_permission:read",),
        "create": ("iam:role_permission:create",),
        "delete": ("iam:role_permission:delete",),
    }


class UserPermissionViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.user_permission.api"
    service_class = UserPermissionManagementService

    allowed_actions = {
        "list",
        "create",
        "delete",
    }

    required_permissions = {
        "list": ("iam:user_permission:read",),
        "create": ("iam:user_permission:create",),
        "delete": ("iam:user_permission:delete",),
    }


class DepartmentPermissionViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.department_permission.api"
    service_class = DepartmentPermissionManagementService

    allowed_actions = {
        "list",
        "create",
        "delete",
    }

    required_permissions = {
        "list": ("iam:department_permission:read",),
        "create": ("iam:department_permission:create",),
        "delete": ("iam:department_permission:delete",),
    }


class SubsidiaryPermissionViewSet(IamManagementViewSet):
    logger_name = "ns_backend.iam.subsidiary_permission.api"
    service_class = SubsidiaryPermissionManagementService

    allowed_actions = {
        "list",
        "create",
        "delete",
    }

    required_permissions = {
        "list": ("iam:subsidiary_permission:read",),
        "create": ("iam:subsidiary_permission:create",),
        "delete": ("iam:subsidiary_permission:delete",),
    }
