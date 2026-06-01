# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings
from django.utils.module_loading import import_string

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.registry.module import PermissionModuleRegistry
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


def register_configured_permission_providers() -> None:
    """Load permission providers from settings.IAM_PERMISSION_PROVIDERS."""
    provider_paths = getattr(settings, "IAM_PERMISSION_PROVIDERS", ()) or ()

    if not isinstance(provider_paths, (list, tuple)):
        raise BusinessError("IAM_PERMISSION_PROVIDERS must be a list or tuple", NsErrorCode.PERMISSION_PROVIDERS_CONFIG_INVALID)

    for provider_path in provider_paths:
        if not isinstance(provider_path, str) or not provider_path.strip():
            raise BusinessError(f"Invalid permission provider path: {provider_path}", NsErrorCode.PROVIDER_PATH_INVALID)

        provider_object = import_string(provider_path.strip())

        if isinstance(provider_object, type):
            provider = provider_object()
        else:
            provider = provider_object

        PermissionModuleRegistry.register_provider(provider)
