# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_common.storage.repositories.memory import AsyncNsInMemoryObjectRefRepository, NsInMemoryObjectRefRepository
from ns_common.storage.repositories.registry import (
    NsObjectRefRepositoryRegistry,
    clear_object_ref_repository_registry,
    get_async_object_ref_repository,
    get_object_ref_repository,
    register_async_object_ref_repository,
    register_object_ref_repository,
    unregister_async_object_ref_repository,
    unregister_object_ref_repository,
)

if TYPE_CHECKING:
    pass

__all__ = [
    "NsInMemoryObjectRefRepository",
    "AsyncNsInMemoryObjectRefRepository",
    "NsObjectRefRepositoryRegistry",
    "register_object_ref_repository",
    "get_object_ref_repository",
    "unregister_object_ref_repository",
    "register_async_object_ref_repository",
    "get_async_object_ref_repository",
    "unregister_async_object_ref_repository",
    "clear_object_ref_repository_registry",
]
