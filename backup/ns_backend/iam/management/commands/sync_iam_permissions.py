# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from asgiref.sync import async_to_sync
from django.core.management import BaseCommand

from ns_backend.iam.services import PermissionSyncService

if TYPE_CHECKING:
    pass


class Command(BaseCommand):
    help = "Sync IAM builtin and configured permission providers into iam_permission."

    def add_arguments(self, parser) -> None:
        """Register command arguments."""
        parser.add_argument("--operator-id", type=int, default=None, help="Operator user id for created_by/updated_by.")
        parser.add_argument("--builtin-only", action="store_true", help="Only sync IAM builtin permissions.")

    def handle(self, *args, **options) -> None:
        """Execute permission synchronization."""
        if options.get("builtin_only"):
            result = async_to_sync(PermissionSyncService.sync_builtin_permissions)(operator_id=options.get("operator_id"))
        else:
            result = async_to_sync(PermissionSyncService.sync_registered_permissions)(operator_id=options.get("operator_id"))

        self.stdout.write(self.style.SUCCESS(f"Synced IAM permissions: {result}"))
