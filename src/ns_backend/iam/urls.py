# -*- coding: utf-8 -*-
from __future__ import annotations

from django.urls import path

from ns_backend.iam.views import IamViewSet

urlpatterns = [
    path("health_check/", IamViewSet.as_view({"post": "health_check"})),
]
