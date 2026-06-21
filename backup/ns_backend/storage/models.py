# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.db import models

if TYPE_CHECKING:
    pass


class StorageObjectRef(models.Model):
    """Infrastructure object reference ledger.

    This model stores technical object metadata only.
    It must not contain business attachment semantics.
    """

    id = models.BigAutoField(primary_key=True)
    bucket = models.CharField(max_length=63)
    object_name = models.CharField(max_length=1024)
    backend = models.CharField(max_length=32)
    module_code = models.CharField(max_length=64)
    resource_type = models.CharField(max_length=128)
    resource_id = models.CharField(max_length=128, null=True, blank=True)
    original_filename = models.CharField(max_length=255, null=True, blank=True)
    content_type = models.CharField(max_length=128, null=True, blank=True)
    object_size = models.BigIntegerField(null=True, blank=True)
    etag = models.CharField(max_length=128, null=True, blank=True)
    sha256 = models.CharField(max_length=64, null=True, blank=True)
    version_id = models.CharField(max_length=128, null=True, blank=True)
    metadata_json = models.JSONField(default=dict)
    created_by = models.BigIntegerField(null=True, blank=True)
    updated_by = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "storage_object_ref"
        indexes = [
            models.Index(
                fields=[
                    "module_code",
                    "resource_type",
                    "resource_id"
                ], name="idx_storage_obj_ref_res"
            ),
            models.Index(
                fields=[
                    "sha256"
                ], name="idx_storage_obj_ref_sha256"
            ),
            models.Index(
                fields=[
                    "created_at"
                ], name="idx_storage_obj_ref_created"
            ),
            models.Index(
                fields=[
                    "deleted_at"
                ], name="idx_storage_obj_ref_deleted"
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "bucket",
                    "object_name"
                ], name="uk_storage_obj_ref_bucket_name"
            ),
        ]
