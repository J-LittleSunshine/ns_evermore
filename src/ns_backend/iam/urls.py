# -*- coding: utf-8 -*-
from __future__ import annotations

from django.urls import path

from ns_backend.iam.views import (
    AuthViewSet,
    CompanyViewSet,
    DepartmentViewSet,
    PermissionViewSet,
    SubsidiaryViewSet,
)

urlpatterns = [
    path("auth/login/", AuthViewSet.as_view({"post": "login"})),
    path("auth/refresh/", AuthViewSet.as_view({"post": "refresh"})),
    path("auth/logout/", AuthViewSet.as_view({"post": "logout"})),
    path("auth/profile/", AuthViewSet.as_view({"post": "profile"})),
    path("auth/current_user/", AuthViewSet.as_view({"post": "current_user"})),
    path("auth/permissions/", AuthViewSet.as_view({"post": "permissions"})),
    path("auth/menus/", AuthViewSet.as_view({"post": "menus"})),
    path("auth/data_scopes/", AuthViewSet.as_view({"post": "data_scopes"})),

    path("company/list/", CompanyViewSet.as_view({"post": "list"})),
    path("company/detail/", CompanyViewSet.as_view({"post": "detail"})),
    path("company/create/", CompanyViewSet.as_view({"post": "create"})),
    path("company/update/", CompanyViewSet.as_view({"post": "update"})),
    path("company/delete/", CompanyViewSet.as_view({"post": "delete"})),

    path("subsidiary/list/", SubsidiaryViewSet.as_view({"post": "list"})),
    path("subsidiary/detail/", SubsidiaryViewSet.as_view({"post": "detail"})),
    path("subsidiary/create/", SubsidiaryViewSet.as_view({"post": "create"})),
    path("subsidiary/update/", SubsidiaryViewSet.as_view({"post": "update"})),
    path("subsidiary/delete/", SubsidiaryViewSet.as_view({"post": "delete"})),

    path("department/list/", DepartmentViewSet.as_view({"post": "list"})),
    path("department/detail/", DepartmentViewSet.as_view({"post": "detail"})),
    path("department/create/", DepartmentViewSet.as_view({"post": "create"})),
    path("department/update/", DepartmentViewSet.as_view({"post": "update"})),
    path("department/delete/", DepartmentViewSet.as_view({"post": "delete"})),

    path("permission/list/", PermissionViewSet.as_view({"post": "list"})),
    path("permission/detail/", PermissionViewSet.as_view({"post": "detail"})),
    path("permission/create/", PermissionViewSet.as_view({"post": "create"})),
    path("permission/update/", PermissionViewSet.as_view({"post": "update"})),
    path("permission/delete/", PermissionViewSet.as_view({"post": "delete"})),
]
