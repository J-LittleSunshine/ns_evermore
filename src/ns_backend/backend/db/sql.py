# -*- coding: utf-8 -*-
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from django.core.management.base import CommandError
from django.db import connections

from backend.db.vendor import (
    DB_VENDOR_SQLITE,
    DB_VENDOR_UNKNOWN,
    detect_db_vendor_from_connection,
)
from ns_common.paths import SQL_DIR

if TYPE_CHECKING:
    from django.db.backends.base.base import BaseDatabaseWrapper


class SqlScriptRunner:
    DEFAULT_SQL_ENCODING = "utf-8"

    @classmethod
    def get_connection(cls, database_alias: str) -> "BaseDatabaseWrapper":
        alias = str(database_alias or "").strip()

        if not alias:
            raise CommandError("database alias must not be empty.")

        if alias not in connections.databases:
            available_aliases = ", ".join(sorted(connections.databases))
            raise CommandError(f"Unknown database alias: {alias}. Available aliases: {available_aliases}")

        return connections[alias]

    @classmethod
    def detect_vendor(cls, connection: "BaseDatabaseWrapper") -> str:
        vendor = detect_db_vendor_from_connection(connection)

        if vendor == DB_VENDOR_UNKNOWN:
            raise CommandError(f"Cannot detect database vendor for alias '{connection.alias}'.")

        return vendor

    @classmethod
    def get_sql_file_path(cls, *, sql_group: str, database_vendor: str, explicit_sql_file: str = "") -> Path:
        if explicit_sql_file:
            return Path(explicit_sql_file).expanduser().resolve()

        return SQL_DIR / "create" / sql_group / f"{database_vendor}.sql"

    @classmethod
    def read_sql(cls, sql_file_path: Path) -> str:
        if not sql_file_path.exists():
            raise CommandError(f"SQL file does not exist: {sql_file_path}")

        if not sql_file_path.is_file():
            raise CommandError(f"SQL path is not a file: {sql_file_path}")

        sql_text = sql_file_path.read_text(encoding=cls.DEFAULT_SQL_ENCODING).strip()

        if not sql_text:
            raise CommandError(f"SQL file is empty: {sql_file_path}")

        return sql_text

    @classmethod
    def run_create_script(cls, *, database_alias: str, sql_group: str, explicit_sql_file: str = "") -> tuple[str, Path]:
        connection = cls.get_connection(database_alias)
        vendor = cls.detect_vendor(connection)

        sql_file_path = cls.get_sql_file_path(sql_group=sql_group, database_vendor=vendor, explicit_sql_file=explicit_sql_file)
        sql_text = cls.read_sql(sql_file_path)

        cls.execute_sql_script(connection=connection, sql_text=sql_text)

        return vendor, sql_file_path

    @classmethod
    def execute_sql_script(cls, *, connection: "BaseDatabaseWrapper", sql_text: str) -> None:
        connection.ensure_connection()

        if detect_db_vendor_from_connection(connection) == DB_VENDOR_SQLITE:
            cls.execute_sqlite_script(connection=connection, sql_text=sql_text)
            return

        cls.execute_prepared_script(connection=connection, sql_text=sql_text)

    @staticmethod
    def execute_sqlite_script(*, connection: "BaseDatabaseWrapper", sql_text: str) -> None:
        raw_connection = connection.connection

        if raw_connection is None:
            raise CommandError(f"Database connection is not available: {connection.alias}")

        try:
            raw_connection.executescript(sql_text)
            raw_connection.commit()
        except Exception as exc:
            raise CommandError(f"Failed to execute SQL script on database alias '{connection.alias}': {exc}") from exc

    @staticmethod
    def execute_prepared_script(*, connection: "BaseDatabaseWrapper", sql_text: str) -> None:
        statements = connection.ops.prepare_sql_script(sql_text)

        if not statements:
            raise CommandError("SQL script contains no executable statements.")

        try:
            with connection.cursor() as cursor:
                for statement in statements:
                    normalized_statement = str(statement).strip()
                    if not normalized_statement:
                        continue

                    cursor.execute(normalized_statement)
        except Exception as exc:
            raise CommandError(f"Failed to execute SQL script on database alias '{connection.alias}' with vendor '{connection.vendor}': {exc}") from exc
