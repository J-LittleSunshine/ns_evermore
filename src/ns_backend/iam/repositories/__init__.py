# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.repositories.auth import (
    AuthLoginBundleRepository,
    AuthUserRepository,
    LoginFailureRepository,
)
from ns_backend.iam.repositories.authorize import RuntimeAuthorizeRepository
from ns_backend.iam.repositories.data_scope import DataScopeRepository
from ns_backend.iam.repositories.decision_audit import DecisionAuditRepository
from ns_backend.iam.repositories.management import IamManagementRepository
from ns_backend.iam.repositories.permission import PermissionRepository
from ns_backend.iam.repositories.token import (
    UserSessionRepository,
    UserTokenRepository,
    UserTokenRotationRepository,
)

if TYPE_CHECKING:
    pass

__all__ = [
    "AuthLoginBundleRepository",
    "AuthUserRepository",
    "DataScopeRepository",
    "DecisionAuditRepository",
    "IamManagementRepository",
    "LoginFailureRepository",
    "PermissionRepository",
    "RuntimeAuthorizeRepository",
    "UserSessionRepository",
    "UserTokenRepository",
    "UserTokenRotationRepository",
]
