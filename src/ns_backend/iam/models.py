# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from ns_backend.iam.constants import DATA_SCOPE_CHOICES

if TYPE_CHECKING:
    pass


class IamCompany(models.Model):
    id = models.BigAutoField(primary_key=True)
    company_code = models.CharField(max_length=64, unique=True)
    company_name = models.CharField(max_length=128)
    legal_name = models.CharField(max_length=128, null=True, blank=True)
    status = models.SmallIntegerField(default=1)
    created_by = models.BigIntegerField(null=True, blank=True)
    updated_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_company"


class IamSubsidiary(models.Model):
    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(IamCompany, on_delete=models.DO_NOTHING, db_column="company_id")
    subsidiary_code = models.CharField(max_length=64, unique=True)
    subsidiary_name = models.CharField(max_length=128)
    status = models.SmallIntegerField(default=1)
    created_by = models.BigIntegerField(null=True, blank=True)
    updated_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_subsidiary"


class IamDepartment(models.Model):
    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(IamCompany, on_delete=models.DO_NOTHING, db_column="company_id")
    subsidiary = models.ForeignKey(IamSubsidiary, on_delete=models.DO_NOTHING, db_column="subsidiary_id", null=True, blank=True)
    parent = models.ForeignKey("self", on_delete=models.DO_NOTHING, db_column="parent_id", null=True, blank=True)
    department_code = models.CharField(max_length=64, unique=True)
    department_name = models.CharField(max_length=128)
    status = models.SmallIntegerField(default=1)
    created_by = models.BigIntegerField(null=True, blank=True)
    updated_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_department"


class IamUser(models.Model):
    USER_TYPE_PERSONAL = "PERSONAL"
    USER_TYPE_ENTERPRISE = "ENTERPRISE"

    USER_TYPE_CHOICES = ((USER_TYPE_PERSONAL, "Personal user"), (USER_TYPE_ENTERPRISE, "Enterprise user"))

    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=64, unique=True)
    password = models.CharField(max_length=128)
    email = models.CharField(max_length=128, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=32, unique=True, null=True, blank=True)
    display_name = models.CharField(max_length=64, null=True, blank=True)
    user_type = models.CharField(max_length=32, choices=USER_TYPE_CHOICES)

    company = models.ForeignKey(IamCompany, on_delete=models.DO_NOTHING, db_column="company_id", null=True, blank=True)
    subsidiary = models.ForeignKey(IamSubsidiary, on_delete=models.DO_NOTHING, db_column="subsidiary_id", null=True, blank=True)
    department = models.ForeignKey(IamDepartment, on_delete=models.DO_NOTHING, db_column="department_id", null=True, blank=True)

    is_active = models.SmallIntegerField(default=1)
    is_staff = models.SmallIntegerField(default=0)
    is_superuser = models.SmallIntegerField(default=0)
    last_login = models.DateTimeField(null=True, blank=True)
    created_by = models.BigIntegerField(null=True, blank=True)
    updated_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_user"


class IamPermission(models.Model):
    TYPE_MENU = "MENU"
    TYPE_ACTION = "ACTION"
    TYPE_DATA = "DATA"

    TYPE_CHOICES = ((TYPE_MENU, "Menu permission"), (TYPE_ACTION, "Action permission"), (TYPE_DATA, "Data permission"))

    id = models.BigAutoField(primary_key=True)
    permission_code = models.CharField(max_length=128, unique=True)
    permission_name = models.CharField(max_length=128)
    permission_type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    parent = models.ForeignKey("self", on_delete=models.DO_NOTHING, db_column="parent_id", null=True, blank=True)
    status = models.SmallIntegerField(default=1)
    created_by = models.BigIntegerField(null=True, blank=True)
    updated_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_permission"


class IamRole(models.Model):
    SCOPE_PERSONAL = "PERSONAL"
    SCOPE_ENTERPRISE = "ENTERPRISE"

    SCOPE_CHOICES = ((SCOPE_PERSONAL, "Personal scope"), (SCOPE_ENTERPRISE, "Enterprise scope"))

    id = models.BigAutoField(primary_key=True)
    role_code = models.CharField(max_length=64)
    role_name = models.CharField(max_length=128)
    role_scope = models.CharField(max_length=32, choices=SCOPE_CHOICES)
    company = models.ForeignKey(IamCompany, on_delete=models.DO_NOTHING, db_column="company_id", null=True, blank=True)
    status = models.SmallIntegerField(default=1)
    created_by = models.BigIntegerField(null=True, blank=True)
    updated_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_role"


class IamRolePermission(models.Model):
    id = models.BigAutoField(primary_key=True)
    role = models.ForeignKey(IamRole, on_delete=models.DO_NOTHING, db_column="role_id")
    permission = models.ForeignKey(IamPermission, on_delete=models.DO_NOTHING, db_column="permission_id")
    data_scope = models.CharField(max_length=32, choices=DATA_SCOPE_CHOICES, null=True, blank=True)
    granted_by = models.ForeignKey(IamUser, on_delete=models.DO_NOTHING, db_column="granted_by", null=True, blank=True)
    expired_at = models.DateTimeField(null=True, blank=True)
    created_by = models.BigIntegerField(null=True, blank=True)
    updated_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_role_permission"
        unique_together = (("role", "permission"),)


class IamUserRole(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(IamUser, on_delete=models.DO_NOTHING, db_column="user_id")
    role = models.ForeignKey(IamRole, on_delete=models.DO_NOTHING, db_column="role_id")
    created_by = models.BigIntegerField(null=True, blank=True)
    updated_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_user_role"
        unique_together = (("user", "role"),)


class IamUserPermission(models.Model):
    EFFECT_ALLOW = "ALLOW"
    EFFECT_DENY = "DENY"
    EFFECT_CHOICES = ((EFFECT_ALLOW, "Allow"), (EFFECT_DENY, "Deny"))

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(IamUser, on_delete=models.DO_NOTHING, db_column="user_id", related_name="direct_permissions")
    permission = models.ForeignKey(IamPermission, on_delete=models.DO_NOTHING, db_column="permission_id", related_name="user_grants")
    effect = models.CharField(max_length=16, choices=EFFECT_CHOICES, default=EFFECT_ALLOW)
    data_scope = models.CharField(max_length=32, choices=DATA_SCOPE_CHOICES, null=True, blank=True)
    granted_by = models.ForeignKey(IamUser, on_delete=models.DO_NOTHING, db_column="granted_by", null=True, blank=True, related_name="granted_user_permissions")
    expired_at = models.DateTimeField(null=True, blank=True)
    created_by = models.BigIntegerField(null=True, blank=True)
    updated_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_user_permission"
        unique_together = (("user", "permission"),)


class IamDepartmentPermission(models.Model):
    EFFECT_ALLOW = "ALLOW"
    EFFECT_DENY = "DENY"
    EFFECT_CHOICES = ((EFFECT_ALLOW, "Allow"), (EFFECT_DENY, "Deny"))

    id = models.BigAutoField(primary_key=True)
    department = models.ForeignKey(IamDepartment, on_delete=models.DO_NOTHING, db_column="department_id", related_name="permission_grants")
    permission = models.ForeignKey(IamPermission, on_delete=models.DO_NOTHING, db_column="permission_id", related_name="department_grants")
    effect = models.CharField(max_length=16, choices=EFFECT_CHOICES, default=EFFECT_ALLOW)
    data_scope = models.CharField(max_length=32, choices=DATA_SCOPE_CHOICES, null=True, blank=True)
    granted_by = models.ForeignKey(IamUser, on_delete=models.DO_NOTHING, db_column="granted_by", null=True, blank=True, related_name="granted_department_permissions")
    expired_at = models.DateTimeField(null=True, blank=True)
    created_by = models.BigIntegerField(null=True, blank=True)
    updated_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_department_permission"
        unique_together = (("department", "permission"),)


class IamSubsidiaryPermission(models.Model):
    EFFECT_ALLOW = "ALLOW"
    EFFECT_DENY = "DENY"
    EFFECT_CHOICES = ((EFFECT_ALLOW, "Allow"), (EFFECT_DENY, "Deny"))

    id = models.BigAutoField(primary_key=True)
    subsidiary = models.ForeignKey(IamSubsidiary, on_delete=models.DO_NOTHING, db_column="subsidiary_id", related_name="permission_grants")
    permission = models.ForeignKey(IamPermission, on_delete=models.DO_NOTHING, db_column="permission_id", related_name="subsidiary_grants")
    effect = models.CharField(max_length=16, choices=EFFECT_CHOICES, default=EFFECT_ALLOW)
    data_scope = models.CharField(max_length=32, choices=DATA_SCOPE_CHOICES, null=True, blank=True)
    granted_by = models.ForeignKey(IamUser, on_delete=models.DO_NOTHING, db_column="granted_by", null=True, blank=True, related_name="granted_subsidiary_permissions")
    expired_at = models.DateTimeField(null=True, blank=True)
    created_by = models.BigIntegerField(null=True, blank=True)
    updated_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_subsidiary_permission"
        unique_together = (("subsidiary", "permission"),)


class IamUserDevice(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(IamUser, on_delete=models.DO_NOTHING, db_column="user_id", related_name="devices")
    device_id = models.CharField(max_length=128, unique=True)
    device_name = models.CharField(max_length=128)
    device_type = models.CharField(max_length=32)
    os_name = models.CharField(max_length=64, null=True, blank=True)
    browser_name = models.CharField(max_length=64, null=True, blank=True)
    fingerprint_hash = models.CharField(max_length=128)
    trusted = models.SmallIntegerField(default=0)
    status = models.SmallIntegerField(default=1)
    first_login_at = models.DateTimeField()
    last_active_at = models.DateTimeField()
    last_client_ip = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_user_device"
        unique_together = (("user", "fingerprint_hash"),)


class IamUserSession(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(IamUser, on_delete=models.DO_NOTHING, db_column="user_id", related_name="sessions")
    device = models.ForeignKey(IamUserDevice, on_delete=models.DO_NOTHING, db_column="device_id", related_name="sessions")
    session_id = models.CharField(max_length=64, unique=True)
    login_ip = models.CharField(max_length=64, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    risk_level = models.SmallIntegerField(default=0)
    last_active_at = models.DateTimeField()
    expired_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_user_session"


class IamUserToken(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(IamUser, on_delete=models.DO_NOTHING, db_column="user_id", related_name="tokens")
    session = models.ForeignKey(IamUserSession, on_delete=models.DO_NOTHING, db_column="session_id", related_name="tokens", null=True, blank=True)
    refresh_token_hash = models.CharField(max_length=64, unique=True, db_column="refresh_token_hash")
    access_jti = models.CharField(max_length=64, null=True, blank=True)
    refresh_jti = models.CharField(max_length=64, unique=True)
    client_ip = models.CharField(max_length=64, null=True, blank=True)
    user_agent = models.CharField(max_length=512, null=True, blank=True)
    expired_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_user_token"
        unique_together = (("user", "access_jti"),)


class IamLoginFailureLock(models.Model):
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(IamUser, on_delete=models.DO_NOTHING, db_column="user_id", null=True, blank=True)
    failed_count = models.IntegerField(default=0)
    locked_until = models.DateTimeField(null=True, blank=True)
    last_failed_at = models.DateTimeField(null=True, blank=True)
    last_client_ip = models.CharField(max_length=64, null=True, blank=True)
    last_user_agent = models.CharField(max_length=512, null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_login_failure_lock"


class IamOperationAudit(models.Model):
    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAILED = "FAILED"
    STATUS_CHOICES = ((STATUS_SUCCESS, "SUCCESS"), (STATUS_FAILED, "FAILED"))

    id = models.BigAutoField(primary_key=True)
    operator = models.ForeignKey(IamUser, on_delete=models.DO_NOTHING, db_column="operator_id", null=True, blank=True, related_name="operation_audits")
    operation_type = models.CharField(max_length=64)
    resource_type = models.CharField(max_length=64)
    company_id = models.BigIntegerField(null=True, blank=True)
    resource_id = models.BigIntegerField(null=True, blank=True)
    request_method = models.CharField(max_length=16, null=True, blank=True)
    request_path = models.CharField(max_length=255, null=True, blank=True)
    client_ip = models.CharField(max_length=64, null=True, blank=True)
    user_agent = models.CharField(max_length=512, null=True, blank=True)
    request_data = models.JSONField(null=True, blank=True)
    before_data = models.JSONField(null=True, blank=True)
    after_data = models.JSONField(null=True, blank=True)
    extra_data = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default=STATUS_SUCCESS)
    error_code = models.IntegerField(null=True, blank=True)
    error_message = models.CharField(max_length=512, null=True, blank=True)
    trace_id = models.CharField(max_length=64, null=True, blank=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_operation_audit"
