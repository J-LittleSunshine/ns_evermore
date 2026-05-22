"""
ASGI config for ns_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

from __future__ import annotations

import os

from ns_backend.path_bootstrap import ensure_project_src_on_path

ensure_project_src_on_path()

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ns_backend.settings')

application = get_asgi_application()
