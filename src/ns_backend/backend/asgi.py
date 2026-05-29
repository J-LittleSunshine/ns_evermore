import os

from ns_backend.backend.bootstrap import ensure_src_on_sys_path, show_banner

ensure_src_on_sys_path()

show_banner()

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

application = get_asgi_application()
