# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.backend.cache.django_backend import NsCommonCacheBackend

if TYPE_CHECKING:
    pass

__all__ = [
    "NsCommonCacheBackend"
]
