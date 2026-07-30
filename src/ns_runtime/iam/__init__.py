# -*- coding: utf-8 -*-
"""Explicit runtime side of the IAM-R1 contract."""

from .authorization import (
    AuthorizationMode,
    BackendUnavailablePolicy,
    ContractTestIamAuthorizationAdapter,
    MessageAuthorizationResult,
    MessageAuthorizationService,
    OperationRiskContext,
)
from .client import IamClient
from .credential_cache import (
    EncryptedCredentialCache,
    RuntimeNodeCredentialClaims,
    RuntimeNodeCredentialVerifier,
)
from .models import PermissionSnapshot
from .recovery import (
    BackendRecoveryCoordinator,
    BackendRecoveryState,
    RecoveryRevalidationResult,
    RecoveryRevalidator,
)

__all__ = (
    "AuthorizationMode", "BackendRecoveryCoordinator",
    "BackendRecoveryState", "BackendUnavailablePolicy",
    "ContractTestIamAuthorizationAdapter",
    "MessageAuthorizationResult",
    "EncryptedCredentialCache", "IamClient", "MessageAuthorizationService",
    "OperationRiskContext", "PermissionSnapshot",
    "RecoveryRevalidationResult", "RecoveryRevalidator",
    "RuntimeNodeCredentialClaims", "RuntimeNodeCredentialVerifier",
)
