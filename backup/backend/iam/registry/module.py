# -*- coding: utf-8 -*-
from __future__ import annotations

from ns_common.error_codes import NsErrorCode
from iam.schemas import PermissionProvider, PermissionSpec
from ns_backend.exceptions import BusinessError


class PermissionModuleRegistry:
    _providers: list[PermissionProvider] = []

    @classmethod
    def register_provider(cls, provider: PermissionProvider) -> None:
        app_label = getattr(provider, "app_label", None)
        normalized_label = app_label.strip() if isinstance(app_label, str) else ""
        if not normalized_label:
            raise BusinessError("Permission provider app_label is required", NsErrorCode.PROVIDER_APP_LABEL_REQUIRED)

        if normalized_label != app_label:
            raise BusinessError(f"Invalid permission provider app_label: {app_label}", NsErrorCode.PROVIDER_APP_LABEL_INVALID)

        if any(str(existing.app_label).strip() == normalized_label for existing in cls._providers):
            raise BusinessError(f"Duplicate permission provider: {normalized_label}", NsErrorCode.PROVIDER_DUPLICATED)

        if not callable(getattr(provider, "list_permissions", None)):
            raise BusinessError(f"Invalid permission provider: {normalized_label}", NsErrorCode.PROVIDER_INVALID)

        cls._providers.append(provider)

    @classmethod
    def register_many(
        cls,
        providers: list[PermissionProvider] | tuple[PermissionProvider, ...],
    ) -> None:
        for provider in providers:
            cls.register_provider(provider)

    @classmethod
    def list_providers(cls) -> list[PermissionProvider]:
        return list(cls._providers)

    @classmethod
    def list_specs(cls) -> list[PermissionSpec]:
        specs: list[PermissionSpec] = []
        for provider in cls._providers:
            app_label = str(provider.app_label).strip()
            provider_specs = provider.list_permissions()
            if not isinstance(provider_specs, (list, tuple)):
                raise BusinessError(
                    f"Permission provider returned invalid specs: {app_label}",
                    NsErrorCode.PROVIDER_SPECS_INVALID,
                )
            specs.extend(provider_specs)
        return specs

    @classmethod
    def clear(cls) -> None:
        cls._providers.clear()


__all__ = ["PermissionModuleRegistry"]

