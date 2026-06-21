# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.db import IntegrityError, transaction

from ns_backend.backend.common import BaseRepository
from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.models import IamUser
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


class AdminRepository:
    """Repository for IAM platform administrator initialization."""

    @staticmethod
    def exists_by_username(*, username: str, db_alias: str | None = None) -> bool:
        """Check whether a user already exists by username."""
        resolved_db_alias = db_alias or BaseRepository.resolve_db_alias(model_class=IamUser)
        return IamUser.objects.using(resolved_db_alias).filter(username=username).exists()

    @staticmethod
    def create_admin_user(*, data: dict[str, Any], db_alias: str | None = None) -> IamUser:
        """Create one platform administrator user."""
        resolved_db_alias = db_alias or BaseRepository.resolve_db_alias(model_class=IamUser)
        return IamUser.objects.using(resolved_db_alias).create(**data)

    @classmethod
    def create_admin_if_absent(cls, *, username: str, data: dict[str, Any]) -> tuple[IamUser | None, bool]:
        """Create platform administrator if username does not exist."""
        db_alias = BaseRepository.resolve_db_alias(model_class=IamUser)

        try:
            with transaction.atomic(using=db_alias):
                if cls.exists_by_username(username=username, db_alias=db_alias):
                    return None, False

                user = cls.create_admin_user(data=data, db_alias=db_alias)
                return user, True
        except IntegrityError as exc:
            if cls.exists_by_username(username=username, db_alias=db_alias):
                return None, False

            raise BusinessError(f"Failed to initialize administrator: {exc}", NsErrorCode.USER_CREATION_FAILED) from exc
