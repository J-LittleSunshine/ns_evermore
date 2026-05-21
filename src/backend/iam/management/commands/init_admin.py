# -*- coding: utf-8 -*-
from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

from django.contrib.auth.hashers import make_password
from django.core.management import BaseCommand
from django.utils import timezone

from iam.repositories.admin import AdminRepository

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
        now = timezone.now()
        exists = AdminRepository.exists_by_username(username)

        if exists:
            self.stdout.write(self.style.WARNING(f"Administrator user already exits: {username}"))
            return

        user = AdminRepository.create_admin_user({
            "username": username,
            "password": make_password(raw_password),
            "display_name": "System Administrator",
            "user_type": "ENTERPRISE",
            "is_active": 1,
            "is_staff": 1,
            "is_superuser": 1,
            "created_at": now,
            "updated_at": now,
        })

        self.stdout.write(self.style.SUCCESS(f"System administrator create success. UserID: {user.id}"))

        self.stdout.write(self.style.WARNING(f"Initial password：{raw_password}"))

        self.stdout.write(self.style.WARNING("Please change your password immediately after your first login."))
