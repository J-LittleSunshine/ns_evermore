# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import (
    Any,
    ClassVar,
    TYPE_CHECKING,
)

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from ns_backend.iam.constants import (
    DATA_SCOPE_VALUES,
    PERMISSION_EFFECT_ALLOW,
    PERMISSION_EFFECT_DENY,
    PERMISSION_TYPE_ACTION,
    PERMISSION_TYPE_DATA,
    PERMISSION_TYPE_MENU,
    ROLE_SCOPE_ENTERPRISE,
    ROLE_SCOPE_PERSONAL,
    USER_TYPE_ENTERPRISE,
    USER_TYPE_PERSONAL,
)
from ns_backend.iam.errors import IamManagementRequestInvalidError

if TYPE_CHECKING:
    pass


class IamManagementValidator:
    required_create_fields: ClassVar[tuple[str, ...]] = ()
    allowed_create_fields: ClassVar[tuple[str, ...]] = ()
    allowed_update_fields: ClassVar[tuple[str, ...]] = ()

    integer_fields: ClassVar[tuple[str, ...]] = ()
    datetime_fields: ClassVar[tuple[str, ...]] = ()
    nullable_fields: ClassVar[tuple[str, ...]] = ()
    status_fields: ClassVar[tuple[str, ...]] = ("status",)
    enum_fields: ClassVar[dict[str, tuple[Any, ...]]] = {}
    max_lengths: ClassVar[dict[str, int]] = {}
    defaults: ClassVar[dict[str, Any]] = {}

    @classmethod
    def validate_create(cls, data: dict[str, Any]) -> dict[str, Any]:
        payload = cls.ensure_dict(data)
        return cls.validate_payload(
            payload=payload,
            allowed_fields=cls.allowed_create_fields,
            required_fields=cls.required_create_fields,
            apply_defaults=True,
            allow_empty_result=False,
        )

    @classmethod
    def validate_update(cls, data: dict[str, Any]) -> dict[str, Any]:
        payload = cls.ensure_dict(data)

        payload = {
            key: value
            for key, value in payload.items()
            if key != "id"
        }

        return cls.validate_payload(
            payload=payload,
            allowed_fields=cls.allowed_update_fields,
            required_fields=(),
            apply_defaults=False,
            allow_empty_result=False,
        )

    @classmethod
    def validate_filter(cls, data: dict[str, Any], *, allowed_fields: tuple[str, ...]) -> dict[str, Any]:
        payload = cls.ensure_dict(data)

        return cls.validate_payload(
            payload=payload,
            allowed_fields=allowed_fields,
            required_fields=(),
            apply_defaults=False,
            allow_empty_result=True,
        )

    @classmethod
    def validate_payload(cls, *, payload: dict[str, Any], allowed_fields: tuple[str, ...], required_fields: tuple[str, ...], apply_defaults: bool, allow_empty_result: bool) -> dict[str, Any]:
        allowed_field_set = set(allowed_fields)
        unknown_fields = [
            field
            for field in payload.keys()
            if field not in allowed_field_set
        ]

        if unknown_fields:
            raise IamManagementRequestInvalidError("Request contains unsupported fields.",
                details={
                    "fields": unknown_fields,
                    "allowed_fields": sorted(allowed_field_set),
                },
            )

        cleaned: dict[str, Any] = {}

        for field in allowed_fields:
            if field not in payload:
                continue

            cleaned[field] = cls.normalize_field_value(field=field, value=payload[field])

        if apply_defaults:
            for field, value in cls.defaults.items():
                if field in allowed_field_set and field not in cleaned:
                    cleaned[field] = value

        missing_fields = [
            field
            for field in required_fields
            if cls.is_empty_value(cleaned.get(field))
        ]

        if missing_fields:
            raise IamManagementRequestInvalidError("Required fields are missing.",
                details={
                    "fields": missing_fields,
                },
            )

        if not cleaned and not allow_empty_result:
            raise IamManagementRequestInvalidError("Request payload is empty.",
                details={
                    "allowed_fields": sorted(allowed_field_set),
                },
            )

        return cleaned

    @classmethod
    def normalize_field_value(cls, *, field: str, value: Any) -> Any:
        if field in cls.integer_fields:
            return cls.normalize_integer_field(field=field, value=value)

        if field in cls.datetime_fields:
            return cls.normalize_datetime_field(field=field, value=value)

        if cls.is_empty_value(value):
            if field in cls.nullable_fields:
                return None

            return ""

        normalized = str(value).strip()
        max_length = cls.max_lengths.get(field)

        if max_length is not None and len(normalized) > max_length:
            raise IamManagementRequestInvalidError("Field length exceeds limit.",
                details={
                    "field": field,
                    "max_length": max_length,
                },
            )

        enum_values = cls.enum_fields.get(field)
        if enum_values is not None and normalized not in enum_values:
            raise IamManagementRequestInvalidError("Field value is not allowed.",
                details={
                    "field": field,
                    "value": normalized,
                    "allowed_values": list(enum_values),
                },
            )

        return normalized

    @classmethod
    def normalize_integer_field(cls, *, field: str, value: Any) -> int | None:
        if cls.is_empty_value(value):
            if field in cls.nullable_fields:
                return None

            raise IamManagementRequestInvalidError(
                "Integer field cannot be empty.",
                details={
                    "field": field,
                },
            )

        try:
            normalized = int(value)
        except (TypeError, ValueError) as exc:
            raise IamManagementRequestInvalidError("Integer field has invalid format.",
                details={
                    "field": field,
                },
            ) from exc

        if field in cls.status_fields and normalized not in (0, 1):
            raise IamManagementRequestInvalidError("Status field must be 0 or 1.",
                details={
                    "field": field,
                    "value": normalized,
                },
            )

        if field.endswith("_id") and normalized <= 0:
            raise IamManagementRequestInvalidError("ID field must be positive.",
                details={
                    "field": field,
                    "value": normalized,
                },
            )

        return normalized

    @classmethod
    def normalize_datetime_field(cls, *, field: str, value: Any) -> datetime | None:
        if cls.is_empty_value(value):
            if field in cls.nullable_fields:
                return None

            raise IamManagementRequestInvalidError(
                "Datetime field cannot be empty.",
                details={
                    "field": field,
                },
            )

        if isinstance(value, datetime):
            normalized = value
        else:
            normalized = parse_datetime(str(value).strip())

        if normalized is None:
            raise IamManagementRequestInvalidError(
                "Datetime field has invalid format.",
                details={
                    "field": field,
                    "expected": "ISO 8601 datetime string",
                },
            )

        if timezone.is_naive(normalized):
            normalized = timezone.make_aware(
                normalized,
                timezone.get_current_timezone(),
            )

        return normalized

    @staticmethod
    def ensure_dict(data: Any) -> dict[str, Any]:
        if not isinstance(data, dict):
            raise IamManagementRequestInvalidError("Request payload must be an object.")

        return dict(data)

    @staticmethod
    def is_empty_value(value: Any) -> bool:
        return value is None or value == ""


class CompanyValidator(IamManagementValidator):
    required_create_fields = (
        "company_code",
        "company_name",
    )
    allowed_create_fields = (
        "company_code",
        "company_name",
        "legal_name",
        "status",
    )
    allowed_update_fields = (
        "company_name",
        "legal_name",
        "status",
    )
    integer_fields = (
        "status",
    )
    nullable_fields = (
        "legal_name",
    )
    max_lengths = {
        "company_code": 64,
        "company_name": 128,
        "legal_name": 128,
    }
    defaults = {
        "status": 1,
    }


class SubsidiaryValidator(IamManagementValidator):
    required_create_fields = (
        "company_id",
        "subsidiary_code",
        "subsidiary_name",
    )
    allowed_create_fields = (
        "company_id",
        "subsidiary_code",
        "subsidiary_name",
        "status",
    )
    allowed_update_fields = (
        "subsidiary_name",
        "status",
    )
    integer_fields = (
        "company_id",
        "status",
    )
    max_lengths = {
        "subsidiary_code": 64,
        "subsidiary_name": 128,
    }
    defaults = {
        "status": 1,
    }


class DepartmentValidator(IamManagementValidator):
    required_create_fields = (
        "company_id",
        "department_code",
        "department_name",
    )
    allowed_create_fields = (
        "company_id",
        "subsidiary_id",
        "parent_id",
        "department_code",
        "department_name",
        "status",
    )
    allowed_update_fields = (
        "department_name",
        "status",
    )
    integer_fields = (
        "company_id",
        "subsidiary_id",
        "parent_id",
        "status",
    )
    nullable_fields = (
        "subsidiary_id",
        "parent_id",
    )
    max_lengths = {
        "department_code": 64,
        "department_name": 128,
    }
    defaults = {
        "status": 1,
    }


class PermissionValidator(IamManagementValidator):
    required_create_fields = (
        "permission_code",
        "permission_name",
        "permission_type",
    )
    allowed_create_fields = (
        "permission_code",
        "permission_name",
        "permission_type",
        "parent_id",
        "status",
    )
    allowed_update_fields = (
        "permission_name",
        "permission_type",
        "parent_id",
        "status",
    )
    integer_fields = (
        "parent_id",
        "status",
    )
    nullable_fields = (
        "parent_id",
    )
    enum_fields = {
        "permission_type": (
            PERMISSION_TYPE_MENU,
            PERMISSION_TYPE_ACTION,
            PERMISSION_TYPE_DATA,
        ),
    }
    max_lengths = {
        "permission_code": 128,
        "permission_name": 128,
        "permission_type": 32,
    }
    defaults = {
        "status": 1,
    }


class RoleValidator(IamManagementValidator):
    required_create_fields = (
        "role_code",
        "role_name",
        "role_scope",
    )
    allowed_create_fields = (
        "role_code",
        "role_name",
        "role_scope",
        "company_id",
        "status",
    )
    allowed_update_fields = (
        "role_name",
        "status",
    )
    integer_fields = (
        "company_id",
        "status",
    )
    nullable_fields = (
        "company_id",
    )
    enum_fields = {
        "role_scope": (
            ROLE_SCOPE_PERSONAL,
            ROLE_SCOPE_ENTERPRISE,
        ),
    }
    max_lengths = {
        "role_code": 64,
        "role_name": 128,
        "role_scope": 32,
    }
    defaults = {
        "status": 1,
    }


class UserValidator(IamManagementValidator):
    required_create_fields = (
        "username",
        "password",
        "user_type",
    )
    allowed_create_fields = (
        "username",
        "password",
        "email",
        "phone",
        "display_name",
        "user_type",
        "company_id",
        "subsidiary_id",
        "department_id",
        "is_active",
        "is_staff",
        "is_superuser",
    )
    allowed_update_fields = (
        "email",
        "phone",
        "display_name",
        "company_id",
        "subsidiary_id",
        "department_id",
        "is_active",
        "is_staff",
        "is_superuser",
    )
    integer_fields = (
        "company_id",
        "subsidiary_id",
        "department_id",
        "is_active",
        "is_staff",
        "is_superuser",
    )
    nullable_fields = (
        "email",
        "phone",
        "display_name",
        "company_id",
        "subsidiary_id",
        "department_id",
    )
    status_fields = (
        "is_active",
        "is_staff",
        "is_superuser",
    )
    enum_fields = {
        "user_type": (
            USER_TYPE_PERSONAL,
            USER_TYPE_ENTERPRISE,
        ),
    }
    max_lengths = {
        "username": 64,
        "email": 128,
        "phone": 32,
        "display_name": 64,
        "user_type": 32,
    }
    defaults = {
        "is_active": 1,
        "is_staff": 0,
        "is_superuser": 0,
    }


class UserRoleValidator(IamManagementValidator):
    required_create_fields = (
        "user_id",
        "role_id",
    )
    allowed_create_fields = (
        "user_id",
        "role_id",
    )
    allowed_update_fields = ()
    integer_fields = (
        "user_id",
        "role_id",
    )


class RolePermissionValidator(IamManagementValidator):
    required_create_fields = (
        "role_id",
        "permission_id",
    )
    allowed_create_fields = (
        "role_id",
        "permission_id",
        "data_scope",
        "expired_at",
    )
    allowed_update_fields = ()
    integer_fields = (
        "role_id",
        "permission_id",
    )
    datetime_fields = (
        "expired_at",
    )
    nullable_fields = (
        "data_scope",
        "expired_at",
    )
    enum_fields = {
        "data_scope": DATA_SCOPE_VALUES,
    }


class DirectPermissionGrantValidator(IamManagementValidator):
    required_create_fields = (
        "permission_id",
        "effect",
    )
    allowed_create_fields = (
        "permission_id",
        "effect",
        "data_scope",
        "expired_at",
    )
    allowed_update_fields = ()
    integer_fields = (
        "permission_id",
    )
    datetime_fields = (
        "expired_at",
    )
    nullable_fields = (
        "data_scope",
        "expired_at",
    )
    enum_fields = {
        "effect": (
            PERMISSION_EFFECT_ALLOW,
            PERMISSION_EFFECT_DENY,
        ),
        "data_scope": DATA_SCOPE_VALUES,
    }


class UserPermissionValidator(DirectPermissionGrantValidator):
    required_create_fields = (
        "user_id",
        "permission_id",
        "effect",
    )
    allowed_create_fields = (
        "user_id",
        "permission_id",
        "effect",
        "data_scope",
        "expired_at",
    )
    integer_fields = (
        "user_id",
        "permission_id",
    )


class DepartmentPermissionValidator(DirectPermissionGrantValidator):
    required_create_fields = (
        "department_id",
        "permission_id",
        "effect",
    )
    allowed_create_fields = (
        "department_id",
        "permission_id",
        "effect",
        "data_scope",
        "expired_at",
    )
    integer_fields = (
        "department_id",
        "permission_id",
    )


class SubsidiaryPermissionValidator(DirectPermissionGrantValidator):
    required_create_fields = (
        "subsidiary_id",
        "permission_id",
        "effect",
    )
    allowed_create_fields = (
        "subsidiary_id",
        "permission_id",
        "effect",
        "data_scope",
        "expired_at",
    )
    integer_fields = (
        "subsidiary_id",
        "permission_id",
    )
