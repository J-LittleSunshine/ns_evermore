# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Protocol

from iam.schemas.permission import PermissionSpec


class PermissionProvider(Protocol):
    app_label: str

    def list_permissions(self) -> tuple[PermissionSpec, ...]:
        ...


__all__ = ["PermissionProvider"]

