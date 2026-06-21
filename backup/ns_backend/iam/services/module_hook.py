# -*- coding: utf-8 -*-
from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.utils.module_loading import import_string

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.services.policy import PolicyService
from ns_backend.iam.services.resource_registry import ResourceRegistryService
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class ModuleRegistrationHookService:
    """Load and execute external IAM module registration hooks."""

    SETTINGS_KEY = "IAM_MODULE_REGISTRATION_HOOKS"

    @classmethod
    def _load_hook_paths(cls) -> tuple[str, ...]:
        raw_value = getattr(settings, cls.SETTINGS_KEY, ()) or ()
        if not isinstance(
                raw_value, (
                        list,
                        tuple
                )
        ):
            raise BusinessError(f"{cls.SETTINGS_KEY} must be a list or tuple", NsErrorCode.INVALID_VALUE)

        normalized: list[str] = []
        for item in raw_value:
            if not isinstance(item, str) or not item.strip():
                raise BusinessError(f"Invalid module hook path: {item}", NsErrorCode.INVALID_VALUE)
            normalized.append(item.strip())
        return tuple(normalized)

    @staticmethod
    def _normalize_hook(hook_object: Any) -> Any:
        if callable(hook_object):
            return hook_object
        if callable(getattr(hook_object, "register", None)):
            return hook_object.register
        raise BusinessError(f"Invalid module registration hook: {hook_object}", NsErrorCode.INVALID_VALUE)

    @classmethod
    async def run_hooks(cls, *, operator_id: int | None = None) -> list[dict[str, Any]]:
        """Execute configured module hooks for resource/action/policy onboarding."""
        results: list[dict[str, Any]] = []
        for hook_path in cls._load_hook_paths():
            loaded_object = import_string(hook_path)
            hook = cls._normalize_hook(loaded_object() if isinstance(loaded_object, type) else loaded_object)

            payload = {
                "operator_id": operator_id,
                "resource_registry": ResourceRegistryService,
                "policy_service": PolicyService,
            }
            result = hook(**payload)
            if inspect.isawaitable(result):
                result = await result

            if result is None:
                result = {
                    "ok": True
                }
            if not isinstance(result, dict):
                result = {
                    "ok": True,
                    "result": result
                }

            results.append(
                {
                    "hook": hook_path,
                    "result": result,
                }
            )

        return results
