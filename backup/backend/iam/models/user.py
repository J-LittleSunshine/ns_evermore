# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db import models

from .company import IamCompany
from .department import IamSubsidiary, IamDepartment


class IamUser(models.Model):
    USER_TYPE_PERSONAL = "PERSONAL"
    USER_TYPE_ENTERPRISE = "ENTERPRISE"

    USER_TYPE_CHOICES = (
        (USER_TYPE_PERSONAL, "Personal user"),
        (USER_TYPE_ENTERPRISE, "Enterprise user"),
    )

    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=64, unique=True)
    password = models.CharField(max_length=128)
    email = models.CharField(max_length=128, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=32, unique=True, null=True, blank=True)
    display_name = models.CharField(max_length=64, null=True, blank=True)
    user_type = models.CharField(max_length=32, choices=USER_TYPE_CHOICES)

    company = models.ForeignKey(
        IamCompany,
        on_delete=models.DO_NOTHING,
        db_column="company_id",
        null=True,
        blank=True,
    )
    subsidiary = models.ForeignKey(
        IamSubsidiary,
        on_delete=models.DO_NOTHING,
        db_column="subsidiary_id",
        null=True,
        blank=True,
    )
    department = models.ForeignKey(
        IamDepartment,
        on_delete=models.DO_NOTHING,
        db_column="department_id",
        null=True,
        blank=True,
    )

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
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.display_name or self.username
