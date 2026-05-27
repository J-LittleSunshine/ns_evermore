# -*- coding: utf-8 -*-
from __future__ import annotations

from argparse import ArgumentParser

from django.core.management.base import BaseCommand, CommandError

from ns_backend.infra_schema import install_infra_schema


class Command(BaseCommand):
    help = "Install static infrastructure schema SQL for configured domain."

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--domain",
            type=str,
            default="iam",
            help="Infrastructure domain name, default: iam",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only print install plan without executing SQL.",
        )

    def handle(self, *args: object, **options: object) -> None:
        domain = options.get("domain", "iam")
        dry_run = bool(options.get("dry_run", False))

        try:
            result = install_infra_schema(str(domain), dry_run=dry_run)
        except (ValueError, FileNotFoundError, RuntimeError) as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(f"infra_domain: {result.infra_domain}")
        self.stdout.write(f"db_alias: {result.db_alias}")
        self.stdout.write(f"vendor: {result.vendor}")
        self.stdout.write(f"sql_path: {result.sql_path}")
        self.stdout.write(f"expected_tables: {', '.join(result.expected_tables)}")
        self.stdout.write(f"existing_tables: {', '.join(result.existing_tables)}")
        self.stdout.write(f"dry_run: {result.dry_run}")
        self.stdout.write(f"skipped: {result.skipped}")
        self.stdout.write(f"executed_statement_count: {result.executed_statement_count}")

        if result.skipped:
            self.stdout.write(self.style.WARNING("Infrastructure schema already installed, skipped."))
            return

        if result.dry_run:
            self.stdout.write(self.style.WARNING("Dry-run completed, SQL statements were not executed."))
            return

        self.stdout.write(self.style.SUCCESS("Infrastructure schema install completed."))

