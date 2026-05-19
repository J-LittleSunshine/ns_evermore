# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

from .company import IamCompany

if TYPE_CHECKING:
    pass


class IamSubsidiary(models.Model):
    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(IamCompany, on_delete=models.DO_NOTHING, db_column="company_id")
    subsidiary_code = models.CharField(max_length=64, unique=True)
    subsidiary_name = models.CharField(max_length=128)
    status = models.SmallIntegerField(default=1)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_subsidiary"
        verbose_name = "子公司"
        verbose_name_plural = "子公司"


class IamDepartment(models.Model):
    id = models.BigAutoField(primary_key=True)
    company = models.ForeignKey(IamCompany, on_delete=models.DO_NOTHING, db_column="company_id")
    subsidiary = models.ForeignKey(
        IamSubsidiary,
        on_delete=models.DO_NOTHING,
        db_column="subsidiary_id",
        null=True,
        blank=True,
    )
    parent = models.ForeignKey(
        "self",
        on_delete=models.DO_NOTHING,
        db_column="parent_id",
        null=True,
        blank=True,
    )
    department_code = models.CharField(max_length=64, unique=True)
    department_name = models.CharField(max_length=128)
    status = models.SmallIntegerField(default=1)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_department"
        verbose_name = "部门"
        verbose_name_plural = "部门"
