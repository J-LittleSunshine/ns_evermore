# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.apps import AppConfig

if TYPE_CHECKING:
    pass


class StorageConfig(AppConfig):
    """Storage infrastructure app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "ns_backend.storage"
    label = "storage"

    def ready(self) -> None:
        """Register Django object ref repositories into ns_common storage registry."""
        from ns_backend.storage.repositories import AsyncDjangoObjectRefRepository, DjangoObjectRefRepository
        from ns_common.storage import register_async_object_ref_repository, register_object_ref_repository

        register_object_ref_repository(DjangoObjectRefRepository(), replace=True)
        register_async_object_ref_repository(AsyncDjangoObjectRefRepository(), replace=True)
