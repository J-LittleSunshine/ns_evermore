# -*- coding: utf-8 -*-
from __future__ import annotations

from ns_backend.exceptions import BusinessError


class AuthRequestValidator:
    @staticmethod
    def validate_login_data(data) -> dict:
        username = data.get("username")
        password = data.get("password")

        if not isinstance(username, str) or not username.strip():
            raise BusinessError("username cannot be empty", 11001)

        if not isinstance(password, str) or not password:
            raise BusinessError("password cannot be empty", 11002)

        return {
            "username": username.strip(),
            "password": password,
            "device_name": data.get("device_name"),
            "device_type": data.get("device_type"),
            "fingerprint": data.get("fingerprint"),
            "os_name": data.get("os_name"),
            "browser_name": data.get("browser_name"),
        }

    @staticmethod
    def validate_refresh_token_data(data) -> str:
        refresh_token = data.get("refresh_token")

        if not isinstance(refresh_token, str) or not refresh_token:
            raise BusinessError("refresh_token cannot be empty", 11004)

        return refresh_token

    @staticmethod
    def validate_data_scope_codes(data) -> list[str]:
        permission_codes = data.get("permission_codes")

        if permission_codes is None:
            raise BusinessError("permission_codes cannot be empty", 12001)

        if not isinstance(permission_codes, list):
            raise BusinessError("permission_codes must be a list", 12002)

        clean_codes: list[str] = []
        for code in permission_codes:
            if not isinstance(code, str) or not code.strip():
                raise BusinessError("permission_code cannot be empty", 12001)
            clean_codes.append(code.strip())

        if len(clean_codes) > 100:
            raise BusinessError("permission_codes exceeds limit", 12004)

        return clean_codes

