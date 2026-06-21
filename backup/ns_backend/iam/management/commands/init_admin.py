# -*- coding: utf-8 -*-
from __future__ import annotations

from argparse import ArgumentParser
from typing import TYPE_CHECKING, Any

from django.core.management.base import BaseCommand, CommandError

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.services import AdminService

if TYPE_CHECKING:
    pass


class Command(BaseCommand):
    """Initialize IAM platform administrator."""

    help = "Initialize IAM platform administrator."

    def add_arguments(self, parser: ArgumentParser) -> None:
        """Register command arguments."""
        parser.add_argument("--username", type=str, default=AdminService.DEFAULT_USERNAME, help="Administrator username. Default: admin.")
        parser.add_argument("--password", type=str, default=None, help="Administrator initial password. If omitted, a random password is generated.")
        parser.add_argument("--display-name", type=str, default=AdminService.DEFAULT_DISPLAY_NAME, help="Administrator display name.")

    def handle(self, *args: Any, **options: Any) -> None:
        """Execute administrator initialization."""
        try:
            result = AdminService.initialize_admin(
                username=options.get("username"),
                password=options.get("password"),
                display_name=options.get("display_name"),
            )
        except BusinessError as exc:
            raise CommandError(str(exc)) from exc

        if not result["created"]:
            self.stdout.write(self.style.WARNING(f"Administrator user already exists: {result['username']}"))
            return

        self.stdout.write(self.style.SUCCESS(f"System administrator created successfully. UserID: {result['user_id']}"))

        if result.get("password_generated"):
            self.stdout.write(self.style.WARNING(f"Initial password: {result['initial_password']}"))
        else:
            self.stdout.write(self.style.WARNING("Initial password was provided by --password and has been applied."))

        self.stdout.write(self.style.WARNING("Please change your password immediately after first login."))
