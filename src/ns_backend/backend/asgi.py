import os

from .path_bootstrap import ensure_src_on_sys_path

ensure_src_on_sys_path()

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

application = get_asgi_application()
