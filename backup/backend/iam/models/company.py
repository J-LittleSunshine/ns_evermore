# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db import models


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
        verbose_name = "Company"
        verbose_name_plural = "Companies"
