# -*- coding: utf-8 -*-
from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.contrib.auth.hashers import make_password
from django.core.management.base import (
    BaseCommand,
    CommandError,
)
from django.db import (
    connections,
    transaction,
)
from django.utils import timezone

from backend.common import BaseRepository
from ns_backend.iam.models import IamUser

if TYPE_CHECKING:
    from argparse import ArgumentParser


@dataclass(slots=True, kw_only=True)
class SeedUserSpec:
    username: str
    raw_password: str
    display_name: str
    user_type: str
    is_staff: int
    is_superuser: int
    password_generated: bool


class Command(BaseCommand):
    help = "Initialize built-in IAM admin and dev users."

    DEFAULT_ADMIN_USERNAME = "admin"
    DEFAULT_DEV_USERNAME = "dev"

    GENERATED_PASSWORD_LENGTH = 24

    def add_arguments(self, parser: "ArgumentParser") -> None:
        parser.add_argument(
            "--database",
            default="",
            help="Django database alias. Default: resolve by IAM database router mapping."
        )

        parser.add_argument(
            "--admin-username",
            default=self.DEFAULT_ADMIN_USERNAME,
            help=f"Admin username. Default: {self.DEFAULT_ADMIN_USERNAME}.",
        )
        parser.add_argument(
            "--admin-password",
            default="",
            help="Admin password. If omitted, a random password will be generated.",
        )

        parser.add_argument(
            "--dev-username",
            default=self.DEFAULT_DEV_USERNAME,
            help=f"Dev username. Default: {self.DEFAULT_DEV_USERNAME}.",
        )
        parser.add_argument(
            "--dev-password",
            default="",
            help="Dev password. If omitted, a random password will be generated.",
        )

        parser.add_argument(
            "--no-reset-password",
            action="store_true",
            help="Do not reset password if user already exists.",
        )

    def handle(self, *args: object, **options: object) -> None:
        database_alias = self.resolve_database_alias(str(options.get("database", "") or "").strip())

        admin_username = self.normalize_username(options["admin_username"],"admin_username")
        dev_username = self.normalize_username(options["dev_username"],"dev_username")

        if admin_username == dev_username:
            raise CommandError("admin username and dev username must be different.")

        admin_password, admin_password_generated = self.resolve_password(explicit_password=str(options.get("admin_password", "") or ""))
        dev_password, dev_password_generated = self.resolve_password(explicit_password=str(options.get("dev_password", "") or ""))

        no_reset_password = bool(options.get("no_reset_password"))

        admin_spec = SeedUserSpec(
            username=admin_username,
            raw_password=admin_password,
            display_name="System Administrator",
            user_type=IamUser.USER_TYPE_PERSONAL,
            is_staff=1,
            is_superuser=1,
            password_generated=admin_password_generated,
        )
        dev_spec = SeedUserSpec(
            username=dev_username,
            raw_password=dev_password,
            display_name="Development User",
            user_type=IamUser.USER_TYPE_PERSONAL,
            is_staff=0,
            is_superuser=0,
            password_generated=dev_password_generated,
        )

        self.stdout.write(
            self.style.NOTICE(
                f"Initializing IAM built-in users on database alias '{database_alias}'."
            )
        )

        results = []
        with transaction.atomic(using=database_alias):
            results.append(
                self.upsert_user(
                    database_alias=database_alias,
                    spec=admin_spec,
                    no_reset_password=no_reset_password,
                )
            )
            results.append(
                self.upsert_user(
                    database_alias=database_alias,
                    spec=dev_spec,
                    no_reset_password=no_reset_password,
                )
            )

        self.stdout.write("")

        for result in results:
            username = result["username"]
            action = result["action"]
            password_changed = result["password_changed"]
            raw_password = result["raw_password"]
            password_generated = result["password_generated"]

            self.stdout.write(
                self.style.SUCCESS(
                    f"IAM user '{username}' {action}."
                )
            )

            if password_changed:
                password_source = "generated" if password_generated else "provided"
                self.stdout.write(
                    self.style.WARNING(
                        f"Initial password for '{username}' ({password_source}, shown once): {raw_password}"
                    )
                )
            else:
                self.stdout.write(
                    self.style.NOTICE(
                        f"Password for '{username}' was not changed."
                    )
                )

        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                "Store generated passwords securely. They cannot be displayed again."
            )
        )

    @staticmethod
    def normalize_username(value: object, field_name: str) -> str:
        username = str(value or "").strip()

        if not username:
            raise CommandError(f"{field_name} must not be empty.")

        if len(username) > 64:
            raise CommandError(f"{field_name} must not exceed 64 characters.")

        return username

    @classmethod
    def resolve_password(cls, *, explicit_password: str) -> tuple[str, bool]:
        password = str(explicit_password or "")

        if password:
            return password, False

        return cls.generate_password(), True

    @classmethod
    def generate_password(cls) -> str:
        uppercase = "ABCDEFGHJKLMNPQRSTUVWXYZ"
        lowercase = "abcdefghijkmnopqrstuvwxyz"
        digits = "23456789"
        symbols = "!@#$%^&*-_=+"
        alphabet = uppercase + lowercase + digits + symbols

        required_chars = [
            secrets.choice(uppercase),
            secrets.choice(lowercase),
            secrets.choice(digits),
            secrets.choice(symbols),
        ]

        remaining_length = cls.GENERATED_PASSWORD_LENGTH - len(required_chars)
        remaining_chars = [
            secrets.choice(alphabet)
            for _ in range(remaining_length)
        ]

        chars = required_chars + remaining_chars
        secrets.SystemRandom().shuffle(chars)

        return "".join(chars)

    @staticmethod
    def resolve_database_alias(database_alias: str) -> str:
        if database_alias:
            resolved_alias = database_alias
        else:
            resolved_alias = BaseRepository.resolve_db_alias(IamUser)

        if resolved_alias not in connections.databases:
            available_aliases = ", ".join(sorted(connections.databases))
            raise CommandError(
                f"Unknown database alias: {resolved_alias}. "
                f"Available aliases: {available_aliases}"
            )

        return resolved_alias

    @staticmethod
    def upsert_user(*,database_alias: str,spec: SeedUserSpec,no_reset_password: bool) -> dict[str, object]:
        now = timezone.now()

        user = (
            IamUser.objects.using(database_alias)
            .filter(username=spec.username)
            .first()
        )

        if user is None:
            IamUser.objects.using(database_alias).create(
                username=spec.username,
                password=make_password(spec.raw_password),
                email=None,
                phone=None,
                display_name=spec.display_name,
                user_type=spec.user_type,
                company_id=None,
                subsidiary_id=None,
                department_id=None,
                is_active=1,
                is_staff=spec.is_staff,
                is_superuser=spec.is_superuser,
                last_login=None,
                created_by=None,
                updated_by=None,
                created_at=now,
                updated_at=now,
            )
            return {
                "username": spec.username,
                "action": "created",
                "password_changed": True,
                "raw_password": spec.raw_password,
                "password_generated": spec.password_generated,
            }

        update_fields = [
            "display_name",
            "user_type",
            "company_id",
            "subsidiary_id",
            "department_id",
            "is_active",
            "is_staff",
            "is_superuser",
            "updated_at",
        ]

        user.display_name = spec.display_name
        user.user_type = spec.user_type
        user.company_id = None
        user.subsidiary_id = None
        user.department_id = None
        user.is_active = 1
        user.is_staff = spec.is_staff
        user.is_superuser = spec.is_superuser
        user.updated_at = now

        password_changed = not no_reset_password

        if password_changed:
            user.password = make_password(spec.raw_password)
            update_fields.append("password")

        user.save(
            using=database_alias,
            update_fields=update_fields,
        )

        return {
            "username": spec.username,
            "action": "updated",
            "password_changed": password_changed,
            "raw_password": spec.raw_password if password_changed else "",
            "password_generated": spec.password_generated if password_changed else False,
        }
