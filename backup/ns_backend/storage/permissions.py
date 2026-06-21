# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.schemas import PermissionSpec

if TYPE_CHECKING:
    pass

STORAGE_PERMISSIONS: tuple[PermissionSpec, ...] = (
    PermissionSpec(code="storage:object", name="Storage Object", permission_type="MENU"),
    PermissionSpec(code="storage:object:upload", name="Upload storage object", permission_type="ACTION", parent_code="storage:object"),
    PermissionSpec(code="storage:object:presigned_get", name="Create storage object presigned GET URL", permission_type="ACTION", parent_code="storage:object"),

    PermissionSpec(code="storage:object_ref", name="Storage Object Reference", permission_type="MENU"),
    PermissionSpec(code="storage:object_ref:list", name="List storage object references", permission_type="ACTION", parent_code="storage:object_ref"),
    PermissionSpec(code="storage:object_ref:detail", name="Get storage object reference detail", permission_type="ACTION", parent_code="storage:object_ref"),
    PermissionSpec(code="storage:object_ref:delete", name="Delete storage object reference", permission_type="ACTION", parent_code="storage:object_ref"),
)


class StoragePermissionProvider:
    """Storage builtin permission provider."""

    app_label = "storage"

    def list_permissions(self) -> tuple[PermissionSpec, ...]:
        """Return storage permission specs."""
        return STORAGE_PERMISSIONS
