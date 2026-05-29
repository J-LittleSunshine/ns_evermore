import os

from .bootstrap import ensure_src_on_sys_path, show_banner

ensure_src_on_sys_path()

show_banner()

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

application = get_wsgi_application()
