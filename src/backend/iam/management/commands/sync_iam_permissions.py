# -*- coding: utf-8 -*-
from __future__ import annotations

from asgiref.sync import async_to_sync
from django.core.management.base import BaseCommand

from iam.services.permission_sync import PermissionSyncService


class Command(BaseCommand):
    help = "sync_iam_permissions: Sync registered permission providers into iam_permission."

    def add_arguments(self, parser):
        parser.add_argument(
            "--operator-id",
            type=int,
            default=None,
            help="Operator user id for created_by/updated_by.",
        )
        parser.add_argument(
            "--builtin-only",
            action="store_true",
            help="Only sync IAM builtin permissions.",
        )

    def handle(self, *args, **options):
        if options.get("builtin_only"):
            result = async_to_sync(PermissionSyncService.sync_builtin_permissions)(
                operator_id=options.get("operator_id"),
            )
        else:
            result = async_to_sync(PermissionSyncService.sync_registered_permissions)(
                operator_id=options.get("operator_id"),
            )
        self.stdout.write(self.style.SUCCESS(f"Synced IAM permissions: {result}"))
