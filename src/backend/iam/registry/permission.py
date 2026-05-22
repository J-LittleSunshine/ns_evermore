# -*- coding: utf-8 -*-
from __future__ import annotations

from ns_common.error_codes import NsErrorCode
from iam.schemas import PermissionSpec
from ns_backend.exceptions import BusinessError


class PermissionRegistry:
    _items: list[PermissionSpec] = []
    _allowed_types = {"MENU", "ACTION", "DATA"}

    @classmethod
    def register(cls, spec: PermissionSpec) -> None:
        if not spec.code:
            raise BusinessError("Permission code is required", NsErrorCode.PERMISSION_CODE_REQUIRED)

        if not spec.name:
            raise BusinessError("Permission name is required", NsErrorCode.PERMISSION_NAME_REQUIRED)

        if spec.permission_type not in cls._allowed_types:
            raise BusinessError(f"Invalid permission type: {spec.permission_type}", NsErrorCode.PERMISSION_TYPE_INVALID)

        if any(item.code == spec.code for item in cls._items):
            raise BusinessError(f"Duplicate permission code: {spec.code}", NsErrorCode.PERMISSION_CODE_DUPLICATED)

        cls._items.append(spec)

    @classmethod
    def register_many(cls, specs: list[PermissionSpec] | tuple[PermissionSpec, ...]) -> None:
        for spec in specs:
            cls.register(spec)

    @classmethod
    def list_specs(cls) -> list[PermissionSpec]:
        return sorted(cls._items, key=lambda item: item.code)

    @classmethod
    def clear(cls) -> None:
        cls._items = []


__all__ = ["PermissionRegistry"]

