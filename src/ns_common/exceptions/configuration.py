# -*- coding: utf-8 -*-
from __future__ import annotations

from .common import NsConfigError
from .metadata import (
    NsErrorCategory,
    NsErrorDefinition,
    NsErrorSeverity,
)


class NsRuntimeConfigInvalidError(NsConfigError):
    code = "RUNTIME_CONFIG_INVALID"
    numeric_code = 200145
    default_message = "Runtime configuration is invalid."


class NsRuntimeConfigVersionConflictError(NsConfigError):
    code = "RUNTIME_CONFIG_VERSION_CONFLICT"
    numeric_code = 200146
    default_message = "Runtime configuration version conflicts."


class NsRuntimeConfigApplyFailedError(NsConfigError):
    code = "RUNTIME_CONFIG_APPLY_FAILED"
    numeric_code = 200147
    default_message = "Runtime configuration could not be applied."


CONFIGURATION_ERROR_DEFINITIONS: tuple[NsErrorDefinition, ...] = (
    NsErrorDefinition.for_error_type(
        NsRuntimeConfigInvalidError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.CONFIGURATION,
        action="reject_runtime_configuration",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeConfigVersionConflictError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.CONFIGURATION,
        audit_required=True,
        action="reject_config_version_conflict",
    ),
    NsErrorDefinition.for_error_type(
        NsRuntimeConfigApplyFailedError,
        severity=NsErrorSeverity.ERROR,
        category=NsErrorCategory.CONFIGURATION,
        audit_required=True,
        action="rollback_runtime_configuration",
    ),
)
