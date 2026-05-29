import os

from .path_bootstrap import ensure_src_on_sys_path

ensure_src_on_sys_path()

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")

application = get_wsgi_application()
