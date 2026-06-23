# -*- coding: utf-8 -*-
from __future__ import annotations

from django.urls import path

from ns_backend.system.views import SystemViewSet

urlpatterns = [
    path("health_check/", SystemViewSet.as_view({"post": "health_check"})),
    path("raise_validation_error/", SystemViewSet.as_view({"post": "raise_validation_error"})),
]
