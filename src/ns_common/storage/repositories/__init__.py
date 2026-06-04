# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_common.storage.repositories.memory import NsInMemoryObjectRefRepository, AsyncNsInMemoryObjectRefRepository

if TYPE_CHECKING:
    pass

__all__ = [
    "NsInMemoryObjectRefRepository",
    "AsyncNsInMemoryObjectRefRepository",
]
