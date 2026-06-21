# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.services import (
    DepartmentPermissionGrantService,
    RolePermissionGrantService,
    SubsidiaryPermissionGrantService,
    UserPermissionGrantService,
    UserRoleGrantService,
)
from ns_backend.iam.views import IamRequestViewSet

if TYPE_CHECKING:
    pass


def _get_operator_id(request) -> int | None:
    """Resolve current operator id from request."""
    return getattr(getattr(request, "current_user", None), "id", None)


def _get_operator(request):
    """Resolve current operator from request."""
    return getattr(request, "current_user", None)


class UserRoleGrantViewSet(IamRequestViewSet):
    async def bind_user_role(self, request, *args, **kwargs):
        result = await UserRoleGrantService.bind_user_role(
            data=request.data,
            operator=_get_operator(request),
            operator_id=_get_operator_id(request),
        )
        return self.success_response(result)

    async def unbind_user_role(self, request, *args, **kwargs):
        await UserRoleGrantService.unbind_user_role(data=request.data, operator=_get_operator(request))
        return self.success_response()


class RolePermissionGrantViewSet(IamRequestViewSet):
    async def grant_role_permission(self, request, *args, **kwargs):
        result = await RolePermissionGrantService.grant_role_permission(
            data=request.data,
            operator=_get_operator(request),
            operator_id=_get_operator_id(request),
        )
        return self.success_response(result)

    async def revoke_role_permission(self, request, *args, **kwargs):
        await RolePermissionGrantService.revoke_role_permission(data=request.data, operator=_get_operator(request))
        return self.success_response()


class UserPermissionGrantViewSet(IamRequestViewSet):
    async def grant_user_permission(self, request, *args, **kwargs):
        result = await UserPermissionGrantService.grant_user_permission(
            data=request.data,
            operator=_get_operator(request),
            operator_id=_get_operator_id(request),
        )
        return self.success_response(result)

    async def revoke_user_permission(self, request, *args, **kwargs):
        await UserPermissionGrantService.revoke_user_permission(data=request.data, operator=_get_operator(request))
        return self.success_response()


class DepartmentPermissionGrantViewSet(IamRequestViewSet):
    async def grant_department_permission(self, request, *args, **kwargs):
        result = await DepartmentPermissionGrantService.grant_department_permission(
            data=request.data,
            operator=_get_operator(request),
            operator_id=_get_operator_id(request),
        )
        return self.success_response(result)

    async def revoke_department_permission(self, request, *args, **kwargs):
        await DepartmentPermissionGrantService.revoke_department_permission(data=request.data, operator=_get_operator(request))
        return self.success_response()


class SubsidiaryPermissionGrantViewSet(IamRequestViewSet):
    async def grant_subsidiary_permission(self, request, *args, **kwargs):
        result = await SubsidiaryPermissionGrantService.grant_subsidiary_permission(
            data=request.data,
            operator=_get_operator(request),
            operator_id=_get_operator_id(request),
        )
        return self.success_response(result)

    async def revoke_subsidiary_permission(self, request, *args, **kwargs):
        await SubsidiaryPermissionGrantService.revoke_subsidiary_permission(data=request.data, operator=_get_operator(request))
        return self.success_response()
