from pathlib import Path
from typing import Any

from ns_common import DATA_DIR, SQL_DIR
from ns_common.config import ns_config
from .db.alias import DEFAULT_DB_ALIAS, IAM_DB_ALIAS_NAME
from .db.sql import build_infra_create_sql_path
from .db.vendor import detect_db_vendor, DB_VENDOR_UNKNOWN

BASE_DIR = Path(__file__).resolve().parent.parent.parent
_BACKEND = ns_config.backend_config

SECRET_KEY = _BACKEND.secret_key
DEBUG = _BACKEND.debug
ALLOWED_HOSTS = list(_BACKEND.allowed_hosts)

INSTALLED_APPS = [
    "backend",
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "adrf",
]

_APP_PATH_MAP = {
    "iam": "ns_backend.iam.apps.IamConfig",
}

for _app_name, _enabled in _BACKEND.loaded_apps.items():
    if not _enabled:
        continue
    _resolved_app = _APP_PATH_MAP.get(_app_name, _app_name)
    if _resolved_app not in INSTALLED_APPS:
        INSTALLED_APPS.append(_resolved_app)

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.urls"
ASGI_APPLICATION = "backend.asgi.application"
WSGI_APPLICATION = "backend.wsgi.application"

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

DATABASE_VENDOR_MAP: dict[str, str] = {
    alias: detect_db_vendor(db_config)
    for alias, db_config in DATABASES.items()
}

_unknown_vendor_aliases = [
    alias for alias, vendor in DATABASE_VENDOR_MAP.items()
    if vendor == DB_VENDOR_UNKNOWN
]

if _unknown_vendor_aliases:
    raise RuntimeError(
        "unsupported or unknown database vendor for aliases: "
        + ", ".join(_unknown_vendor_aliases)
        + ". Please set NS_VENDOR or ENGINE correctly."
    )

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
        raise RuntimeError(
            f"infra_db_router_map.{_infra_domain} points to undefined database alias: {_db_alias}"
        )

for _app_label, _db_alias in DATABASE_ROUTER_MAP.items():
    if not isinstance(_app_label, str) or not _app_label.strip():
        raise TypeError("database_router_map app label must be non-empty str")
    if not isinstance(_db_alias, str) or not _db_alias.strip():
        raise TypeError("database_router_map db alias must be non-empty str")
    if _db_alias not in DATABASES:
        raise RuntimeError(
            f"database_router_map.{_app_label} points to undefined database alias: {_db_alias}"
        )

DATABASE_ROUTERS = [
    "backend.db.routers.AppDatabaseRouter",
]

INFRA_SQL_ROOT = SQL_DIR

INFRA_DB_VENDOR_MAP: dict[str, str] = {
    infra_domain: DATABASE_VENDOR_MAP.get(db_alias, DB_VENDOR_UNKNOWN)
    for infra_domain, db_alias in INFRA_DB_ROUTER_MAP.items()
}

_unknown_infra_domains = [
    infra_domain
    for infra_domain, vendor in INFRA_DB_VENDOR_MAP.items()
    if vendor == DB_VENDOR_UNKNOWN
]
if _unknown_infra_domains:
    raise RuntimeError(
        "unsupported infra db vendor for domains: "
        + ", ".join(_unknown_infra_domains)
    )

INFRA_CREATE_SQL_PATH_MAP: dict[str, Path] = {
    infra_domain: build_infra_create_sql_path(
        sql_root=INFRA_SQL_ROOT,
        infra_domain=infra_domain,
        vendor=vendor,
    )
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
