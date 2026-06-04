# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.urls import path

from ns_backend.storage.views import StorageObjectViewSet

if TYPE_CHECKING:
    pass

urlpatterns = [
    path("object/upload",StorageObjectViewSet.as_view({"post": "upload_object"},required_permissions=("storage:object:upload",))),
    path("object/presigned-get",StorageObjectViewSet.as_view({"post": "presigned_get_url"},required_permissions=("storage:object:presigned_get",))),
    path("object-ref/list",StorageObjectViewSet.as_view({"post": "list_object_refs"},required_permissions=("storage:object_ref:list",))),
    path("object-ref/detail",StorageObjectViewSet.as_view({"post": "detail_object_ref"},required_permissions=("storage:object_ref:detail",))),
    path("object-ref/delete",StorageObjectViewSet.as_view({"post": "delete_object_ref"},required_permissions=("storage:object_ref:delete",))),
]
