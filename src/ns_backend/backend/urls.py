# -*- coding: utf-8 -*-
from __future__ import annotations

from django.urls import (
    include,
    path
)

urlpatterns = [
    path("api/system/", include("ns_backend.system.urls")),
]
