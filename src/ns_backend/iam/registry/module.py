# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.errors import IamManagementRequestInvalidError
from ns_backend.iam.schemas import (
    PermissionProvider,
    PermissionSpec,
)

if TYPE_CHECKING:
    pass


class PermissionModuleRegistry:
    _providers: dict[str, PermissionProvider] = {}

    @staticmethod
    def normalize_app_label(value: object) -> str:
        return str(value or "").strip()

    @classmethod
    def has_provider(cls, app_label: str) -> bool:
        normalized_label = cls.normalize_app_label(app_label)
        return normalized_label in cls._providers

    @classmethod
    def register_provider(cls, provider: PermissionProvider) -> None:
        app_label = getattr(provider, "app_label", None)
        normalized_label = cls.normalize_app_label(app_label)

        if not normalized_label:
            raise IamManagementRequestInvalidError(
                "Permission provider app_label is required.",
                details={
                    "field": "app_label",
                },
            )

        if normalized_label != app_label:
            raise IamManagementRequestInvalidError(
                "Permission provider app_label is invalid.",
                details={
                    "app_label": app_label,
                },
            )

        if normalized_label in cls._providers:
            raise IamManagementRequestInvalidError(
                "Permission provider is duplicated.",
                details={
                    "app_label": normalized_label,
                },
            )

        if not callable(getattr(provider, "list_permissions", None)):
            raise IamManagementRequestInvalidError(
                "Permission provider is invalid.",
                details={
                    "app_label": normalized_label,
                },
            )

        cls._providers[normalized_label] = provider

    @classmethod
    def register_many(cls, providers: list[PermissionProvider] | tuple[PermissionProvider, ...]) -> None:
        for provider in providers:
            cls.register_provider(provider)

    @classmethod
    def list_providers(cls) -> list[PermissionProvider]:
        return list(cls._providers.values())

    @classmethod
    def list_specs(cls) -> list[PermissionSpec]:
        specs: list[PermissionSpec] = []

        for provider in cls.list_providers():
            app_label = cls.normalize_app_label(getattr(provider, "app_label", None))
            provider_specs = provider.list_permissions()

            if not isinstance(provider_specs, (list, tuple)):
                raise IamManagementRequestInvalidError(
                    "Permission provider returned invalid specs.",
                    details={
                        "app_label": app_label,
                    },
                )

            for spec in provider_specs:
                if not isinstance(spec, PermissionSpec):
                    raise IamManagementRequestInvalidError(
                        "Permission provider returned invalid spec item.",
                        details={
                            "app_label": app_label,
                            "actual_type": type(spec).__name__,
                        },
                    )

                specs.append(spec)

        return specs

    @classmethod
    def clear(cls) -> None:
        cls._providers.clear()
