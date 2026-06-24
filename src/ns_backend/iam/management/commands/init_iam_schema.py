# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from backend.db import SqlScriptRunner

if TYPE_CHECKING:
    from argparse import ArgumentParser


class Command(BaseCommand):
    help = "Initialize IAM database schema on the selected database alias."

    SQL_GROUP = "iam"

    def add_arguments(self, parser: "ArgumentParser") -> None:
        parser.add_argument(
            "--database",
            default="default",
            help="Django database alias to initialize. Default: default.",
        )
        parser.add_argument(
            "--sql-file",
            default="",
            help="Optional explicit SQL file path. Normally omit this and let the command choose by database vendor."
        )

    def handle(self, *args: object, **options: object) -> None:
        database_alias = str(options["database"]).strip()
        explicit_sql_file = str(options.get("sql_file", "") or "").strip()

        if not database_alias:
            raise CommandError("--database must not be empty.")

        self.stdout.write(self.style.NOTICE(f"Initializing IAM schema on database alias '{database_alias}'."))

        vendor, sql_file_path = SqlScriptRunner.run_create_script(
            database_alias=database_alias,
            sql_group=self.SQL_GROUP,
            explicit_sql_file=explicit_sql_file,
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"IAM schema initialized on database alias '{database_alias}' "
                f"with vendor '{vendor}' using SQL file: {sql_file_path}"
            )
        )
