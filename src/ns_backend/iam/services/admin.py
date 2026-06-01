# -*- coding: utf-8 -*-
from __future__ import annotations

import secrets
from typing import TYPE_CHECKING, Any

from django.contrib.auth.hashers import make_password
from django.utils import timezone

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.constants import USER_TYPE_ENTERPRISE
from ns_backend.iam.repositories import AdminRepository
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class AdminService:
    """Platform administrator initialization service."""

    DEFAULT_USERNAME = "admin"
    DEFAULT_DISPLAY_NAME = "System Administrator"
    RANDOM_PASSWORD_BYTES = 16

    @classmethod
    def initialize_admin(cls, *, username: str | None = None, password: str | None = None, display_name: str | None = None) -> dict[str, Any]:
        """Initialize one platform administrator if it does not already exist."""
        normalized_username = cls.normalize_username(username)
        normalized_display_name = cls.normalize_display_name(display_name)
        raw_password, is_random_password = cls.resolve_initial_password(password)

        now = timezone.now()
        user, created = AdminRepository.create_admin_if_absent(
            username=normalized_username,
            data={
                "username": normalized_username,
                "password": make_password(raw_password),
                "display_name": normalized_display_name,
                "user_type": USER_TYPE_ENTERPRISE,
                "is_active": 1,
                "is_staff": 1,
                "is_superuser": 1,
                "created_at": now,
                "updated_at": now,
            },
        )

        return {
            "created": created,
            "user_id": None if user is None else user.id,
            "username": normalized_username,
            "initial_password": raw_password if created and is_random_password else None,
            "password_generated": created and is_random_password,
        }

    @classmethod
    def normalize_username(cls, username: str | None) -> str:
        """Normalize administrator username."""
        value = str(username or cls.DEFAULT_USERNAME).strip()
        if not value:
            raise BusinessError("Administrator username must not be empty", NsErrorCode.USERNAME_EMPTY)
        return value

    @classmethod
    def normalize_display_name(cls, display_name: str | None) -> str:
        """Normalize administrator display name."""
        value = str(display_name or cls.DEFAULT_DISPLAY_NAME).strip()
        return value or cls.DEFAULT_DISPLAY_NAME

    @classmethod
    def resolve_initial_password(cls, password: str | None) -> tuple[str, bool]:
        """Resolve initial administrator password and whether it was generated."""
        if password is None:
            return secrets.token_urlsafe(cls.RANDOM_PASSWORD_BYTES), True

        value = str(password)
        if not value.strip():
            raise BusinessError("Administrator password must not be empty when --password is provided", NsErrorCode.PASSWORD_EMPTY)

        return value, False
