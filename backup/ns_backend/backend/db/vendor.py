# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

DB_VENDOR_SQLITE = "sqlite"
DB_VENDOR_MYSQL = "mysql"
DB_VENDOR_POSTGRESQL = "postgresql"
DB_VENDOR_DM8 = "dm8"
DB_VENDOR_UNKNOWN = "unknown"

SUPPORTED_INFRA_DB_VENDORS = (
    DB_VENDOR_SQLITE,
    DB_VENDOR_MYSQL,
    DB_VENDOR_POSTGRESQL,
    DB_VENDOR_DM8
)


def normalize_db_vendor(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError(f"unsupported db vendor: {value}")

    text = value.strip().lower()
    if not text:
        raise ValueError(f"unsupported db vendor: {value}")

    if text in {
        "sqlite",
        "sqlite3"
    }:
        return DB_VENDOR_SQLITE
    if text in {
        "mysql",
        "mariadb"
    }:
        return DB_VENDOR_MYSQL
    if text in {
        "postgres",
        "postgresql",
        "pgsql"
    }:
        return DB_VENDOR_POSTGRESQL
    if text in {
        "dm",
        "dm8",
        "dameng"
    }:
        return DB_VENDOR_DM8

    raise ValueError(f"unsupported db vendor: {value}")


def detect_db_vendor(db_config: dict[str, Any]) -> str:
    if not isinstance(db_config, dict):
        return DB_VENDOR_UNKNOWN

    for key in (
            "NS_VENDOR",
            "VENDOR",
            "vendor"
    ):
        value = db_config.get(key)
        if isinstance(value, str) and value.strip():
            try:
                return normalize_db_vendor(value)
            except ValueError:
                return DB_VENDOR_UNKNOWN

    engine = str(db_config.get("ENGINE", "") or "").strip().lower()
    if not engine:
        return DB_VENDOR_UNKNOWN

    if engine == "django.db.backends.sqlite3" or "sqlite" in engine:
        return DB_VENDOR_SQLITE

    if engine in {
        "django.db.backends.mysql",
        "mysql.connector.django"
    }:
        return DB_VENDOR_MYSQL
    if "mysql" in engine or "mariadb" in engine:
        return DB_VENDOR_MYSQL

    if engine in {
        "django.db.backends.postgresql",
        "django.db.backends.postgresql_psycopg2"
    }:
        return DB_VENDOR_POSTGRESQL
    if "postgres" in engine or "psycopg" in engine or "pgsql" in engine:
        return DB_VENDOR_POSTGRESQL

    if "django_dm" in engine or "dameng" in engine or "dm8" in engine or "dm" in engine:
        return DB_VENDOR_DM8

    return DB_VENDOR_UNKNOWN
