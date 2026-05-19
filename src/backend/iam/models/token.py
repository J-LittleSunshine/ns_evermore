# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    pass

from .user import IamUser


class IamUserToken(models.Model):

    id = models.BigAutoField(primary_key=True)

    user = models.ForeignKey(
        IamUser,
        on_delete=models.DO_NOTHING,
        db_column="user_id",
        related_name="tokens",
        verbose_name="用户",
    )

    refresh_token = models.CharField(
        max_length=512,
        verbose_name="Refresh Token Hash",
    )

    access_jti = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name="Access Token JTI",
    )

    refresh_jti = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Refresh Token JTI",
    )

    client_ip = models.CharField(
        max_length=64,
        null=True,
        blank=True,
        verbose_name="客户端IP",
    )

    user_agent = models.CharField(
        max_length=512,
        null=True,
        blank=True,
        verbose_name="User-Agent",
    )

    expired_at = models.DateTimeField(verbose_name="过期时间")
    revoked_at = models.DateTimeField(null=True, blank=True, verbose_name="吊销时间")
    created_at = models.DateTimeField(verbose_name="创建时间")

    class Meta:
        managed = False
        db_table = "iam_user_token"
        verbose_name = "用户Token"
        verbose_name_plural = "用户Token"

    def __str__(self):
        return f"{self.user_id}:{self.refresh_jti}"
