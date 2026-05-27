# -*- coding: utf-8 -*-
from __future__ import annotations

import secrets
from argparse import ArgumentParser
from typing import TYPE_CHECKING

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from iam.constants import IAM_DB_ALIAS
from iam.repositories.admin import AdminRepository

if TYPE_CHECKING:
    pass


class Command(BaseCommand):
    help = "Initialize IAM System Administrator"

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument("--username", type=str, default="admin", help="Administrator username, default: admin")
        parser.add_argument("--password", type=str, default=None, help="Administrator Initial Password: If not specified, a random password will be automatically generated.")
        parser.add_argument("--display-name", type=str, default="System Administrator", help="Administrator display name, default: System Administrator")

    def handle(self, *args: object, **options: object) -> None:
        username = str(options.get("username", "admin")).strip()
        if not username:
            raise CommandError("Administrator username must not be empty.")

        display_name = str(options.get("display_name", "System Administrator")).strip() or "System Administrator"

        password_option = options.get("password")
        is_random_password = password_option is None
        if is_random_password:
            raw_password = secrets.token_urlsafe(16)
        else:
            raw_password = str(password_option)
            if not raw_password.strip():
                raise CommandError("Administrator password must not be empty when --password is provided.")

        now = timezone.now()

        # 关键路径：管理员检测与创建在同一事务中执行，避免并发初始化导致脏数据。
        with transaction.atomic(using=IAM_DB_ALIAS):
            exists = AdminRepository.exists_by_username(username)

            if exists:
                self.stdout.write(self.style.WARNING(f"Administrator user already exists: {username}"))
                return

            user = AdminRepository.create_admin_user({
                "username": username,
                "password": make_password(raw_password),
                "display_name": display_name,
                "user_type": "ENTERPRISE",
                "is_active": 1,
                "is_staff": 1,
                "is_superuser": 1,
                "created_at": now,
                "updated_at": now,
            })

        self.stdout.write(self.style.SUCCESS(f"System administrator create success. UserID: {user.id}"))

        if is_random_password:
            self.stdout.write(self.style.WARNING(f"Initial password: {raw_password}"))
        else:
            self.stdout.write(self.style.WARNING("Initial password was provided by --password and has been applied."))

        self.stdout.write(self.style.WARNING("Please change your password immediately after your first login."))
