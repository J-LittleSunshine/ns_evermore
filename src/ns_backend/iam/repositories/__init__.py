# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.repositories.auth import AuthUserRepository, LoginFailureRepository
from ns_backend.iam.repositories.device import UserDeviceRepository
from ns_backend.iam.repositories.permission_sync import PermissionSyncRepository
from ns_backend.iam.repositories.session import UserSessionRepository
from ns_backend.iam.repositories.token import UserTokenRepository, UserTokenRotationRepository
from ns_backend.iam.schemas import TokenRotationResult

if TYPE_CHECKING:
    pass

__all__ = [
    "AuthUserRepository",
    "LoginFailureRepository",
    "PermissionSyncRepository",
    "TokenRotationResult",
    "UserDeviceRepository",
    "UserSessionRepository",
    "UserTokenRepository",
    "UserTokenRotationRepository",
]
