import json
import os
from json import JSONDecodeError
from pathlib import Path
from typing import Dict, Any, List

BASE_DIR = Path(__file__).resolve().parent.parent

ETC_DIR = BASE_DIR.parent.parent / "etc"
ETC_DIR.mkdir(parents=True, exist_ok=True)

DATA_DIR = BASE_DIR.parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)


BACKEND_CONFIG_FILE_PATH = ETC_DIR / "backend_config.json"
if not BACKEND_CONFIG_FILE_PATH.exists():
    BACKEND_CONFIG_FILE_PATH.write_text("{}", encoding="utf-8")

try:
    CONFIG: Dict[str, Any] = json.loads(BACKEND_CONFIG_FILE_PATH.read_text(encoding="utf-8"))
except JSONDecodeError:
    CONFIG = {}

BACKEND_CONFIG = CONFIG.get("backend", {})


def _coerce_positive_int(value, default: int) -> int:
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

SECRET_KEY = BACKEND_CONFIG.get("secret_key", "") or os.getenv("NS_SECRET_KEY") or ""
if not SECRET_KEY:
    raise RuntimeError("secret_key is not set")

JWT_SECRET_KEY = BACKEND_CONFIG.get("jwt_secret_key", "") or os.getenv("NS_JWT_SECRET_KEY") or ""
if not JWT_SECRET_KEY:
    raise RuntimeError("jwt_secret_key is not set")

ACCESS_TOKEN_EXPIRE_MINUTES = BACKEND_CONFIG.get("access_token_expire_minutes", 30)
REFRESH_TOKEN_EXPIRE_DAYS = BACKEND_CONFIG.get("refresh_token_expire_days", 14)
JWT_ISSUER = BACKEND_CONFIG.get("jwt_issuer", "ns_evermore")
JWT_LEEWAY_SECONDS = BACKEND_CONFIG.get("jwt_leeway_seconds", 30)
JWT_MIN_SECRET_LENGTH = BACKEND_CONFIG.get("jwt_min_secret_length", 32)

PASSWORD_TRANSPORT_MODE = (
    BACKEND_CONFIG.get("password_transport_mode", "")
    or os.getenv("NS_PASSWORD_TRANSPORT_MODE")
    or "plain"
).strip().lower()
PASSWORD_TRANSPORT_ALLOWED_MODES = ("plain", "rsa_oaep")
if PASSWORD_TRANSPORT_MODE not in PASSWORD_TRANSPORT_ALLOWED_MODES:
    raise RuntimeError(
        f"password_transport_mode must be one of: {', '.join(PASSWORD_TRANSPORT_ALLOWED_MODES)}"
    )

_password_transport_max_payload_length = _coerce_positive_int(
    BACKEND_CONFIG.get("password_transport_max_payload_length"),
    0,
)
if _password_transport_max_payload_length <= 0:
    _password_transport_max_payload_length = _coerce_positive_int(
        os.getenv("NS_PASSWORD_TRANSPORT_MAX_PAYLOAD_LENGTH"),
        4096,
    )
PASSWORD_TRANSPORT_MAX_PAYLOAD_LENGTH = _password_transport_max_payload_length

_password_plaintext_max_length = _coerce_positive_int(
    BACKEND_CONFIG.get("password_plaintext_max_length"),
    0,
)
if _password_plaintext_max_length <= 0:
    _password_plaintext_max_length = _coerce_positive_int(
        os.getenv("NS_PASSWORD_PLAINTEXT_MAX_LENGTH"),
        256,
    )
PASSWORD_PLAINTEXT_MAX_LENGTH = _password_plaintext_max_length
PASSWORD_RSA_PRIVATE_KEY = (
    BACKEND_CONFIG.get("password_rsa_private_key", "")
    or os.getenv("NS_PASSWORD_RSA_PRIVATE_KEY")
    or ""
)
PASSWORD_RSA_PRIVATE_KEY_FILE = (
    BACKEND_CONFIG.get("password_rsa_private_key_file", "")
    or os.getenv("NS_PASSWORD_RSA_PRIVATE_KEY_FILE")
    or ""
)
PASSWORD_RSA_PRIVATE_KEY_PASSPHRASE = (
    BACKEND_CONFIG.get("password_rsa_private_key_passphrase", "")
    or os.getenv("NS_PASSWORD_RSA_PRIVATE_KEY_PASSPHRASE")
    or ""
)
if PASSWORD_TRANSPORT_MODE == "rsa_oaep" and not (
    PASSWORD_RSA_PRIVATE_KEY or PASSWORD_RSA_PRIVATE_KEY_FILE
):
    raise RuntimeError(
        "password_rsa_private_key or password_rsa_private_key_file is required when password_transport_mode is rsa_oaep"
    )

LOGIN_MAX_FAILED_COUNT = BACKEND_CONFIG.get("log_in_max_failed_count", 5)
LOGIN_LOCK_MINUTES = BACKEND_CONFIG.get("log_in_lock_minutes", 15)

DEBUG = BACKEND_CONFIG.get("debug", False)

ALLOWED_HOSTS: List[str] = BACKEND_CONFIG.get("allowed_hosts", [])

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "adrf",
]

_LOAD_APPS: Dict[str, bool] = BACKEND_CONFIG.get("loaded_apps", {})
for app, install in _LOAD_APPS.items():
    if not isinstance(app, str):
        raise TypeError("app must be str")
    if not isinstance(install, bool):
        raise TypeError("install must be bool")
    if install:
        INSTALLED_APPS.append(app)

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "ns_backend.urls"

WSGI_APPLICATION = "ns_backend.wsgi.application"

ASGI_APPLICATION = "ns_backend.asgi.application"
_DATABASES_CONFIG = BACKEND_CONFIG.get("databases", {})

if not _DATABASES_CONFIG:
    _DATABASES_CONFIG = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": str(DATA_DIR / "db.sqlite3"),
        }
    }

DATABASES = {}

for _db_alias, _db_config in _DATABASES_CONFIG.items():
    if not isinstance(_db_alias, str):
        raise TypeError("database alias must be str")

    if not isinstance(_db_config, dict):
        raise TypeError("database config must be dict")

    db_config = _db_config.copy()

    if db_config.get("ENGINE") == "django.db.backends.sqlite3":
        name = db_config.get("NAME")

        if name and not Path(str(name)).is_absolute():
            db_config["NAME"] = str(DATA_DIR / str(name))

    DATABASES[_db_alias] = db_config

DATABASE_ROUTER_MAP = BACKEND_CONFIG.get("database_router_map", {})

if not isinstance(DATABASE_ROUTER_MAP, dict):
    raise TypeError("database_router_map must be dict")

DATABASE_ROUTERS = [
    "ns_backend.db_routers.AppDatabaseRouter",
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
