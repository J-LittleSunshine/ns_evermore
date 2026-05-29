# -*- coding: utf-8 -*-
from __future__ import annotations

from django.db import models

from .user import IamUser


class IamUserDevice(models.Model):
    id = models.BigAutoField(primary_key=True)

    user = models.ForeignKey(
        IamUser,
        on_delete=models.DO_NOTHING,
        db_column="user_id",
        related_name="devices",
    )

    device_id = models.CharField(max_length=128, unique=True)
    device_name = models.CharField(max_length=128)
    device_type = models.CharField(max_length=32)

    os_name = models.CharField(max_length=64, null=True, blank=True)
    browser_name = models.CharField(max_length=64, null=True, blank=True)

    fingerprint_hash = models.CharField(max_length=128)

    trusted = models.SmallIntegerField(default=0)
    status = models.SmallIntegerField(default=1)

    first_login_at = models.DateTimeField()
    last_active_at = models.DateTimeField()

    last_client_ip = models.CharField(max_length=64, null=True, blank=True)

    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_user_device"
        unique_together = (("user", "fingerprint_hash"),)


class IamUserSession(models.Model):
    id = models.BigAutoField(primary_key=True)

    user = models.ForeignKey(
        IamUser,
        on_delete=models.DO_NOTHING,
        db_column="user_id",
        related_name="sessions",
    )

    device = models.ForeignKey(
        IamUserDevice,
        on_delete=models.DO_NOTHING,
        db_column="device_id",
        related_name="sessions",
    )

    session_id = models.CharField(max_length=64, unique=True)

    login_ip = models.CharField(max_length=64, null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    risk_level = models.SmallIntegerField(default=0)

    last_active_at = models.DateTimeField()
    expired_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "iam_user_session"
