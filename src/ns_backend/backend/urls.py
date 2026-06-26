# -*- coding: utf-8 -*-
from __future__ import annotations

from backend.app_loader import build_urlpatterns
from ns_common import ns_config

urlpatterns = build_urlpatterns(ns_config.backend.installed_apps)
