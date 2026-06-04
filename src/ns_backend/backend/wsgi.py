# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from ns_backend import __version__
from ns_backend.backend.bootstrap import ensure_src_on_sys_path, show_banner
from ns_backend.backend.common.logger import logger

ensure_src_on_sys_path()
show_banner()

from django.core.wsgi import get_wsgi_application  # noqa: E402

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ns_backend.backend.settings")

logger.info(
    "system startup",
    extra={
        "event": "system_startup",
        "version": __version__,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
    },
)
application = get_wsgi_application()
