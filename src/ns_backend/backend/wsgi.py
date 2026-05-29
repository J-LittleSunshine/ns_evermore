# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from ns_backend.backend.bootstrap import ensure_src_on_sys_path, show_banner

ensure_src_on_sys_path()
show_banner()

from django.core.wsgi import get_wsgi_application  # noqa: E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ns_backend.backend.settings")

application = get_wsgi_application()
