# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db import models


class IamPermission(models.Model):
    TYPE_MENU = "MENU"
    TYPE_ACTION = "ACTION"
    TYPE_DATA = "DATA"

    TYPE_CHOICES = (
        (TYPE_MENU, "Menu permission"),
        (TYPE_ACTION, "Action permission"),
        (TYPE_DATA, "Data permission"),
    )

    id = models.BigAutoField(primary_key=True)
    permission_code = models.CharField(max_length=128, unique=True)
    permission_name = models.CharField(max_length=128)
    permission_type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    parent = models.ForeignKey(
        "self",
        on_delete=models.DO_NOTHING,
        db_column="parent_id",
        null=True,
        blank=True,
    )
    status = models.SmallIntegerField(default=1)
    created_by = models.BigIntegerField(null=True, blank=True)
    updated_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_permission"
        verbose_name = "Permission"
        verbose_name_plural = "Permissions"

    def __str__(self):
        return self.permission_name
