# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PermissionSpec:
    code: str
    name: str
    permission_type: str
    parent_code: str | None = None
    status: int = 1


__all__ = ["PermissionSpec"]

