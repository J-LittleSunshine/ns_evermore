# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_common.error_codes import NsErrorCode
from . import IamRequestViewSet
from ..errors import IamDomainError
from ..models import (
    IamUserRole,
    IamPermission,
    IamRolePermission,
    IamUserPermission,
    IamDepartmentPermission,
    IamSubsidiaryPermission
)
from ..policies import DataScopePolicy
from ..validators import (
    UserRoleValidator,
    RolePermissionValidator,
    UserPermissionValidator,
    DepartmentPermissionValidator,
    SubsidiaryPermissionValidator
)
from ...backend.common import CrudRepository
from ...backend.exceptions import BusinessError

if TYPE_CHECKING:
    pass


def _to_positive_int(value: Any, field_name: str) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise BusinessError(f"{field_name} is invalid", NsErrorCode.INVALID_VALUE) from exc

    if parsed <= 0:
        raise BusinessError(f"{field_name} is invalid", NsErrorCode.INVALID_VALUE)
    return parsed


def _raise_business_from_domain_error(exc: IamDomainError) -> None:
    raise BusinessError(exc.message, exc.code, exc.data) from exc


class UserRoleGrantViewSet(IamRequestViewSet):
    async def bind_user_role(self, request, *args, **kwargs):
        data = UserRoleValidator.validate_create(request.data)
        user_id = _to_positive_int(data.get("user_id"), "user_id")
        role_id = _to_positive_int(data.get("role_id"), "role_id")

        existed = await IamUserRole.objects.filter(user_id=user_id, role_id=role_id).afirst()
        if existed:
            return self.success_response({"id": existed.id})

        operator = getattr(getattr(request, "current_user", None), "id", None)
        result = await CrudRepository.create_item_with_audit(
            model_class=IamUserRole,
            data={"user_id": user_id, "role_id": role_id},
            operator_id=operator,
        )
        return self.success_response(result)

    async def unbind_user_role(self, request, *args, **kwargs):
        user_id = _to_positive_int(request.data.get("user_id"), "user_id")
        role_id = _to_positive_int(request.data.get("role_id"), "role_id")

        item = await IamUserRole.objects.filter(user_id=user_id, role_id=role_id).afirst()
        if item:
            await CrudRepository.delete_item(item)
        return self.success_response()


class RolePermissionGrantViewSet(IamRequestViewSet):
    async def grant_role_permission(self, request, *args, **kwargs):
        data = RolePermissionValidator.validate_create(request.data)
        role_id = _to_positive_int(data.get("role_id"), "role_id")
        permission_id = _to_positive_int(data.get("permission_id"), "permission_id")
        data_scope = data.get("data_scope")

        existed = await IamRolePermission.objects.filter(role_id=role_id, permission_id=permission_id).afirst()
        if existed:
            return self.success_response({"id": existed.id})

        permission = await IamPermission.objects.filter(id=permission_id).afirst()
        try:
            DataScopePolicy.ensure_grant_data_scope_by_permission_type(
                permission_type=getattr(permission, "permission_type", None),
                data_scope=data_scope,
                role_permission=True,
            )
        except IamDomainError as exc:
            _raise_business_from_domain_error(exc)

        operator = getattr(getattr(request, "current_user", None), "id", None)
        result = await CrudRepository.create_item_with_audit(
            model_class=IamRolePermission,
            data={
                "role_id": role_id,
                "permission_id": permission_id,
                "data_scope": data_scope,
                "granted_by_id": operator,
                "expired_at": data.get("expired_at"),
            },
            operator_id=operator,
        )
        return self.success_response(result)

    async def revoke_role_permission(self, request, *args, **kwargs):
        role_id = _to_positive_int(request.data.get("role_id"), "role_id")
        permission_id = _to_positive_int(request.data.get("permission_id"), "permission_id")

        item = await IamRolePermission.objects.filter(role_id=role_id, permission_id=permission_id).afirst()
        if item:
            await CrudRepository.delete_item(item)
        return self.success_response()


class UserPermissionGrantViewSet(IamRequestViewSet):
    async def grant_user_permission(self, request, *args, **kwargs):
        data = UserPermissionValidator.validate_create(request.data)
        user_id = _to_positive_int(data.get("user_id"), "user_id")
        permission_id = _to_positive_int(data.get("permission_id"), "permission_id")
        effect = data.get("effect")
        data_scope = data.get("data_scope")

        existed = await IamUserPermission.objects.filter(user_id=user_id, permission_id=permission_id).afirst()
        if existed:
            return self.success_response({"id": existed.id})

        permission = await IamPermission.objects.filter(id=permission_id).afirst()
        try:
            DataScopePolicy.ensure_grant_data_scope_by_permission_type(
                permission_type=getattr(permission, "permission_type", None),
                data_scope=data_scope,
                effect=effect,
                role_permission=False,
            )
        except IamDomainError as exc:
            _raise_business_from_domain_error(exc)

        operator = getattr(getattr(request, "current_user", None), "id", None)
        result = await CrudRepository.create_item_with_audit(
            model_class=IamUserPermission,
            data={
                "user_id": user_id,
                "permission_id": permission_id,
                "effect": effect,
                "data_scope": data_scope,
                "granted_by_id": operator,
                "expired_at": data.get("expired_at"),
            },
            operator_id=operator,
        )
        return self.success_response(result)

    async def revoke_user_permission(self, request, *args, **kwargs):
        user_id = _to_positive_int(request.data.get("user_id"), "user_id")
        permission_id = _to_positive_int(request.data.get("permission_id"), "permission_id")

        item = await IamUserPermission.objects.filter(user_id=user_id, permission_id=permission_id).afirst()
        if item:
            await CrudRepository.delete_item(item)
        return self.success_response()


class DepartmentPermissionGrantViewSet(IamRequestViewSet):
    async def grant_department_permission(self, request, *args, **kwargs):
        data = DepartmentPermissionValidator.validate_create(request.data)
        department_id = _to_positive_int(data.get("department_id"), "department_id")
        permission_id = _to_positive_int(data.get("permission_id"), "permission_id")
        effect = data.get("effect")
        data_scope = data.get("data_scope")

        existed = await IamDepartmentPermission.objects.filter(department_id=department_id, permission_id=permission_id).afirst()
        if existed:
            return self.success_response({"id": existed.id})

        permission = await IamPermission.objects.filter(id=permission_id).afirst()
        try:
            DataScopePolicy.ensure_grant_data_scope_by_permission_type(
                permission_type=getattr(permission, "permission_type", None),
                data_scope=data_scope,
                effect=effect,
                role_permission=False,
            )
        except IamDomainError as exc:
            _raise_business_from_domain_error(exc)

        operator = getattr(getattr(request, "current_user", None), "id", None)
        result = await CrudRepository.create_item_with_audit(
            model_class=IamDepartmentPermission,
            data={
                "department_id": department_id,
                "permission_id": permission_id,
                "effect": effect,
                "data_scope": data_scope,
                "granted_by_id": operator,
                "expired_at": data.get("expired_at"),
            },
            operator_id=operator,
        )
        return self.success_response(result)

    async def revoke_department_permission(self, request, *args, **kwargs):
        department_id = _to_positive_int(request.data.get("department_id"), "department_id")
        permission_id = _to_positive_int(request.data.get("permission_id"), "permission_id")

        item = await IamDepartmentPermission.objects.filter(department_id=department_id, permission_id=permission_id).afirst()
        if item:
            await CrudRepository.delete_item(item)
        return self.success_response()


class SubsidiaryPermissionGrantViewSet(IamRequestViewSet):
    async def grant_subsidiary_permission(self, request, *args, **kwargs):
        data = SubsidiaryPermissionValidator.validate_create(request.data)
        subsidiary_id = _to_positive_int(data.get("subsidiary_id"), "subsidiary_id")
        permission_id = _to_positive_int(data.get("permission_id"), "permission_id")
        effect = data.get("effect")
        data_scope = data.get("data_scope")

        existed = await IamSubsidiaryPermission.objects.filter(subsidiary_id=subsidiary_id, permission_id=permission_id).afirst()
        if existed:
            return self.success_response({"id": existed.id})

        permission = await IamPermission.objects.filter(id=permission_id).afirst()
        try:
            DataScopePolicy.ensure_grant_data_scope_by_permission_type(
                permission_type=getattr(permission, "permission_type", None),
                data_scope=data_scope,
                effect=effect,
                role_permission=False,
            )
        except IamDomainError as exc:
            _raise_business_from_domain_error(exc)

        operator = getattr(getattr(request, "current_user", None), "id", None)
        result = await CrudRepository.create_item_with_audit(
            model_class=IamSubsidiaryPermission,
            data={
                "subsidiary_id": subsidiary_id,
                "permission_id": permission_id,
                "effect": effect,
                "data_scope": data_scope,
                "granted_by_id": operator,
                "expired_at": data.get("expired_at"),
            },
            operator_id=operator,
        )
        return self.success_response(result)

    async def revoke_subsidiary_permission(self, request, *args, **kwargs):
        subsidiary_id = _to_positive_int(request.data.get("subsidiary_id"), "subsidiary_id")
        permission_id = _to_positive_int(request.data.get("permission_id"), "permission_id")

        item = await IamSubsidiaryPermission.objects.filter(subsidiary_id=subsidiary_id, permission_id=permission_id).afirst()
        if item:
            await CrudRepository.delete_item(item)
        return self.success_response()
