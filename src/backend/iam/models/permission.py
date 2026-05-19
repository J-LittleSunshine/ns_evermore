# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    pass

class IamPermission(models.Model):
    TYPE_MENU = "MENU"
    TYPE_ACTION = "ACTION"
    TYPE_DATA = "DATA"

    TYPE_CHOICES = (
        (TYPE_MENU, "菜单权限"),
        (TYPE_ACTION, "操作权限"),
        (TYPE_DATA, "数据权限"),
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
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_permission"
        verbose_name = "权限"
        verbose_name_plural = "权限"

    def __str__(self):
        return self.permission_name
