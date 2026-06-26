# -*- coding: utf-8 -*-
from __future__ import annotations

import re
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
    RESOURCE_ACCESS_MODE_ACL_REQUIRED,
    RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW,
    ROLE_SCOPE_ENTERPRISE,
    ROLE_SCOPE_PERSONAL,
    USER_TYPE_ENTERPRISE,
    USER_TYPE_PERSONAL
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


class ResourceValidator(IamManagementValidator):
    required_create_fields = (
        "resource_type",
        "resource_name",
    )
    allowed_create_fields = (
        "resource_type",
        "resource_name",
        "module_code",
        "access_mode",
        "status",
    )
    allowed_update_fields = (
        "resource_name",
        "module_code",
        "access_mode",
        "status",
    )
    integer_fields = (
        "status",
    )
    enum_fields = {
        "access_mode": (
            RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW,
            RESOURCE_ACCESS_MODE_ACL_REQUIRED,
        ),
    }
    max_lengths = {
        "resource_type": 128,
        "resource_name": 128,
        "module_code": 64,
        "access_mode": 32,
    }
    defaults = {
        "access_mode": RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW,
        "status": 1,
    }

    @classmethod
    def validate_create(cls, data: dict[str, Any]) -> dict[str, Any]:
        payload = cls.ensure_dict(data)

        if payload.get("resource_type") not in (None, ""):
            payload["resource_type"] = cls.normalize_resource_key(
                value=payload.get("resource_type"),
                field="resource_type",
            )

        if payload.get("module_code") in (None, "") and payload.get("resource_type") not in (None, ""):
            payload["module_code"] = cls.resolve_default_module_code(
                str(payload["resource_type"])
            )

        return super().validate_create(payload)

    @classmethod
    def validate_update(cls, data: dict[str, Any]) -> dict[str, Any]:
        payload = cls.ensure_dict(data)

        if payload.get("module_code") not in (None, ""):
            payload["module_code"] = cls.normalize_resource_key(
                value=payload.get("module_code"),
                field="module_code",
            )

        if payload.get("access_mode") not in (None, ""):
            payload["access_mode"] = str(payload["access_mode"]).strip().upper()

        return super().validate_update(payload)

    @classmethod
    def normalize_field_value(cls, *, field: str, value: Any) -> Any:
        if field in ("resource_type", "module_code"):
            return cls.normalize_resource_key(value=value, field=field)

        if field == "access_mode" and not cls.is_empty_value(value):
            value = str(value).strip().upper()

        return super().normalize_field_value(field=field, value=value)

    @classmethod
    def normalize_resource_key(cls, *, value: Any, field: str) -> str:
        normalized = str(value or "").strip().lower()

        if not normalized:
            return ""

        if " " in normalized:
            raise IamManagementRequestInvalidError(
                f"{field} cannot contain spaces.",
                details={
                    "field": field,
                    "value": normalized,
                },
            )

        return normalized

    @staticmethod
    def resolve_default_module_code(resource_type: str) -> str:
        if "." in resource_type:
            return resource_type.split(".", 1)[0]

        if ":" in resource_type:
            return resource_type.split(":", 1)[0]

        return resource_type


class ResourceActionValidator(IamManagementValidator):
    ACTION_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")

    required_create_fields = (
        "resource_id",
        "action_code",
        "action_name",
    )
    allowed_create_fields = (
        "resource_id",
        "action_code",
        "action_name",
        "status",
    )
    allowed_update_fields = (
        "action_name",
        "status",
    )
    integer_fields = (
        "resource_id",
        "status",
    )
    max_lengths = {
        "action_code": 64,
        "action_name": 128,
    }
    defaults = {
        "status": 1,
    }

    @classmethod
    def normalize_field_value(cls, *, field: str, value: Any) -> Any:
        if field == "action_code":
            normalized = str(value or "").strip().lower()

            if cls.ACTION_CODE_PATTERN.fullmatch(normalized) is None:
                raise IamManagementRequestInvalidError(
                    "action_code is invalid.",
                    details={
                        "field": field,
                        "value": normalized,
                        "pattern": cls.ACTION_CODE_PATTERN.pattern,
                    },
                )

            return normalized

        return super().normalize_field_value(field=field, value=value)


class ResourceRelationValidator(IamManagementValidator):
    required_create_fields = (
        "resource_type",
        "resource_id",
        "parent_resource_type",
        "parent_resource_id",
    )
    allowed_create_fields = (
        "resource_type",
        "resource_id",
        "parent_resource_type",
        "parent_resource_id",
        "relation_type",
    )
    allowed_update_fields = ()
    max_lengths = {
        "resource_type": 128,
        "resource_id": 128,
        "parent_resource_type": 128,
        "parent_resource_id": 128,
        "relation_type": 32,
    }
    defaults = {
        "relation_type": "PARENT",
    }

    @classmethod
    def normalize_field_value(cls, *, field: str, value: Any) -> Any:
        if field in ("resource_type", "parent_resource_type"):
            return ResourceValidator.normalize_resource_key(
                value=value,
                field=field,
            )

        if field == "relation_type":
            normalized = str(value or "PARENT").strip().upper()

            if normalized != "PARENT":
                raise IamManagementRequestInvalidError(
                    "relation_type is invalid.",
                    details={
                        "field": field,
                        "value": normalized,
                        "allowed_values": [
                            "PARENT"
                        ],
                    },
                )

            return normalized

        return super().normalize_field_value(field=field, value=value)


class ResourceAclValidator(IamManagementValidator):
    SUBJECT_TYPES = (
        "USER",
        "ROLE",
        "DEPARTMENT",
        "ORGANIZATION",
        "SUBSIDIARY",
    )

    ACTION_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")

    required_create_fields = (
        "subject_type",
        "subject_id",
        "resource_type",
        "resource_id",
        "action_code",
    )
    allowed_create_fields = (
        "subject_type",
        "subject_id",
        "resource_type",
        "resource_id",
        "action_code",
        "effect",
        "data_scope",
        "expired_at",
    )
    allowed_update_fields = ()
    integer_fields = (
        "subject_id",
    )
    datetime_fields = (
        "expired_at",
    )
    nullable_fields = (
        "data_scope",
        "expired_at",
    )
    enum_fields = {
        "subject_type": SUBJECT_TYPES,
        "effect": (
            PERMISSION_EFFECT_ALLOW,
            PERMISSION_EFFECT_DENY,
        ),
        "data_scope": DATA_SCOPE_VALUES,
    }
    max_lengths = {
        "subject_type": 32,
        "resource_type": 128,
        "resource_id": 128,
        "action_code": 64,
        "effect": 16,
        "data_scope": 32,
    }
    defaults = {
        "effect": PERMISSION_EFFECT_ALLOW,
    }

    @classmethod
    def normalize_field_value(cls, *, field: str, value: Any) -> Any:
        if field == "subject_type":
            value = str(value or "").strip().upper()

        if field == "resource_type":
            return ResourceValidator.normalize_resource_key(
                value=value,
                field=field,
            )

        if field == "action_code":
            normalized = str(value or "").strip().lower()

            if cls.ACTION_CODE_PATTERN.fullmatch(normalized) is None:
                raise IamManagementRequestInvalidError(
                    "action_code is invalid.",
                    details={
                        "field": field,
                        "value": normalized,
                        "pattern": cls.ACTION_CODE_PATTERN.pattern,
                    },
                )

            return normalized

        if field == "effect":
            value = str(value or PERMISSION_EFFECT_ALLOW).strip().upper()

        return super().normalize_field_value(
            field=field,
            value=value,
        )


class PolicyValidator(IamManagementValidator):
    required_create_fields = (
        "policy_code",
        "policy_name",
    )
    allowed_create_fields = (
        "policy_code",
        "policy_name",
        "priority",
        "status",
        "version",
    )
    allowed_update_fields = (
        "policy_name",
        "priority",
        "status",
        "version",
    )
    integer_fields = (
        "priority",
        "status",
        "version",
    )
    max_lengths = {
        "policy_code": 128,
        "policy_name": 128,
    }
    defaults = {
        "priority": 0,
        "status": 0,
        "version": 1,
    }

    @classmethod
    def normalize_field_value(cls, *, field: str, value: Any) -> Any:
        if field == "policy_code":
            normalized = str(value or "").strip().lower()

            if not normalized:
                return ""

            if " " in normalized:
                raise IamManagementRequestInvalidError(
                    "policy_code cannot contain spaces.",
                    details={
                        "field": field,
                        "value": normalized,
                    },
                )

            if len(normalized) > cls.max_lengths["policy_code"]:
                raise IamManagementRequestInvalidError(
                    "Field length exceeds limit.",
                    details={
                        "field": field,
                        "max_length": cls.max_lengths["policy_code"],
                    },
                )

            return normalized

        return super().normalize_field_value(
            field=field,
            value=value,
        )


class PolicyRuleValidator(IamManagementValidator):
    ACTION_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")

    SUBJECT_TYPES = (
        "USER",
        "ROLE",
        "DEPARTMENT",
        "ORGANIZATION",
        "SUBSIDIARY",
    )

    required_create_fields = (
        "policy_id",
        "action_code",
        "effect",
    )
    allowed_create_fields = (
        "policy_id",
        "subject_type",
        "subject_id",
        "resource_type",
        "resource_id",
        "action_code",
        "effect",
        "data_scope",
        "condition_json",
        "priority",
        "status",
    )
    allowed_update_fields = (
        "subject_type",
        "subject_id",
        "resource_type",
        "resource_id",
        "action_code",
        "effect",
        "data_scope",
        "condition_json",
        "priority",
        "status",
    )
    integer_fields = (
        "policy_id",
        "subject_id",
        "priority",
        "status",
    )
    nullable_fields = (
        "subject_type",
        "subject_id",
        "resource_type",
        "resource_id",
        "data_scope",
        "condition_json",
    )
    enum_fields = {
        "subject_type": SUBJECT_TYPES,
        "effect": (
            PERMISSION_EFFECT_ALLOW,
            PERMISSION_EFFECT_DENY,
        ),
        "data_scope": DATA_SCOPE_VALUES,
    }
    max_lengths = {
        "subject_type": 32,
        "resource_type": 128,
        "resource_id": 128,
        "action_code": 64,
        "effect": 16,
        "data_scope": 32,
    }
    defaults = {
        "priority": 0,
        "status": 1,
    }

    @classmethod
    def normalize_field_value(cls, *, field: str, value: Any) -> Any:
        if field == "subject_type":
            if cls.is_empty_value(value):
                return None

            return str(value).strip().upper()

        if field == "resource_type":
            if cls.is_empty_value(value):
                return None

            return ResourceValidator.normalize_resource_key(
                value=value,
                field=field,
            )

        if field == "action_code":
            normalized = str(value or "").strip().lower()

            if cls.ACTION_CODE_PATTERN.fullmatch(normalized) is None:
                raise IamManagementRequestInvalidError(
                    "action_code is invalid.",
                    details={
                        "field": field,
                        "value": normalized,
                        "pattern": cls.ACTION_CODE_PATTERN.pattern,
                    },
                )

            return normalized

        if field == "effect":
            return str(value or "").strip().upper()

        if field == "condition_json":
            if cls.is_empty_value(value):
                return None

            if not isinstance(value, dict):
                raise IamManagementRequestInvalidError(
                    "condition_json must be an object.",
                    details={
                        "field": field,
                    },
                )

            return value

        return super().normalize_field_value(
            field=field,
            value=value,
        )
   