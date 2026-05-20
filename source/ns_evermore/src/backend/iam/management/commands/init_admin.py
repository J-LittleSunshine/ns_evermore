# -*- coding: utf-8 -*-
from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

from django.contrib.auth.hashers import make_password
from django.core.management import BaseCommand
from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from iam.models import IamUser

if TYPE_CHECKING:
    pass


class Command(BaseCommand):
    help = "Initialize IAM System Administrator"

    def add_arguments(self, parser):
        parser.add_argument("--username", type=str, default="admin", help="Administrator username, default: admin")
        parser.add_argument("--password", type=str, default=None, help="Administrator Initial Password: If not specified, a random password will be automatically generated.")

    def handle(self, *args, **options):
        username = options["username"]
        raw_password = options["password"] or secrets.token_urlsafe(16)

        exists = IamUser.objects.using(IAM_DB_ALIAS).filter(username=username).exists()

        if exists:
            self.stdout.write(self.style.WARNING(f"Administrator user already exits: {username}"))
            return
        now = timezone.now()
        user = IamUser.objects.using(IAM_DB_ALIAS).create(
            username=username,
            password=make_password(raw_password),
            display_name="System Administrator",
            user_type="ENTERPRISE",
            is_active=1,
            is_staff=1,
            is_superuser=1,
            created_at=now,
            updated_at=now,
        )

        self.stdout.write(self.style.SUCCESS(f"System administrator create success. UserID: {user.id}"))

        self.stdout.write(self.style.WARNING(f"Initial password：{raw_password}"))

        self.stdout.write(self.style.WARNING("Please change your password immediately after your first login."))
