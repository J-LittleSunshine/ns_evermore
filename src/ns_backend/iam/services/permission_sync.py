# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from django.utils import timezone

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.registry.builtin import register_builtin_permissions, register_builtin_permission_providers
from ns_backend.iam.registry.loader import register_configured_permission_providers
from ns_backend.iam.registry.module import PermissionModuleRegistry
from ns_backend.iam.registry.permission import PermissionRegistry
from ns_backend.iam.repositories import PermissionSyncRepository
from ns_backend.iam.schemas import PermissionSpec
from ns_backend.iam.services.module_hook import ModuleRegistrationHookService
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class PermissionSyncService:
    """Synchronize declared PermissionSpec items into iam_permission.

    Service responsibilities:
    1. Load builtin/configured permission providers.
    2. Validate permission specs before persistence.
    3. Resolve parent dependencies.
    4. Delegate permission persistence to PermissionSyncRepository.
    """

    MAX_DEPENDENCY_ROUNDS = 20
    ALLOWED_PERMISSION_TYPES = {"MENU", "ACTION", "DATA"}
    ALLOWED_STATUS_VALUES = {0, 1}
    ACTION_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")

    @classmethod
    def parse_action_code(cls, permission_code: str) -> str | None:
        """Extract action segment from permission code using module:resource:action shape."""
        segments = [segment.strip() for segment in permission_code.split(":")]
        if len(segments) < 3:
            return None

        if any(not segment for segment in segments):
            return None

        return segments[-1].lower()

    @classmethod
    async def sync_builtin_permissions(cls, operator_id: int | None = None) -> dict[str, int]:
        """Sync only IAM builtin permission specs."""
        PermissionRegistry.clear()
        register_builtin_permissions()
        specs = PermissionRegistry.list_specs()
        return await cls.sync_specs(specs, operator_id=operator_id)

    @classmethod
    async def sync_registered_permissions(cls, operator_id: int | None = None) -> dict[str, Any]:
        """Sync builtin provider and configured external providers."""
        PermissionModuleRegistry.clear()
        register_builtin_permission_providers()
        register_configured_permission_providers()
        specs = PermissionModuleRegistry.list_specs()
        result = await cls.sync_specs(specs, operator_id=operator_id)
        hook_results = await ModuleRegistrationHookService.run_hooks(operator_id=operator_id)
        return {
            **result,
            "hook_total": len(hook_results),
            "hook_items": hook_results,
        }

    @classmethod
    def validate_specs(cls, specs: list[PermissionSpec]) -> None:
        """Validate permission specs before writing database."""
        if not specs:
            return

        seen_codes: set[str] = set()

        for spec in specs:
            if not isinstance(spec, PermissionSpec):
                raise BusinessError("Permission spec is invalid", NsErrorCode.PROVIDER_SPECS_INVALID)

            code_value = spec.code.strip() if isinstance(spec.code, str) else ""
            if not code_value:
                raise BusinessError("Permission code is required", NsErrorCode.PERMISSION_CODE_REQUIRED)
            if isinstance(spec.code, str) and spec.code != code_value:
                raise BusinessError(f"Invalid permission code: {spec.code}", NsErrorCode.PERMISSION_CODE_FORMAT_INVALID)

            name_value = spec.name.strip() if isinstance(spec.name, str) else ""
            if not name_value:
                raise BusinessError("Permission name is required", NsErrorCode.PERMISSION_NAME_REQUIRED)
            if isinstance(spec.name, str) and spec.name != name_value:
                raise BusinessError(f"Invalid permission name: {spec.name}", NsErrorCode.PERMISSION_NAME_INVALID)

            if spec.permission_type not in cls.ALLOWED_PERMISSION_TYPES:
                raise BusinessError(f"Invalid permission type: {spec.permission_type}", NsErrorCode.PERMISSION_TYPE_INVALID)

            if spec.status not in cls.ALLOWED_STATUS_VALUES:
                raise BusinessError(f"Invalid permission status: {spec.status}", NsErrorCode.PERMISSION_STATUS_INVALID)

            if code_value in seen_codes:
                raise BusinessError(f"Duplicate permission code: {spec.code}", NsErrorCode.PERMISSION_CODE_DUPLICATED)
            seen_codes.add(code_value)

            if spec.permission_type == "ACTION":
                action_code = cls.parse_action_code(code_value)
                if action_code is None:
                    raise BusinessError(f"Invalid action permission code format: {spec.code}", NsErrorCode.PERMISSION_CODE_FORMAT_INVALID)

                if cls.ACTION_CODE_PATTERN.fullmatch(action_code) is None:
                    raise BusinessError(f"Invalid permission action: {action_code}", NsErrorCode.PERMISSION_ACTION_INVALID)

            if spec.parent_code is None:
                continue

            parent_code_value = spec.parent_code.strip() if isinstance(spec.parent_code, str) else ""
            if not parent_code_value:
                raise BusinessError(f"Invalid permission parent_code: {spec.parent_code}", NsErrorCode.PERMISSION_PARENT_CODE_INVALID)
            if isinstance(spec.parent_code, str) and spec.parent_code != parent_code_value:
                raise BusinessError(f"Invalid permission parent_code: {spec.parent_code}", NsErrorCode.PERMISSION_PARENT_CODE_FORMAT_INVALID)

            if parent_code_value == code_value:
                raise BusinessError(f"Permission cannot be parent of itself: {spec.code}", NsErrorCode.PERMISSION_PARENT_CODE_INVALID)

    @classmethod
    async def sync_specs(cls, specs: list[PermissionSpec], operator_id: int | None = None) -> dict[str, int]:
        """Create or update permission rows according to specs."""
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

        existing_permissions = await PermissionSyncRepository.get_permissions_by_codes([spec.code for spec in specs])
        code_to_id = {code: permission.id for code, permission in existing_permissions.items()}

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
                        }
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
                    )
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
            raise BusinessError("Permission parent dependency cannot be resolved", NsErrorCode.PERMISSION_PARENT_DEPENDENCY_UNRESOLVED)

        return {
            "total": total,
            "created": created_count,
            "updated": updated_count,
            "skipped": skipped_count,
        }
