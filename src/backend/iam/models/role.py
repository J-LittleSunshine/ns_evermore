# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from .permission import IamPermission
from .user import IamUser

if TYPE_CHECKING:
    pass


class IamRole(models.Model):
    SCOPE_PERSONAL = "PERSONAL"
    SCOPE_ENTERPRISE = "ENTERPRISE"

    SCOPE_CHOICES = (
        (SCOPE_PERSONAL, "个人体系"),
        (SCOPE_ENTERPRISE, "企业体系"),
    )

    id = models.BigAutoField(primary_key=True)
    role_code = models.CharField(max_length=64, unique=True)
    role_name = models.CharField(max_length=128)
    role_scope = models.CharField(max_length=32, choices=SCOPE_CHOICES)
    status = models.SmallIntegerField(default=1)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_role"
        verbose_name = "角色"
        verbose_name_plural = "角色"

    def __str__(self):
        return self.role_name


class IamRolePermission(models.Model):
    id = models.BigAutoField(primary_key=True)
    role = models.ForeignKey(IamRole, on_delete=models.DO_NOTHING, db_column="role_id")
    permission = models.ForeignKey(IamPermission, on_delete=models.DO_NOTHING, db_column="permission_id")
    granted_by = models.ForeignKey(
        IamUser,
        on_delete=models.DO_NOTHING,
        db_column="granted_by",
        null=True,
        blank=True,
    )
    expired_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_role_permission"
        unique_together = (("role", "permission"),)


class IamUserRole(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(IamUser, on_delete=models.DO_NOTHING, db_column="user_id")
    role = models.ForeignKey(IamRole, on_delete=models.DO_NOTHING, db_column="role_id")
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_user_role"
        unique_together = (("user", "role"),)
