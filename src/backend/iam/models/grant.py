# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db import models

from iam.constants import DATA_SCOPE_CHOICES

from .department import IamDepartment, IamSubsidiary
from .permission import IamPermission
from .user import IamUser


class IamUserPermission(models.Model):
    EFFECT_ALLOW = "ALLOW"
    EFFECT_DENY = "DENY"

    EFFECT_CHOICES = (
        (EFFECT_ALLOW, "允许"),
        (EFFECT_DENY, "拒绝"),
    )

    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        IamUser,
        on_delete=models.DO_NOTHING,
        db_column="user_id",
        related_name="direct_permissions",
        verbose_name="用户",
    )
    permission = models.ForeignKey(
        IamPermission,
        on_delete=models.DO_NOTHING,
        db_column="permission_id",
        related_name="user_grants",
        verbose_name="权限",
    )
    effect = models.CharField(
        max_length=16,
        choices=EFFECT_CHOICES,
        default=EFFECT_ALLOW,
        verbose_name="权限效果",
    )
    data_scope = models.CharField(
        max_length=32,
        choices=DATA_SCOPE_CHOICES,
        null=True,
        blank=True,
        verbose_name="数据权限范围",
    )
    granted_by = models.ForeignKey(
        IamUser,
        on_delete=models.DO_NOTHING,
        db_column="granted_by",
        null=True,
        blank=True,
        related_name="granted_user_permissions",
        verbose_name="授权人",
    )
    expired_at = models.DateTimeField(null=True, blank=True, verbose_name="过期时间")
    created_by = models.BigIntegerField(null=True, blank=True)
    updated_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="创建时间")
    updated_at = models.DateTimeField(verbose_name="更新时间")

    class Meta:
        managed = False
        db_table = "iam_user_permission"
        unique_together = (("user", "permission"),)
        verbose_name = "用户直接权限"
        verbose_name_plural = "用户直接权限"

    def __str__(self):
        return f"{self.user_id}:{self.permission_id}:{self.effect}"


class IamDepartmentPermission(models.Model):
    EFFECT_ALLOW = "ALLOW"
    EFFECT_DENY = "DENY"

    EFFECT_CHOICES = (
        (EFFECT_ALLOW, "允许"),
        (EFFECT_DENY, "拒绝"),
    )

    id = models.BigAutoField(primary_key=True)
    department = models.ForeignKey(
        IamDepartment,
        on_delete=models.DO_NOTHING,
        db_column="department_id",
        related_name="permission_grants",
        verbose_name="部门",
    )
    permission = models.ForeignKey(
        IamPermission,
        on_delete=models.DO_NOTHING,
        db_column="permission_id",
        related_name="department_grants",
        verbose_name="权限",
    )
    effect = models.CharField(
        max_length=16,
        choices=EFFECT_CHOICES,
        default=EFFECT_ALLOW,
        verbose_name="权限效果",
    )
    data_scope = models.CharField(
        max_length=32,
        choices=DATA_SCOPE_CHOICES,
        null=True,
        blank=True,
        verbose_name="数据权限范围",
    )
    granted_by = models.ForeignKey(
        IamUser,
        on_delete=models.DO_NOTHING,
        db_column="granted_by",
        null=True,
        blank=True,
        related_name="granted_department_permissions",
        verbose_name="授权人",
    )
    expired_at = models.DateTimeField(null=True, blank=True, verbose_name="过期时间")
    created_by = models.BigIntegerField(null=True, blank=True)
    updated_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="创建时间")
    updated_at = models.DateTimeField(verbose_name="更新时间")

    class Meta:
        managed = False
        db_table = "iam_department_permission"
        unique_together = (("department", "permission"),)
        verbose_name = "部门权限"
        verbose_name_plural = "部门权限"

    def __str__(self):
        return f"{self.department_id}:{self.permission_id}:{self.effect}"


class IamSubsidiaryPermission(models.Model):
    EFFECT_ALLOW = "ALLOW"
    EFFECT_DENY = "DENY"

    EFFECT_CHOICES = (
        (EFFECT_ALLOW, "允许"),
        (EFFECT_DENY, "拒绝"),
    )

    id = models.BigAutoField(primary_key=True)
    subsidiary = models.ForeignKey(
        IamSubsidiary,
        on_delete=models.DO_NOTHING,
        db_column="subsidiary_id",
        related_name="permission_grants",
        verbose_name="子公司",
    )
    permission = models.ForeignKey(
        IamPermission,
        on_delete=models.DO_NOTHING,
        db_column="permission_id",
        related_name="subsidiary_grants",
        verbose_name="权限",
    )
    effect = models.CharField(
        max_length=16,
        choices=EFFECT_CHOICES,
        default=EFFECT_ALLOW,
        verbose_name="权限效果",
    )
    data_scope = models.CharField(
        max_length=32,
        choices=DATA_SCOPE_CHOICES,
        null=True,
        blank=True,
        verbose_name="数据权限范围",
    )
    granted_by = models.ForeignKey(
        IamUser,
        on_delete=models.DO_NOTHING,
        db_column="granted_by",
        null=True,
        blank=True,
        related_name="granted_subsidiary_permissions",
        verbose_name="授权人",
    )
    expired_at = models.DateTimeField(null=True, blank=True, verbose_name="过期时间")
    created_by = models.BigIntegerField(null=True, blank=True)
    updated_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(verbose_name="创建时间")
    updated_at = models.DateTimeField(verbose_name="更新时间")

    class Meta:
        managed = False
        db_table = "iam_subsidiary_permission"
        unique_together = (("subsidiary", "permission"),)
        verbose_name = "子公司权限"
        verbose_name_plural = "子公司权限"

    def __str__(self):
        return f"{self.subsidiary_id}:{self.permission_id}:{self.effect}"
