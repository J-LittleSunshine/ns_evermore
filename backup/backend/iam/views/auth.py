# -*- coding: utf-8 -*-
from __future__ import annotations

import ipaddress
from typing import TYPE_CHECKING

from django.conf import settings

from iam.services.auth_context import AuthContextService
from iam.services.auth import LoginService, LogoutService, RefreshService, RevokeService
from iam.validators.auth import AuthRequestValidator
from iam.views.base import IamRequestViewSet

if TYPE_CHECKING:
    pass


class AuthPublicViewSet(IamRequestViewSet):
    audit_resource_type = "iam_auth"
    authentication_required = False

    async def login(self, request, *args, **kwargs):
        validated_data = AuthRequestValidator.validate_login_data(request.data)

        data = await LoginService.execute(
            username=validated_data["username"],
            password=validated_data["password"],
            client_ip=self.get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            device_name=validated_data["device_name"],
            device_type=validated_data["device_type"],
            fingerprint_raw=validated_data["fingerprint"],
            os_name=validated_data["os_name"],
            browser_name=validated_data["browser_name"],
        )

        return self.success_response(data)

    async def refresh_token(self, request, *args, **kwargs):
        refresh_token = AuthRequestValidator.validate_refresh_token_data(request.data)

        data = await RefreshService.execute(refresh_token=refresh_token)

        return self.success_response(data)

    @staticmethod
    def get_client_ip(request):
        trust_xff = bool(getattr(settings, "TRUST_X_FORWARDED_FOR", False))

        if trust_xff:
            x_forwarded_for = request.headers.get("X-Forwarded-For")
            if x_forwarded_for:
                candidate = x_forwarded_for.split(",")[0].strip()
                try:
                    ipaddress.ip_address(candidate)
                    return candidate
                except ValueError:
                    pass

        remote_addr = request.META.get("REMOTE_ADDR")
        if not remote_addr:
            return None

        try:
            ipaddress.ip_address(remote_addr)
            return remote_addr
        except ValueError:
            return None


class AuthPrivateViewSet(IamRequestViewSet):
    audit_resource_type = "iam_auth"
    authentication_required = True

    async def logout(self, request, *args, **kwargs):
        current_user = request.current_user
        access_token = self.get_bearer_token_from_request(request)
        refresh_token = request.data.get("refresh_token")

        if not access_token:
            return self.failed_response("access_token cannot be empty", 11004)

        access_revoked = await RevokeService.revoke_access_token(access_token)
        refresh_revoked = False

        if refresh_token:
            refresh_revoked = await LogoutService.execute(
                refresh_token=refresh_token,
                current_user_id=current_user.id,
            )

        return self.success_response({
            "success": access_revoked or refresh_revoked,
            "access_revoked": access_revoked,
            "refresh_revoked": refresh_revoked,
        })

    async def current_user(self, request, *args, **kwargs):
        user = request.current_user

        if not user:
            return self.failed_response("User is not logged in or session has expired", 11007)

        return self.success_response({
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "email": user.email,
            "phone": user.phone,
            "user_type": user.user_type,
            "company_id": user.company_id,
            "subsidiary_id": user.subsidiary_id,
            "department_id": user.department_id,
            "is_active": user.is_active,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        })

    async def profile(self, request, *args, **kwargs):
        user = request.current_user

        if not user:
            return self.failed_response("User is not logged in or session has expired", 11007)

        data = AuthContextService.build_profile(user)
        return self.success_response(data)

    async def permissions(self, request, *args, **kwargs):
        user = request.current_user

        if not user:
            return self.failed_response("User is not logged in or session has expired", 11007)

        permission_codes = await AuthContextService.list_permission_codes(user)
        return self.success_response({
            "permissions": permission_codes,
        })

    async def menus(self, request, *args, **kwargs):
        user = request.current_user

        if not user:
            return self.failed_response("User is not logged in or session has expired", 11007)

        menus = await AuthContextService.list_menu_tree(user)
        return self.success_response({
            "menus": menus,
        })

    async def data_scopes(self, request, *args, **kwargs):
        user = request.current_user

        if not user:
            return self.failed_response("User is not logged in or session has expired", 11007)

        clean_codes = AuthRequestValidator.validate_data_scope_codes(request.data)

        items = await AuthContextService.list_data_scopes(
            user=user,
            permission_codes=clean_codes,
        )
        return self.success_response({
            "items": items,
        })

