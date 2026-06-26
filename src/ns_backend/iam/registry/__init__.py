# -*- coding: utf-8 -*-
from __future__ import annotations

from ns_backend.iam.registry.builtin import (
    IAM_BUILTIN_PERMISSION_SPECS,
    IamBuiltinPermissionProvider,
    register_builtin_permission_providers,
)
from ns_backend.iam.registry.module import PermissionModuleRegistry

__all__ = [
    "IAM_BUILTIN_PERMISSION_SPECS",
    "IamBuiltinPermissionProvider",
    "PermissionModuleRegistry",
    "register_builtin_permission_providers",
]