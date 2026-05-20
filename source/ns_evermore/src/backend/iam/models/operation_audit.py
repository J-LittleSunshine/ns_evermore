# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db import models

from .user import IamUser


class IamOperationAudit(models.Model):
    id = models.BigAutoField(primary_key=True)
    operator = models.ForeignKey(
        IamUser,
        on_delete=models.DO_NOTHING,
        db_column="operator_id",
        null=True,
        blank=True,
        related_name="operation_audits",
    )
    operation_type = models.CharField(max_length=64)
    resource_type = models.CharField(max_length=64)
    resource_id = models.BigIntegerField(null=True, blank=True)
    request_path = models.CharField(max_length=255, null=True, blank=True)
    client_ip = models.CharField(max_length=64, null=True, blank=True)
    user_agent = models.CharField(max_length=512, null=True, blank=True)
    request_data = models.JSONField(null=True, blank=True)
    before_data = models.JSONField(null=True, blank=True)
    after_data = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_operation_audit"
        verbose_name = "操作审计"
        verbose_name_plural = "操作审计"
