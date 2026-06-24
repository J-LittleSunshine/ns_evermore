# -*- coding: utf-8 -*-
from __future__ import annotations

from django.urls import path

from ns_backend.iam.views import AuthViewSet

urlpatterns = [
    path("auth/login/", AuthViewSet.as_view({"post": "login"})),
    path("auth/refresh/", AuthViewSet.as_view({"post": "refresh"})),
    path("auth/logout/", AuthViewSet.as_view({"post": "logout"})),
    path("auth/profile/", AuthViewSet.as_view({"post": "profile"})),
    path("auth/current_user/", AuthViewSet.as_view({"post": "current_user"})),
    path("auth/permissions/", AuthViewSet.as_view({"post": "permissions"})),
    path("auth/menus/", AuthViewSet.as_view({"post": "menus"})),
]
