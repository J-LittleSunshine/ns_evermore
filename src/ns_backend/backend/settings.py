from pathlib import Path
from typing import Any, Mapping

from backend.app_loader import build_installed_apps
from ns_common import ns_config
from ns_common.cache import validate_cache_backend
from ns_common.exceptions import NsConfigError
from ns_common.paths import (
    DATA_DIR,
    ensure_runtime_dirs
)

ensure_runtime_dirs()

BASE_DIR = Path(__file__).resolve().parent.parent


def _is_sqlite_engine(engine: Any) -> bool:
    return str(engine or "").strip().lower() == "django.db.backends.sqlite3"


def _normalize_sqlite_name(*, alias: str, name: Any) -> Path:
    raw_name = str(name or "").strip()

    if not raw_name:
        details = {
            "field": f"backend.databases.{alias}.NAME",
            "alias": alias,
        }
        raise NsConfigError("SQLite database NAME must be configured as a filename.", details=details)

    if raw_name in {
        ".",
        "..",
    }:
        details = {
            "field": f"backend.databases.{alias}.NAME",
            "alias": alias,
            "value": raw_name,
        }
        raise NsConfigError("SQLite database NAME must be a filename, not a relative directory reference.", details=details)

    if "/" in raw_name or "\\" in raw_name:
        details = {
            "field": f"backend.databases.{alias}.NAME",
            "alias": alias,
            "value": raw_name,
            "expected": "filename only, for example: iam.sqlite3",
        }
        raise NsConfigError("SQLite database NAME must be a filename only. Do not include directory paths.", details=details)

    candidate = Path(raw_name)
    if candidate.is_absolute() or candidate.name != raw_name:
        details = {
            "field": f"backend.databases.{alias}.NAME",
            "alias": alias,
            "value": raw_name,
            "expected": "filename only, for example: iam.sqlite3",
        }
        raise NsConfigError("SQLite database NAME must be a filename only. Absolute or relative paths are not allowed.", details=details)

    return DATA_DIR / raw_name


def _build_django_databases(raw_databases: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    if not raw_databases:
        return {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": DATA_DIR / "ns_db.sqlite3",
            }
        }

    databases: dict[str, dict[str, Any]] = {}

    for alias, raw_database_config in raw_databases.items():
        alias_text = str(alias or "").strip()
        if not alias_text:
            details = {
                "field": "backend.databases",
                "alias": alias,
            }
            raise NsConfigError("Database alias must not be empty.", details=details)

        if not isinstance(raw_database_config, Mapping):
            details = {
                "field": f"backend.databases.{alias_text}",
                "actual_type": type(raw_database_config).__name__,
            }
            raise NsConfigError("Database config must be a JSON object.", details=details)

        database_config = dict(raw_database_config)
        engine = database_config.get("ENGINE")

        if _is_sqlite_engine(engine):
            database_config["NAME"] = _normalize_sqlite_name(alias=alias_text, name=database_config.get("NAME"))

        databases[alias_text] = database_config

    return databases


SECRET_KEY = ns_config.backend.secret_key

DEBUG = ns_config.backend.debug

ALLOWED_HOSTS = ns_config.backend.allowed_hosts

INSTALLED_APPS = build_installed_apps(ns_config.backend.installed_apps)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'backend.urls'

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.AllowAny",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "UNAUTHENTICATED_USER": None,
    "UNAUTHENTICATED_TOKEN": None,
}

WSGI_APPLICATION = 'backend.wsgi.application'

ASGI_APPLICATION = 'backend.asgi.application'

DATABASES = _build_django_databases(ns_config.backend.databases)

DATABASE_ROUTER_MAP = ns_config.backend.database_router_map

DATABASE_ROUTERS = [
    "backend.db.routers.AppDatabaseRouter",
]

CACHES = {
    "default": {
        "BACKEND": "ns_common.cache.django.NsDjangoCacheBackend",
        "LOCATION": "default",
        "TIMEOUT": ns_config.cache.default_ttl_seconds,
        "OPTIONS": {},
    }
}

validate_cache_backend()

LANGUAGE_CODE = ns_config.backend.language_code

TIME_ZONE = ns_config.backend.time_zone

USE_I18N = ns_config.backend.use_i18n

USE_TZ = ns_config.backend.use_tz

STATIC_URL = ns_config.backend.static_url

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

JWT_SECRET_KEY = ns_config.backend.jwt_secret_key or SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = ns_config.backend.access_token_expire_minutes
REFRESH_TOKEN_EXPIRE_DAYS = ns_config.backend.refresh_token_expire_days
JWT_ISSUER = ns_config.backend.jwt_issuer
JWT_LEEWAY_SECONDS = ns_config.backend.jwt_leeway_seconds
JWT_MIN_SECRET_LENGTH = ns_config.backend.jwt_min_secret_length

PASSWORD_TRANSPORT_MODE = ns_config.backend.password_transport_mode
PASSWORD_TRANSPORT_MAX_PAYLOAD_LENGTH = ns_config.backend.password_transport_max_payload_length
PASSWORD_PLAINTEXT_MAX_LENGTH = ns_config.backend.password_plaintext_max_length
PASSWORD_RSA_PRIVATE_KEY = ns_config.backend.password_rsa_private_key
PASSWORD_RSA_PRIVATE_KEY_FILE = ns_config.backend.password_rsa_private_key_file
PASSWORD_RSA_PRIVATE_KEY_PASSPHRASE = ns_config.backend.password_rsa_private_key_passphrase

IAM_INTERNAL_TOKEN = ns_config.backend.iam_internal_token
IAM_RUNTIME_CONFIG_VERSION = ns_config.config_version
IAM_RUNTIME_POLICY_VERSION = ns_config.policy_version
IAM_RUNTIME_NODE_CREDENTIAL_TTL_SECONDS = 900

IAM_DECISION_AUDIT_ENABLED = ns_config.backend.iam_decision_audit_enabled
IAM_DECISION_AUDIT_STRICT_MODE = ns_config.backend.iam_decision_audit_strict_mode
IAM_OPERATION_AUDIT_ENABLED = ns_config.backend.iam_operation_audit_enabled
IAM_OPERATION_AUDIT_STRICT_MODE = ns_config.backend.iam_operation_audit_strict_mode

IAM_AUTH_BACKOFF_ENABLED = ns_config.backend.iam_auth_backoff_enabled
IAM_AUTH_BACKOFF_MAX_RETRIES = ns_config.backend.iam_auth_backoff_max_retries
IAM_AUTH_BACKOFF_BASE_DELAY_MS = ns_config.backend.iam_auth_backoff_base_delay_ms
IAM_AUTH_BACKOFF_MAX_DELAY_MS = ns_config.backend.iam_auth_backoff_max_delay_ms
IAM_AUTH_BACKOFF_JITTER_RATIO = ns_config.backend.iam_auth_backoff_jitter_ratio

IAM_CACHE_ENABLED = ns_config.backend.iam_cache_enabled
IAM_CACHE_TTL_SECONDS = ns_config.backend.iam_cache_ttl_seconds
IAM_USER_CACHE_TTL_SECONDS = ns_config.backend.iam_user_cache_ttl_seconds
IAM_AUTHZ_CACHE_TTL_SECONDS = ns_config.backend.iam_authz_cache_ttl_seconds
