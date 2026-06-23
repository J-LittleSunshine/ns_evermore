from pathlib import Path

from ns_common import ns_config
from ns_common.paths import DATA_DIR, ensure_runtime_dirs

ensure_runtime_dirs()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = ns_config.backend.secret_key

DEBUG = ns_config.backend.debug

ALLOWED_HOSTS = ns_config.backend.allowed_hosts

INSTALLED_APPS = [
    'rest_framework',
    'adrf',
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
        "NAME": DATA_DIR / "db.sqlite3",
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
