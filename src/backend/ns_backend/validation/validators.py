# -*- coding: utf-8 -*-
from __future__ import annotations

from ns_backend.exceptions import ValidateError


class BaseValidator:
    required_fields: tuple[str, ...] = ()
    allowed_fields: tuple[str, ...] = ()
    enum_fields: dict[str, set] = {}

    @classmethod
    def validate_create(cls, data: dict) -> dict:
        cls._check_required(data)
        cls._check_allowed(data)
        cls._check_enum(data)
        return cls._pick_allowed(data)

    @classmethod
    def validate_update(cls, data: dict) -> dict:
        if "id" not in data:
            raise ValidateError("id 不能为空", 10001)

        update_fields = [field for field in data if field != "id"]

        if not update_fields:
            raise ValidateError("没有需要更新的字段", 12001)

        cls._check_allowed(data)
        cls._check_enum(data)

        return {
            field: value
            for field, value in data.items()
            if field in cls.allowed_fields
        }

    @classmethod
    def _check_required(cls, data: dict) -> None:
        for field in cls.required_fields:
            if field not in data:
                raise ValidateError(f"{field} 不能为空", 12002)

            value = data[field]

            if value is None:
                raise ValidateError(f"{field} 不能为空", 12002)

            if isinstance(value, str) and not value.strip():
                raise ValidateError(f"{field} 不能为空", 12002)

    @classmethod
    def _check_allowed(cls, data: dict) -> None:
        allowed = set(cls.allowed_fields) | {"id"}

        for field in data.keys():
            if field not in allowed:
                raise ValidateError(f"不允许字段：{field}", 12003)

    @classmethod
    def _check_enum(cls, data: dict) -> None:
        for field, enum_values in cls.enum_fields.items():
            if field not in data:
                continue

            if data[field] not in enum_values:
                raise ValidateError(
                    f"{field} 字段值非法，允许值：{sorted(enum_values)}",
                    12004,
                )

    @classmethod
    def _pick_allowed(cls, data: dict) -> dict:
        return {
            field: data[field]
            for field in cls.allowed_fields
            if field in data
        }

