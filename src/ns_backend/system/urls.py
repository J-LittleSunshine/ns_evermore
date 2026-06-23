# -*- coding: utf-8 -*-
from __future__ import annotations

from django.urls import path

from ns_backend.system.views import SystemViewSet

urlpatterns = [
    path(
        "ping/", SystemViewSet.as_view(
            {
                "post": "ping"
            }
        )
    ),
    path(
        "raise_validation_error/", SystemViewSet.as_view(
            {
                "post": "raise_validation_error"
            }
        ),
    ),
]
