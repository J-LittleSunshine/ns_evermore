# -*- coding: utf-8 -*-
from __future__ import annotations

"""Load configured permission providers.

Settings example:
    IAM_PERMISSION_PROVIDERS = [
        "crm.permissions.CrmPermissionProvider",
    ]
"""

from django.conf import settings
from django.utils.module_loading import import_string

from iam.error_codes import IamErrorCode
from iam.registry.module import PermissionModuleRegistry
from ns_backend.exceptions import BusinessError


def register_configured_permission_providers() -> None:
    provider_paths = getattr(settings, "IAM_PERMISSION_PROVIDERS", ()) or ()

    if not isinstance(provider_paths, (list, tuple)):
        raise BusinessError("IAM_PERMISSION_PROVIDERS must be a list or tuple", IamErrorCode.PERMISSION_PROVIDERS_CONFIG_INVALID)

    for provider_path in provider_paths:
        if not isinstance(provider_path, str) or not provider_path.strip():
            raise BusinessError(f"Invalid permission provider path: {provider_path}", IamErrorCode.PROVIDER_PATH_INVALID)

        provider_object = import_string(provider_path.strip())

        if isinstance(provider_object, type):
            provider = provider_object()
        else:
            provider = provider_object

        PermissionModuleRegistry.register_provider(provider)


__all__ = ["register_configured_permission_providers"]

