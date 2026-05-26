# -*- coding: utf-8 -*-
from __future__ import annotations

import re
from pathlib import Path

from ns_backend.db_vendor import DB_VENDOR_UNKNOWN, SUPPORTED_INFRA_DB_VENDORS

SQL_OPERATION_CREATE = "create"
SUPPORTED_INFRA_SQL_OPERATIONS = (
    SQL_OPERATION_CREATE,
)

_INFRA_DOMAIN_PATTERN = re.compile(r"^[a-z0-9_]+$")


def validate_infra_domain(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("infra_domain must be non-empty str")

    text = value.strip()
    if not text:
        raise ValueError("infra_domain must be non-empty str")

    if not _INFRA_DOMAIN_PATTERN.fullmatch(text):
        raise ValueError(f"invalid infra_domain: {value}")

    return text


def validate_sql_operation(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("sql operation is invalid")

    text = value.strip()
    if text not in SUPPORTED_INFRA_SQL_OPERATIONS:
        raise ValueError(f"unsupported sql operation: {value}")

    return text


def validate_infra_db_vendor(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("infra db vendor is invalid")

    text = value.strip()
    if text == DB_VENDOR_UNKNOWN:
        raise ValueError(f"unsupported infra db vendor: {value}")

    if text not in SUPPORTED_INFRA_DB_VENDORS:
        raise ValueError(f"unsupported infra db vendor: {value}")

    return text


def build_infra_sql_path(
    *,
    sql_root: str | Path,
    operation: str,
    infra_domain: str,
    vendor: str,
) -> Path:
    operation_name = validate_sql_operation(operation)
    domain_name = validate_infra_domain(infra_domain)
    vendor_name = validate_infra_db_vendor(vendor)
    return Path(sql_root) / operation_name / domain_name / f"{vendor_name}.sql"


def build_infra_create_sql_path(
    *,
    sql_root: str | Path,
    infra_domain: str,
    vendor: str,
) -> Path:
    return build_infra_sql_path(
        sql_root=sql_root,
        operation=SQL_OPERATION_CREATE,
        infra_domain=infra_domain,
        vendor=vendor,
    )


def ensure_sql_file_exists(path: str | Path) -> Path:
    file_path = Path(path)
    if not file_path.is_file():
        raise FileNotFoundError(f"sql file does not exist: {file_path}")
    return file_path


__all__ = [
    "SQL_OPERATION_CREATE",
    "SUPPORTED_INFRA_SQL_OPERATIONS",
    "validate_infra_domain",
    "validate_sql_operation",
    "validate_infra_db_vendor",
    "build_infra_sql_path",
    "build_infra_create_sql_path",
    "ensure_sql_file_exists",
]

