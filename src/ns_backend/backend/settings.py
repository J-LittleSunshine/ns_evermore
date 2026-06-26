from pathlib import Path

from backend.app_loader import build_installed_apps
from ns_common import ns_config
from ns_common.paths import (
    DATA_DIR,
    ensure_runtime_dirs
)

ensure_runtime_dirs()

BASE_DIR = Path(__file__).resolve().parent.parent

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

DATABASES = ns_config.backend.databases or {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "ns_db.sqlite3",
    }
}

DATABASE_ROUTER_MAP = ns_config.backend.database_router_map

DATABASE_ROUTERS = [
    "backend.db.routers.AppDatabaseRouter",
]

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

IAM_DECISION_AUDIT_ENABLED = ns_config.backend.iam_decision_audit_enabled
IAM_DECISION_AUDIT_STRICT_MODE = ns_config.backend.iam_decision_audit_strict_mode
IAM_OPERATION_AUDIT_ENABLED = ns_config.backend.iam_operation_audit_enabled
IAM_OPERATION_AUDIT_STRICT_MODE = ns_config.backend.iam_operation_audit_strict_mode

IAM_AUTH_BACKOFF_ENABLED = ns_config.backend.iam_auth_backoff_enabled
IAM_AUTH_BACKOFF_MAX_RETRIES = ns_config.backend.iam_auth_backoff_max_retries
IAM_AUTH_BACKOFF_BASE_DELAY_MS = ns_config.backend.iam_auth_backoff_base_delay_ms
IAM_AUTH_BACKOFF_MAX_DELAY_MS = ns_config.backend.iam_auth_backoff_max_delay_ms
IAM_AUTH_BACKOFF_JITTER_RATIO = ns_config.backend.iam_auth_backoff_jitter_ratio
