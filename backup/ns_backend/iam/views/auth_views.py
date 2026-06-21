# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.backend.common.validators import AuthRequestValidator
from ns_backend.iam.services import AuthContextService, AuthService
from ns_backend.iam.views import IamRequestViewSet

if TYPE_CHECKING:
    pass


class AuthViewSet(IamRequestViewSet):
    audit_resource_type = "iam_auth"

    async def login(self, request, *args, **kwargs):
        result = await AuthService.login(data=request.data, request=request)
        request.current_user = result.user
        return self.success_response(result.data)

    async def refresh(self, request, *args, **kwargs):
        data = await AuthService.refresh(data=request.data)
        return self.success_response(data)

    async def refresh_token(self, request, *args, **kwargs):
        return await self.refresh(request, *args, **kwargs)

    async def logout(self, request, *args, **kwargs):
        data = await AuthService.logout(data=request.data, request=request)
        return self.success_response(data)

    async def profile(self, request, *args, **kwargs):
        user, _ = await AuthService.resolve_user_from_request(request)
        data = AuthContextService.build_profile(user)
        return self.success_response(data)

    async def current_user(self, request, *args, **kwargs):
        user, _ = await AuthService.resolve_user_from_request(request)
        return self.success_response(AuthService.build_current_user_payload(user))

    async def permissions(self, request, *args, **kwargs):
        user, _ = await AuthService.resolve_user_from_request(request)
        permission_codes = await AuthContextService.list_permission_codes(user)
        return self.success_response(
            {
                "permissions": permission_codes
            }
        )

    async def menus(self, request, *args, **kwargs):
        user, _ = await AuthService.resolve_user_from_request(request)
        menus = await AuthContextService.list_menu_tree(user)
        return self.success_response(
            {
                "menus": menus
            }
        )

    async def data_scopes(self, request, *args, **kwargs):
        user, _ = await AuthService.resolve_user_from_request(request)
        clean_codes = AuthRequestValidator.validate_data_scope_codes(request.data)
        items = await AuthContextService.list_data_scopes(user=user, permission_codes=clean_codes)
        return self.success_response(
            {
                "items": items
            }
        )
