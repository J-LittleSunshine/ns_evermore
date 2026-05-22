# -*- coding: utf-8 -*-
from __future__ import annotations

from django.utils import timezone

from iam.registry.builtin import (
    register_builtin_permissions,
    register_builtin_permission_providers,
)
from iam.registry.module import PermissionModuleRegistry
from iam.registry.permission import PermissionRegistry
from iam.repositories.permission_sync import PermissionSyncRepository
from iam.schemas import PermissionSpec
from ns_backend.exceptions import BusinessError


class PermissionSyncService:
    MAX_DEPENDENCY_ROUNDS = 20
    ALLOWED_PERMISSION_TYPES = {"MENU", "ACTION", "DATA"}
    ALLOWED_STATUS_VALUES = {0, 1}

    @classmethod
    async def sync_builtin_permissions(cls, operator_id: int | None = None) -> dict:
        PermissionRegistry.clear()
        register_builtin_permissions()
        specs = PermissionRegistry.list_specs()
        return await cls.sync_specs(specs, operator_id=operator_id)

    @classmethod
    async def sync_registered_permissions(cls, operator_id: int | None = None) -> dict:
        PermissionModuleRegistry.clear()
        register_builtin_permission_providers()
        specs = PermissionModuleRegistry.list_specs()
        return await cls.sync_specs(specs, operator_id=operator_id)

    @classmethod
    def validate_specs(cls, specs: list[PermissionSpec]) -> None:
        if not specs:
            return

        seen_codes: set[str] = set()

        for spec in specs:
            code_value = spec.code.strip() if isinstance(spec.code, str) else ""
            if not code_value:
                raise BusinessError("Permission code is required", 17005)

            name_value = spec.name.strip() if isinstance(spec.name, str) else ""
            if not name_value:
                raise BusinessError("Permission name is required", 17006)

            if spec.permission_type not in cls.ALLOWED_PERMISSION_TYPES:
                raise BusinessError(f"Invalid permission type: {spec.permission_type}", 17007)

            if spec.status not in cls.ALLOWED_STATUS_VALUES:
                raise BusinessError(f"Invalid permission status: {spec.status}", 17008)

            if code_value in seen_codes:
                raise BusinessError(f"Duplicate permission code: {spec.code}", 17001)
            seen_codes.add(code_value)

            if spec.parent_code is None:
                continue

            parent_code_value = spec.parent_code.strip() if isinstance(spec.parent_code, str) else ""
            if not parent_code_value:
                raise BusinessError(f"Invalid permission parent_code: {spec.parent_code}", 17009)

            if parent_code_value == code_value:
                raise BusinessError(f"Permission cannot be parent of itself: {spec.code}", 17009)

    @classmethod
    async def sync_specs(
        cls,
        specs: list[PermissionSpec],
        operator_id: int | None = None,
    ) -> dict:
        total = len(specs)
        cls.validate_specs(specs)
        created_count = 0
        updated_count = 0
        skipped_count = 0

        if not specs:
            return {
                "total": total,
                "created": created_count,
                "updated": updated_count,
                "skipped": skipped_count,
            }

        existing_permissions = await PermissionSyncRepository.get_permissions_by_codes(
            [spec.code for spec in specs],
        )
        code_to_id = {
            code: permission.id
            for code, permission in existing_permissions.items()
        }

        pending_specs = list(specs)

        for _ in range(cls.MAX_DEPENDENCY_ROUNDS):
            if not pending_specs:
                break

            unresolved_parent_codes = sorted({
                spec.parent_code
                for spec in pending_specs
                if spec.parent_code and spec.parent_code not in code_to_id
            })
            if unresolved_parent_codes:
                parent_ids = await PermissionSyncRepository.bulk_get_parent_ids(unresolved_parent_codes)
                code_to_id.update(parent_ids)

            progressed = False
            next_pending: list[PermissionSpec] = []

            for spec in pending_specs:
                if spec.parent_code and spec.parent_code not in code_to_id:
                    next_pending.append(spec)
                    continue

                parent_id = code_to_id.get(spec.parent_code) if spec.parent_code else None
                now = timezone.now()
                existing = existing_permissions.get(spec.code)

                if existing is None:
                    created = await PermissionSyncRepository.create_permission(
                        {
                            "permission_code": spec.code,
                            "permission_name": spec.name,
                            "permission_type": spec.permission_type,
                            "parent_id": parent_id,
                            "status": spec.status,
                            "created_by": operator_id,
                            "updated_by": operator_id,
                            "created_at": now,
                            "updated_at": now,
                        },
                    )
                    existing_permissions[spec.code] = created
                    code_to_id[spec.code] = created.id
                    created_count += 1
                    progressed = True
                    continue

                has_changes = any(
                    (
                        existing.permission_name != spec.name,
                        existing.permission_type != spec.permission_type,
                        existing.parent_id != parent_id,
                        existing.status != spec.status,
                    ),
                )

                if has_changes:
                    await PermissionSyncRepository.update_permission(
                        existing,
                        {
                            "permission_name": spec.name,
                            "permission_type": spec.permission_type,
                            "parent_id": parent_id,
                            "status": spec.status,
                            "updated_by": operator_id,
                            "updated_at": now,
                        },
                    )
                    updated_count += 1
                else:
                    skipped_count += 1

                code_to_id[spec.code] = existing.id
                progressed = True

            pending_specs = next_pending

            if not progressed and pending_specs:
                break

        if pending_specs:
            raise BusinessError("Permission parent dependency cannot be resolved", 17004)

        return {
            "total": total,
            "created": created_count,
            "updated": updated_count,
            "skipped": skipped_count,
        }


__all__ = ["PermissionSyncService"]
