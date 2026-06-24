from pathlib import Path

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

INSTALLED_APPS = [
    'rest_framework',
    'adrf',

    'ns_backend.iam.apps.IamConfig',
]

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
