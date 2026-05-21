# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.validation import BaseValidator

if TYPE_CHECKING:
    pass

class CompanyValidator(BaseValidator):
    required_fields = ("company_code", "company_name")
    allowed_fields = ("company_code", "company_name", "legal_name", "status")
    enum_fields = {
        "status": (0, 1),
    }


class SubsidiaryValidator(BaseValidator):
    required_fields = ("company_id", "subsidiary_code", "subsidiary_name")
    allowed_fields = ("company_id", "subsidiary_code", "subsidiary_name", "status")
    enum_fields = {
        "status": (0, 1),
    }


class DepartmentValidator(BaseValidator):
    required_fields = ("company_id", "department_code", "department_name")
    allowed_fields = (
        "company_id",
        "subsidiary_id",
        "parent_id",
        "department_code",
        "department_name",
        "status",
    )
    enum_fields = {
        "status": (0, 1),
    }


class PermissionValidator(BaseValidator):
    required_fields = ("permission_code", "permission_name", "permission_type")
    allowed_fields = (
        "permission_code",
        "permission_name",
        "permission_type",
        "parent_id",
        "status",
    )
    enum_fields = {
        "permission_type": ("MENU", "ACTION", "DATA"),
        "status": (0, 1),
    }


class RoleValidator(BaseValidator):
    required_fields = ("role_code", "role_name", "role_scope")
    allowed_fields = ("role_code", "role_name", "role_scope", "status")
    enum_fields = {
        "role_scope": ("PERSONAL", "ENTERPRISE"),
        "status": (0, 1),
    }


class UserValidator(BaseValidator):
    required_fields = ("username", "password", "user_type")
    allowed_fields = (
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
    enum_fields = {
        "user_type": ("PERSONAL", "ENTERPRISE"),
        "is_active": (0, 1),
        "is_staff": (0, 1),
        "is_superuser": (0, 1),
    }


class UserRoleValidator(BaseValidator):
    required_fields = ("user_id", "role_id")
    allowed_fields = ("user_id", "role_id")


class RolePermissionValidator(BaseValidator):
    required_fields = ("role_id", "permission_id")
    allowed_fields = ("role_id", "permission_id", "expired_at")


class UserPermissionValidator(BaseValidator):
    required_fields = ("user_id", "permission_id", "effect")
    allowed_fields = ("user_id", "permission_id", "effect", "expired_at")
    enum_fields = {
        "effect": ("ALLOW", "DENY"),
    }


class DepartmentPermissionValidator(BaseValidator):
    required_fields = ("department_id", "permission_id", "effect")
    allowed_fields = ("department_id", "permission_id", "effect", "expired_at")
    enum_fields = {
        "effect": ("ALLOW", "DENY"),
    }


class SubsidiaryPermissionValidator(BaseValidator):
    required_fields = ("subsidiary_id", "permission_id", "effect")
    allowed_fields = ("subsidiary_id", "permission_id", "effect", "expired_at")
    enum_fields = {
        "effect": ("ALLOW", "DENY"),
    }
