# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_common.error_codes import NsErrorCode

from ..exceptions import ValidateError, BusinessError

if TYPE_CHECKING:
    pass


class BaseValidator:
    required_fields: tuple[str, ...] = ()
    allowed_fields: tuple[str, ...] = ()
    enum_fields: dict[str, tuple[Any, ...]] = {}

    @classmethod
    def validate_create(cls, data: dict[str, Any]) -> dict[str, Any]:
        cls._check_required(data)
        cls._check_allowed(data)
        cls._check_enum(data)
        return cls._pick_allowed(data)

    @classmethod
    def validate_update(cls, data: dict[str, Any]) -> dict[str, Any]:
        cls._check_allowed(data)
        cls._check_enum(data)
        picked_data = cls._pick_allowed(data)
        if not picked_data:
            raise ValidateError("No fields to update", NsErrorCode.INVALID_VALUE)
        return picked_data

    @classmethod
    def _check_required(cls, data: dict[str, Any]) -> None:
        for field in cls.required_fields:
            value = data.get(field)
            if value is None or value == "":
                raise ValidateError(f"{field} cannot be empty", NsErrorCode.INVALID_VALUE)

    @classmethod
    def _check_allowed(cls, data: dict[str, Any]) -> None:
        if not cls.allowed_fields:
            return
        for field in data.keys():
            if field in ("id",):
                continue
            if field not in cls.allowed_fields:
                raise ValidateError(f"Disallowed field: {field}", NsErrorCode.UPDATE_FIELD_NOT_ALLOWED)

    @classmethod
    def _check_enum(cls, data: dict[str, Any]) -> None:
        for field, values in cls.enum_fields.items():
            if field not in data:
                continue
            if data[field] not in values:
                raise ValidateError(f"{field} has invalid value, allowed values: {', '.join(map(str, values))}", NsErrorCode.INVALID_VALUE)

    @classmethod
    def _pick_allowed(cls, data: dict[str, Any]) -> dict[str, Any]:
        if not cls.allowed_fields:
            return data
        return {field: data[field] for field in cls.allowed_fields if field in data}

class AuthRequestValidator:
    @staticmethod
    def validate_login_data(data) -> dict:
        username = data.get("username")
        password = data.get("password")

        if not isinstance(username, str) or not username.strip():
            raise BusinessError("username cannot be empty", NsErrorCode.USERNAME_EMPTY)

        if not isinstance(password, str) or not password:
            raise BusinessError("password cannot be empty", NsErrorCode.PASSWORD_EMPTY)

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
    def validate_data_scope_codes(data) -> list[str]:
        permission_codes = data.get("permission_codes")

        if permission_codes is None:
            raise BusinessError("permission_codes cannot be empty", NsErrorCode.PERMISSION_CODES_EMPTY)

        if not isinstance(permission_codes, list):
            raise BusinessError("permission_codes must be a list", NsErrorCode.PERMISSION_CODES_TYPE_INVALID)

        clean_codes: list[str] = []
        for code in permission_codes:
            if not isinstance(code, str) or not code.strip():
                raise BusinessError("permission_code cannot be empty", NsErrorCode.PERMISSION_CODE_EMPTY)
            clean_codes.append(code.strip())

        if len(clean_codes) > 100:
            raise BusinessError("permission_codes exceeds limit", NsErrorCode.PERMISSION_CODES_EXCEEDS_LIMIT)

        return clean_codes
