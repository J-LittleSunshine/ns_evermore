# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from django.conf import settings
from django.db import connections, transaction

from ns_backend.db_sql import ensure_sql_file_exists, validate_infra_domain

_CREATE_TABLE_NAME_PATTERN = re.compile(
    r"^\s*create\s+table\s+(?:if\s+not\s+exists\s+)?(?P<name>`[^`]+`|\"[^\"]+\"|\[[^\]]+\]|[a-zA-Z_][\w$.]*)",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class InfraSchemaInstallPlan:
    infra_domain: str
    db_alias: str
    vendor: str
    sql_path: Path
    sql_statement_count: int
    expected_tables: tuple[str, ...]
    existing_tables: tuple[str, ...]


@dataclass(frozen=True)
class InfraSchemaInstallResult:
    infra_domain: str
    db_alias: str
    vendor: str
    sql_path: Path
    dry_run: bool
    skipped: bool
    executed_statement_count: int
    expected_tables: tuple[str, ...]
    existing_tables: tuple[str, ...]


def _normalize_infra_domain(value: object) -> str:
    return validate_infra_domain(value)


def _split_sql_statements(sql_text: str) -> list[str]:
    statements: list[str] = []
    buffer: list[str] = []
    index = 0
    length = len(sql_text)
    in_single_quote = False
    in_double_quote = False
    in_line_comment = False
    in_block_comment = False

    while index < length:
        current = sql_text[index]
        next_char = sql_text[index + 1] if index + 1 < length else ""

        if in_line_comment:
            if current == "\n":
                in_line_comment = False
            index += 1
            continue

        if in_block_comment:
            if current == "*" and next_char == "/":
                in_block_comment = False
                index += 2
                continue
            index += 1
            continue

        if not in_single_quote and not in_double_quote:
            if current == "-" and next_char == "-":
                in_line_comment = True
                index += 2
                continue

            if current == "#":
                in_line_comment = True
                index += 1
                continue

            if current == "/" and next_char == "*":
                in_block_comment = True
                index += 2
                continue

        if current == "'" and not in_double_quote:
            if in_single_quote and next_char == "'":
                buffer.append(current)
                buffer.append(next_char)
                index += 2
                continue
            in_single_quote = not in_single_quote
            buffer.append(current)
            index += 1
            continue

        if current == '"' and not in_single_quote:
            if in_double_quote and next_char == '"':
                buffer.append(current)
                buffer.append(next_char)
                index += 2
                continue
            in_double_quote = not in_double_quote
            buffer.append(current)
            index += 1
            continue

        if current == ";" and not in_single_quote and not in_double_quote:
            statement = "".join(buffer).strip()
            if statement:
                statements.append(statement)
            buffer = []
            index += 1
            continue

        buffer.append(current)
        index += 1

    trailing_statement = "".join(buffer).strip()
    if trailing_statement:
        statements.append(trailing_statement)

    return statements


def _strip_table_name_wrapper(table_name: str) -> str:
    text = table_name.strip()
    if not text:
        return text

    if text[0] in {'`', '"', '['} and text[-1] in {'`', '"', ']'}:
        text = text[1:-1]

    if "." in text:
        text = text.split(".")[-1]
        text = text.strip('`"[]')

    return text.strip()


def _extract_create_table_names(sql_text: str) -> tuple[str, ...]:
    table_names: list[str] = []
    seen: set[str] = set()

    for statement in _split_sql_statements(sql_text):
        match = _CREATE_TABLE_NAME_PATTERN.match(statement)
        if match is None:
            continue

        table_name = _strip_table_name_wrapper(match.group("name"))
        if not table_name:
            continue

        normalized = table_name.lower()
        if normalized in seen:
            continue

        seen.add(normalized)
        table_names.append(table_name)

    return tuple(table_names)


def _get_existing_tables(db_alias: str) -> tuple[str, ...]:
    connection = connections[db_alias]
    with connection.cursor() as cursor:
        table_names = connection.introspection.table_names(cursor)

    unique_table_names = sorted({str(name) for name in table_names if str(name).strip()})
    return tuple(unique_table_names)


def get_infra_schema_install_plan(infra_domain: str) -> InfraSchemaInstallPlan:
    domain_name = _normalize_infra_domain(infra_domain)

    if domain_name not in settings.INFRA_DB_ROUTER_MAP:
        raise ValueError(f"infra domain is not configured in infra_db_router_map: {domain_name}")
    if domain_name not in settings.INFRA_DB_VENDOR_MAP:
        raise ValueError(f"infra domain is not configured in infra_db_vendor_map: {domain_name}")
    if domain_name not in settings.INFRA_CREATE_SQL_PATH_MAP:
        raise ValueError(f"infra domain is not configured in infra_create_sql_path_map: {domain_name}")

    db_alias = settings.INFRA_DB_ROUTER_MAP[domain_name]
    vendor = settings.INFRA_DB_VENDOR_MAP[domain_name]
    sql_path = ensure_sql_file_exists(settings.INFRA_CREATE_SQL_PATH_MAP[domain_name])

    sql_text = sql_path.read_text(encoding="utf-8")
    expected_tables = _extract_create_table_names(sql_text)
    if not expected_tables:
        raise RuntimeError(f"no CREATE TABLE statements found in sql file: {sql_path}")

    statements = _split_sql_statements(sql_text)
    existing_tables = _get_existing_tables(db_alias)

    return InfraSchemaInstallPlan(
        infra_domain=domain_name,
        db_alias=db_alias,
        vendor=vendor,
        sql_path=sql_path,
        sql_statement_count=len(statements),
        expected_tables=expected_tables,
        existing_tables=existing_tables,
    )


def install_infra_schema(infra_domain: str, *, dry_run: bool = False) -> InfraSchemaInstallResult:
    plan = get_infra_schema_install_plan(infra_domain)

    expected_index = {name.lower(): name for name in plan.expected_tables}
    existing_index = {name.lower(): name for name in plan.existing_tables}

    existing_expected = tuple(
        expected_index[name]
        for name in expected_index
        if name in existing_index
    )

    if len(existing_expected) == len(plan.expected_tables):
        return InfraSchemaInstallResult(
            infra_domain=plan.infra_domain,
            db_alias=plan.db_alias,
            vendor=plan.vendor,
            sql_path=plan.sql_path,
            dry_run=dry_run,
            skipped=True,
            executed_statement_count=0,
            expected_tables=plan.expected_tables,
            existing_tables=plan.existing_tables,
        )

    if existing_expected:
        # 关键保护：检测到部分表存在时立即失败，避免半初始化状态继续执行。
        raise RuntimeError(
            "infra schema is partially initialized, please verify database state manually before retry: "
            f"domain={plan.infra_domain}, existing_expected_tables={existing_expected}"
        )

    if dry_run:
        return InfraSchemaInstallResult(
            infra_domain=plan.infra_domain,
            db_alias=plan.db_alias,
            vendor=plan.vendor,
            sql_path=plan.sql_path,
            dry_run=True,
            skipped=False,
            executed_statement_count=0,
            expected_tables=plan.expected_tables,
            existing_tables=plan.existing_tables,
        )

    sql_text = plan.sql_path.read_text(encoding="utf-8")
    statements = _split_sql_statements(sql_text)
    executed_statement_count = 0

    # 关键执行路径：逐条执行拆分后的 SQL，避免依赖驱动 multi statements 能力。
    with transaction.atomic(using=plan.db_alias):
        connection = connections[plan.db_alias]
        with connection.cursor() as cursor:
            for statement in statements:
                cursor.execute(statement)
                executed_statement_count += 1

    return InfraSchemaInstallResult(
        infra_domain=plan.infra_domain,
        db_alias=plan.db_alias,
        vendor=plan.vendor,
        sql_path=plan.sql_path,
        dry_run=False,
        skipped=False,
        executed_statement_count=executed_statement_count,
        expected_tables=plan.expected_tables,
        existing_tables=plan.existing_tables,
    )


__all__ = [
    "InfraSchemaInstallPlan",
    "InfraSchemaInstallResult",
    "get_infra_schema_install_plan",
    "install_infra_schema",
]


