# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db import models

from .device import IamUserSession
from .user import IamUser


class IamUserToken(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(
        IamUser,
        on_delete=models.DO_NOTHING,
        db_column="user_id",
        related_name="tokens",
        verbose_name="User",
    )
    session = models.ForeignKey(
        IamUserSession,
        on_delete=models.DO_NOTHING,
        db_column="session_id",
        related_name="tokens",
        null=True,
        blank=True,
        verbose_name="Session",
    )
    refresh_token_hash = models.CharField(
        max_length=64,
        unique=True,
        db_column="refresh_token_hash",
        verbose_name="Refresh Token Hash",
    )
    access_jti = models.CharField(max_length=64, null=True, blank=True, verbose_name="Access Token JTI")
    refresh_jti = models.CharField(max_length=64, unique=True, verbose_name="Refresh Token JTI")
    client_ip = models.CharField(max_length=64, null=True, blank=True, verbose_name="Client IP")
    user_agent = models.CharField(max_length=512, null=True, blank=True, verbose_name="User-Agent")
    expired_at = models.DateTimeField(verbose_name="Expiration time")
    revoked_at = models.DateTimeField(null=True, blank=True, verbose_name="Revocation time")
    created_at = models.DateTimeField(verbose_name="Creation time")

    class Meta:
        managed = False
        db_table = "iam_user_token"
        unique_together = (("user", "access_jti"),)
        verbose_name = "User token"
        verbose_name_plural = "User tokens"

    def __str__(self):
        return f"{self.user_id}:{self.refresh_jti}"
