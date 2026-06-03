# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from ns_backend.backend.db.alias import DEFAULT_DB_ALIAS, IAM_DB_ALIAS_NAME
from ns_backend.backend.db.sql import build_infra_create_sql_path
from ns_backend.backend.db.vendor import detect_db_vendor, DB_VENDOR_UNKNOWN
from ns_common import DATA_DIR, SQL_DIR
from ns_common.config import ns_config

BASE_DIR = Path(__file__).resolve().parent.parent.parent
_BACKEND = ns_config.backend_config


def _coerce_positive_int(value: Any, default: int) -> int:
    """Resolve integer config from JSON/env while rejecting bool and non-positive values."""
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value if value > 0 else default
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return default
        try:
            parsed = int(text)
        except (TypeError, ValueError):
            return default
        return parsed if parsed > 0 else default
    return default


def _coerce_non_negative_int(value: Any, default: int) -> int:
    """Resolve integer config while allowing zero as a valid non-negative value."""
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value if value >= 0 else default
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return default
        try:
            parsed = int(text)
        except (TypeError, ValueError):
            return default
        return parsed if parsed >= 0 else default
    return default


def _coerce_bool(value: Any, default: bool) -> bool:
    """Resolve bool config from JSON/env values."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y", "on"}:
            return True
        if text in {"0", "false", "no", "n", "off"}:
            return False
    return default


def _coerce_float_in_range(value: Any, default: float, *, min_value: float, max_value: float) -> float:
    """Resolve float config from JSON/env and clamp to one inclusive range."""
    if isinstance(value, bool):
        return default

    parsed_value: float
    if isinstance(value, (int, float)):
        parsed_value = float(value)
    elif isinstance(value, str):
        text = value.strip()
        if not text:
            return default
        try:
            parsed_value = float(text)
        except (TypeError, ValueError):
            return default
    else:
        return default

    if parsed_value < min_value:
        return min_value
    if parsed_value > max_value:
        return max_value
    return parsed_value


def _coerce_string_tuple(value: Any) -> tuple[str, ...]:
    """Resolve list-like string config for audit sensitive keys."""
    if value is None:
        return ()

    if isinstance(value, (list, tuple, set)):
        result: list[str] = []
        seen: set[str] = set()
        for item in value:
            if not isinstance(item, str):
                continue
            text = item.strip()
            if not text or text in seen:
                continue
            seen.add(text)
            result.append(text)
        return tuple(result)

    if isinstance(value, str):
        text = value.strip()
        if not text:
            return ()

        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parts = [part.strip() for part in text.split(",")]
            result: list[str] = []
            seen: set[str] = set()
            for part in parts:
                if not part or part in seen:
                    continue
                seen.add(part)
                result.append(part)
            return tuple(result)

        if isinstance(parsed, str):
            return _coerce_string_tuple((parsed,))
        if isinstance(parsed, (list, tuple, set)):
            return _coerce_string_tuple(parsed)
        return ()

    return ()


def _merge_string_tuples(*values: Any) -> tuple[str, ...]:
    """Merge JSON/env string-list values while preserving order."""
    merged: list[str] = []
    seen: set[str] = set()
    for value in values:
        for item in _coerce_string_tuple(value):
            if item in seen:
                continue
            seen.add(item)
            merged.append(item)
    return tuple(merged)


SECRET_KEY = os.getenv("NS_SECRET_KEY") or _BACKEND.secret_key
JWT_SECRET_KEY = os.getenv("NS_JWT_SECRET_KEY") or _BACKEND.jwt_secret_key

ACCESS_TOKEN_EXPIRE_MINUTES = _coerce_positive_int(os.getenv("NS_ACCESS_TOKEN_EXPIRE_MINUTES") or _BACKEND.access_token_expire_minutes, 30)
REFRESH_TOKEN_EXPIRE_DAYS = _coerce_positive_int(os.getenv("NS_REFRESH_TOKEN_EXPIRE_DAYS") or _BACKEND.refresh_token_expire_days, 14)
JWT_ISSUER = os.getenv("NS_JWT_ISSUER") or _BACKEND.jwt_issuer
JWT_LEEWAY_SECONDS = _coerce_positive_int(os.getenv("NS_JWT_LEEWAY_SECONDS") or _BACKEND.jwt_leeway_seconds, 30)
JWT_MIN_SECRET_LENGTH = _coerce_positive_int(os.getenv("NS_JWT_MIN_SECRET_LENGTH") or _BACKEND.jwt_min_secret_length, 32)

PASSWORD_TRANSPORT_ALLOWED_MODES = ("plain", "rsa_oaep")
PASSWORD_TRANSPORT_MODE = (os.getenv("NS_PASSWORD_TRANSPORT_MODE") or _BACKEND.password_transport_mode or "plain").strip().lower()
if PASSWORD_TRANSPORT_MODE not in PASSWORD_TRANSPORT_ALLOWED_MODES:
    raise RuntimeError(f"password_transport_mode must be one of: {', '.join(PASSWORD_TRANSPORT_ALLOWED_MODES)}")

PASSWORD_TRANSPORT_MAX_PAYLOAD_LENGTH = _coerce_positive_int(os.getenv("NS_PASSWORD_TRANSPORT_MAX_PAYLOAD_LENGTH") or _BACKEND.password_transport_max_payload_length, 4096)
PASSWORD_PLAINTEXT_MAX_LENGTH = _coerce_positive_int(os.getenv("NS_PASSWORD_PLAINTEXT_MAX_LENGTH") or _BACKEND.password_plaintext_max_length, 256)
PASSWORD_RSA_PRIVATE_KEY = os.getenv("NS_PASSWORD_RSA_PRIVATE_KEY") or _BACKEND.password_rsa_private_key or ""
PASSWORD_RSA_PRIVATE_KEY_FILE = os.getenv("NS_PASSWORD_RSA_PRIVATE_KEY_FILE") or _BACKEND.password_rsa_private_key_file or ""
PASSWORD_RSA_PRIVATE_KEY_PASSPHRASE = os.getenv("NS_PASSWORD_RSA_PRIVATE_KEY_PASSPHRASE") or _BACKEND.password_rsa_private_key_passphrase or ""

if PASSWORD_TRANSPORT_MODE == "rsa_oaep" and not (PASSWORD_RSA_PRIVATE_KEY or PASSWORD_RSA_PRIVATE_KEY_FILE):
    raise RuntimeError("password_rsa_private_key or password_rsa_private_key_file is required when password_transport_mode is rsa_oaep")

LOGIN_MAX_FAILED_COUNT = _coerce_positive_int(os.getenv("NS_LOGIN_MAX_FAILED_COUNT") or _BACKEND.login_max_failed_count, 5)
LOGIN_LOCK_MINUTES = _coerce_positive_int(os.getenv("NS_LOGIN_LOCK_MINUTES") or _BACKEND.login_lock_minutes, 15)

IAM_AUDIT_EXTRA_SENSITIVE_KEYS = _merge_string_tuples(
    _BACKEND.extra_sensitive_keys,
    os.getenv("NS_EXTRA_SENSITIVE_KEYS"),
    _BACKEND.audit_extra_sensitive_keys,
    os.getenv("IAM_AUDIT_EXTRA_SENSITIVE_KEYS"),
)

IAM_DECISION_AUDIT_STRICT_MODE = _coerce_bool(
    os.getenv("NS_IAM_DECISION_AUDIT_STRICT_MODE") or os.getenv("IAM_DECISION_AUDIT_STRICT_MODE"),
    _coerce_bool(getattr(_BACKEND, "iam_decision_audit_strict_mode", False), False),
)

IAM_PERMISSION_PROVIDERS = _merge_string_tuples(
    _BACKEND.iam_permission_providers,
    os.getenv("NS_IAM_PERMISSION_PROVIDERS"),
    os.getenv("IAM_PERMISSION_PROVIDERS"),
)

IAM_MODULE_REGISTRATION_HOOKS = _merge_string_tuples(
    getattr(_BACKEND, "iam_module_registration_hooks", ()),
    os.getenv("NS_IAM_MODULE_REGISTRATION_HOOKS"),
    os.getenv("IAM_MODULE_REGISTRATION_HOOKS"),
)

IAM_AUTH_CONTEXT_TTL_SECONDS = _coerce_positive_int(
    os.getenv("NS_IAM_AUTH_CONTEXT_TTL_SECONDS") or os.getenv("IAM_AUTH_CONTEXT_TTL_SECONDS") or getattr(_BACKEND, "iam_auth_context_ttl_seconds", 300),
    300,
)

IAM_AUTH_BACKOFF_ENABLED = _coerce_bool(
    os.getenv("NS_IAM_AUTH_BACKOFF_ENABLED") or os.getenv("IAM_AUTH_BACKOFF_ENABLED"),
    _coerce_bool(getattr(_BACKEND, "iam_auth_backoff_enabled", True), True),
)

IAM_AUTH_BACKOFF_MAX_RETRIES = _coerce_non_negative_int(
    os.getenv("NS_IAM_AUTH_BACKOFF_MAX_RETRIES") or os.getenv("IAM_AUTH_BACKOFF_MAX_RETRIES") or getattr(_BACKEND, "iam_auth_backoff_max_retries", 3),
    3,
)

IAM_AUTH_BACKOFF_BASE_DELAY_MS = _coerce_non_negative_int(
    os.getenv("NS_IAM_AUTH_BACKOFF_BASE_DELAY_MS") or os.getenv("IAM_AUTH_BACKOFF_BASE_DELAY_MS") or getattr(_BACKEND, "iam_auth_backoff_base_delay_ms", 50),
    50,
)

IAM_AUTH_BACKOFF_MAX_DELAY_MS = _coerce_non_negative_int(
    os.getenv("NS_IAM_AUTH_BACKOFF_MAX_DELAY_MS") or os.getenv("IAM_AUTH_BACKOFF_MAX_DELAY_MS") or getattr(_BACKEND, "iam_auth_backoff_max_delay_ms", 1000),
    1000,
)

IAM_AUTH_BACKOFF_JITTER_RATIO = _coerce_float_in_range(
    os.getenv("NS_IAM_AUTH_BACKOFF_JITTER_RATIO") or os.getenv("IAM_AUTH_BACKOFF_JITTER_RATIO") or getattr(_BACKEND, "iam_auth_backoff_jitter_ratio", 0.5),
    0.5,
    min_value=0.0,
    max_value=1.0,
)

IAM_AUTH_LOCAL_FALLBACK_CACHE_ENABLED = _coerce_bool(
    os.getenv("NS_IAM_AUTH_LOCAL_FALLBACK_CACHE_ENABLED") or os.getenv("IAM_AUTH_LOCAL_FALLBACK_CACHE_ENABLED"),
    _coerce_bool(getattr(_BACKEND, "iam_auth_local_fallback_cache_enabled", True), True),
)

IAM_AUTH_LOCAL_FALLBACK_CACHE_TTL_SECONDS = _coerce_positive_int(
    os.getenv("NS_IAM_AUTH_LOCAL_FALLBACK_CACHE_TTL_SECONDS") or os.getenv("IAM_AUTH_LOCAL_FALLBACK_CACHE_TTL_SECONDS") or getattr(_BACKEND, "iam_auth_local_fallback_cache_ttl_seconds", 3),
    3,
)

IAM_AUTH_LOCAL_FALLBACK_CACHE_MAX_SIZE = _coerce_positive_int(
    os.getenv("NS_IAM_AUTH_LOCAL_FALLBACK_CACHE_MAX_SIZE") or os.getenv("IAM_AUTH_LOCAL_FALLBACK_CACHE_MAX_SIZE") or getattr(_BACKEND, "iam_auth_local_fallback_cache_max_size", 1024),
    1024,
)

IAM_AUTH_SINGLE_FLIGHT_ENABLED = _coerce_bool(
    os.getenv("NS_IAM_AUTH_SINGLE_FLIGHT_ENABLED") or os.getenv("IAM_AUTH_SINGLE_FLIGHT_ENABLED"),
    _coerce_bool(getattr(_BACKEND, "iam_auth_single_flight_enabled", True), True),
)

def _resolve_cache_backend(value: Any, url: str) -> str:
    """Resolve redis-compatible cache backend type."""
    backend = str(value or "").strip().lower()
    if not backend:
        return "valkey" if url.strip().lower().startswith("valkey://") else "redis"

    if backend not in {"redis", "valkey"}:
        raise RuntimeError("cache_backend must be one of: redis, valkey")

    return backend


def _resolve_cache_serializer(value: Any, default: str = "pickle") -> str:
    """Resolve ns_common cache serializer name."""
    serializer = str(value or default).strip().lower()
    if serializer not in {"pickle", "json", "raw"}:
        raise RuntimeError("cache_serializer must be one of: pickle, json, raw")

    return serializer


def _build_ns_common_cache_config(
    *,
    url: str,
    key_prefix: str,
    timeout_seconds: int,
    backend: str,
    serializer: str,
    socket_timeout: float,
    socket_connect_timeout: float,
    max_connections: int,
    health_check_interval: int,
) -> dict[str, Any]:
    """Build Django CACHES entry for NsCommonCacheBackend."""
    return {
        "BACKEND": "ns_backend.backend.cache.django_backend.NsCommonCacheBackend",
        "LOCATION": url,
        "TIMEOUT": timeout_seconds,
        "KEY_PREFIX": key_prefix,
        "OPTIONS": {
            "backend": backend,
            "ns_key_prefix": key_prefix,
            "serializer": serializer,
            "socket_timeout": socket_timeout,
            "socket_connect_timeout": socket_connect_timeout,
            "max_connections": max_connections,
            "health_check_interval": health_check_interval,
        },
    }


_COMMON_CACHE_URL = str(
    os.getenv("NS_CACHE_URL")
    or os.getenv("CACHE_URL")
    or getattr(_BACKEND, "cache_url", "")
    or ""
).strip()

_COMMON_CACHE_BACKEND = _resolve_cache_backend(
    os.getenv("NS_CACHE_BACKEND")
    or os.getenv("CACHE_BACKEND")
    or getattr(_BACKEND, "cache_backend", ""),
    _COMMON_CACHE_URL,
)

_COMMON_CACHE_KEY_PREFIX = str(
    os.getenv("NS_CACHE_KEY_PREFIX")
    or os.getenv("CACHE_KEY_PREFIX")
    or getattr(_BACKEND, "cache_key_prefix", "ns")
    or "ns"
).strip().strip(":") or "ns"

_COMMON_CACHE_TIMEOUT_SECONDS = _coerce_positive_int(
    os.getenv("NS_CACHE_TIMEOUT_SECONDS")
    or os.getenv("CACHE_TIMEOUT_SECONDS")
    or getattr(_BACKEND, "cache_timeout_seconds", 300),
    300,
)

_COMMON_CACHE_SERIALIZER = _resolve_cache_serializer(
    os.getenv("NS_CACHE_SERIALIZER")
    or os.getenv("CACHE_SERIALIZER")
    or getattr(_BACKEND, "cache_serializer", "pickle"),
    "pickle",
)

_COMMON_CACHE_SOCKET_TIMEOUT = _coerce_float_in_range(
    os.getenv("NS_CACHE_SOCKET_TIMEOUT") or getattr(_BACKEND, "cache_socket_timeout", 3.0),
    3.0,
    min_value=0.001,
    max_value=60.0,
)

_COMMON_CACHE_SOCKET_CONNECT_TIMEOUT = _coerce_float_in_range(
    os.getenv("NS_CACHE_SOCKET_CONNECT_TIMEOUT") or getattr(_BACKEND, "cache_socket_connect_timeout", 3.0),
    3.0,
    min_value=0.001,
    max_value=60.0,
)

_COMMON_CACHE_MAX_CONNECTIONS = _coerce_positive_int(
    os.getenv("NS_CACHE_MAX_CONNECTIONS") or getattr(_BACKEND, "cache_max_connections", 64),
    64,
)

_COMMON_CACHE_HEALTH_CHECK_INTERVAL = _coerce_positive_int(
    os.getenv("NS_CACHE_HEALTH_CHECK_INTERVAL") or getattr(_BACKEND, "cache_health_check_interval", 30),
    30,
)

_IAM_AUTH_CONTEXT_REDIS_URL = str(
    os.getenv("NS_IAM_AUTH_CONTEXT_REDIS_URL")
    or os.getenv("IAM_AUTH_CONTEXT_REDIS_URL")
    or getattr(_BACKEND, "iam_auth_context_redis_url", "")
    or ""
).strip()

_IAM_AUTH_CONTEXT_CACHE_ALIAS = str(
    os.getenv("NS_IAM_AUTH_CONTEXT_CACHE_ALIAS")
    or os.getenv("IAM_AUTH_CONTEXT_CACHE_ALIAS")
    or getattr(_BACKEND, "iam_auth_context_cache_alias", "")
    or ""
).strip()

CACHES: dict[str, dict[str, Any]] = {}

if _COMMON_CACHE_URL:
    CACHES["default"] = _build_ns_common_cache_config(
        url=_COMMON_CACHE_URL,
        key_prefix=_COMMON_CACHE_KEY_PREFIX,
        timeout_seconds=_COMMON_CACHE_TIMEOUT_SECONDS,
        backend=_COMMON_CACHE_BACKEND,
        serializer=_COMMON_CACHE_SERIALIZER,
        socket_timeout=_COMMON_CACHE_SOCKET_TIMEOUT,
        socket_connect_timeout=_COMMON_CACHE_SOCKET_CONNECT_TIMEOUT,
        max_connections=_COMMON_CACHE_MAX_CONNECTIONS,
        health_check_interval=_COMMON_CACHE_HEALTH_CHECK_INTERVAL,
    )
else:
    CACHES["default"] = {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "ns_evermore_default_cache",
        "TIMEOUT": IAM_AUTH_CONTEXT_TTL_SECONDS,
    }

if _IAM_AUTH_CONTEXT_REDIS_URL:
    CACHES["iam_auth"] = _build_ns_common_cache_config(
        url=_IAM_AUTH_CONTEXT_REDIS_URL,
        key_prefix=f"{_COMMON_CACHE_KEY_PREFIX}:iam_auth",
        timeout_seconds=IAM_AUTH_CONTEXT_TTL_SECONDS,
        backend=_resolve_cache_backend("", _IAM_AUTH_CONTEXT_REDIS_URL),
        serializer=_COMMON_CACHE_SERIALIZER,
        socket_timeout=_COMMON_CACHE_SOCKET_TIMEOUT,
        socket_connect_timeout=_COMMON_CACHE_SOCKET_CONNECT_TIMEOUT,
        max_connections=_COMMON_CACHE_MAX_CONNECTIONS,
        health_check_interval=_COMMON_CACHE_HEALTH_CHECK_INTERVAL,
    )

IAM_AUTH_CONTEXT_CACHE_ALIAS = _IAM_AUTH_CONTEXT_CACHE_ALIAS or ("iam_auth" if _IAM_AUTH_CONTEXT_REDIS_URL else "default")
if IAM_AUTH_CONTEXT_CACHE_ALIAS not in CACHES:
    IAM_AUTH_CONTEXT_CACHE_ALIAS = "default"

TRUST_X_FORWARDED_FOR = _coerce_bool(os.getenv("NS_TRUST_X_FORWARDED_FOR"), _BACKEND.trust_x_forwarded_for)

DEBUG = _BACKEND.debug
ALLOWED_HOSTS = list(_BACKEND.allowed_hosts)

INSTALLED_APPS = [
    "ns_backend.backend",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "adrf",
    "ns_backend.iam.apps.IamConfig"
]

for _app_name, _enabled in _BACKEND.loaded_apps.items():
    if not _enabled:
        continue
    if _app_name not in INSTALLED_APPS:
        INSTALLED_APPS.append(_app_name)

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware"
]

ROOT_URLCONF = "ns_backend.backend.urls"
ASGI_APPLICATION = "ns_backend.backend.asgi.application"
WSGI_APPLICATION = "ns_backend.backend.wsgi.application"

_DATABASES_CONFIG: dict[str, dict[str, Any]] = dict(_BACKEND.databases)
if not _DATABASES_CONFIG:
    _DATABASES_CONFIG = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(DATA_DIR / "ns_db.sqlite3")
        }
    }

DATABASES: dict[str, dict[str, Any]] = {}
for _db_alias, _db_config in _DATABASES_CONFIG.items():
    if not isinstance(_db_alias, str):
        raise TypeError("database alias must be str")
    if not isinstance(_db_config, dict):
        raise TypeError("database config must be dict")

    current_config = dict(_db_config)
    if current_config.get("ENGINE") == "django.db.backends.sqlite3":
        db_name = current_config.get("NAME")
        if db_name and not Path(str(db_name)).is_absolute():
            current_config["NAME"] = str(DATA_DIR / str(db_name))

    DATABASES[_db_alias] = current_config

DATABASE_VENDOR_MAP: dict[str, str] = {alias: detect_db_vendor(db_config) for alias, db_config in DATABASES.items()}

_unknown_vendor_aliases = [alias for alias, vendor in DATABASE_VENDOR_MAP.items() if vendor == DB_VENDOR_UNKNOWN]

if _unknown_vendor_aliases:
    raise RuntimeError("unsupported or unknown database vendor for aliases: " + ", ".join(_unknown_vendor_aliases) + ". Please set NS_VENDOR or ENGINE correctly.")

INFRA_DB_ROUTER_MAP = dict(_BACKEND.infra_db_router_map)
DATABASE_ROUTER_MAP = dict(_BACKEND.database_router_map)

if DEFAULT_DB_ALIAS not in DATABASES:
    raise RuntimeError("DATABASES must contain 'default' alias.")

if IAM_DB_ALIAS_NAME not in INFRA_DB_ROUTER_MAP:
    INFRA_DB_ROUTER_MAP[IAM_DB_ALIAS_NAME] = IAM_DB_ALIAS_NAME if IAM_DB_ALIAS_NAME in DATABASES else DEFAULT_DB_ALIAS

for _infra_domain, _db_alias in INFRA_DB_ROUTER_MAP.items():
    if not isinstance(_infra_domain, str) or not _infra_domain.strip():
        raise TypeError("infra db domain must be non-empty str")
    if not isinstance(_db_alias, str) or not _db_alias.strip():
        raise TypeError("infra db alias must be non-empty str")
    if _db_alias not in DATABASES:
        raise RuntimeError(f"infra_db_router_map.{_infra_domain} points to undefined database alias: {_db_alias}")

for _app_label, _db_alias in DATABASE_ROUTER_MAP.items():
    if not isinstance(_app_label, str) or not _app_label.strip():
        raise TypeError("database_router_map app label must be non-empty str")
    if not isinstance(_db_alias, str) or not _db_alias.strip():
        raise TypeError("database_router_map db alias must be non-empty str")
    if _db_alias not in DATABASES:
        raise RuntimeError(f"database_router_map.{_app_label} points to undefined database alias: {_db_alias}")

DATABASE_ROUTERS = [
    "ns_backend.backend.db.routers.AppDatabaseRouter"
]

INFRA_SQL_ROOT = SQL_DIR

INFRA_DB_VENDOR_MAP: dict[str, str] = {
    infra_domain: DATABASE_VENDOR_MAP.get(db_alias, DB_VENDOR_UNKNOWN)
    for infra_domain, db_alias in INFRA_DB_ROUTER_MAP.items()
}

_unknown_infra_domains = [infra_domain for infra_domain, vendor in INFRA_DB_VENDOR_MAP.items() if vendor == DB_VENDOR_UNKNOWN]
if _unknown_infra_domains:
    raise RuntimeError("unsupported infra db vendor for domains: " + ", ".join(_unknown_infra_domains))

INFRA_CREATE_SQL_PATH_MAP: dict[str, Path] = {
    infra_domain: build_infra_create_sql_path(sql_root=INFRA_SQL_ROOT, infra_domain=infra_domain, vendor=vendor)
    for infra_domain, vendor in INFRA_DB_VENDOR_MAP.items()
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = _BACKEND.language_code
TIME_ZONE = _BACKEND.time_zone
USE_I18N = _BACKEND.use_i18n
USE_TZ = _BACKEND.use_tz
STATIC_URL = _BACKEND.static_url
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
