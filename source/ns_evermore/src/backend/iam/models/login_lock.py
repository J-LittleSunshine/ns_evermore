# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db import models

from .user import IamUser


class IamLoginFailureLock(models.Model):
    id = models.BigAutoField(primary_key=True)
    username = models.CharField(max_length=64, unique=True)
    user = models.ForeignKey(
        IamUser,
        on_delete=models.DO_NOTHING,
        db_column="user_id",
        null=True,
        blank=True,
    )
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
        verbose_name = "登录失败锁定"
        verbose_name_plural = "登录失败锁定"

    def __str__(self):
        return self.username
