# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

class DefaultCacheTimeout:
    """Sentinel for using configured default timeout."""


NS_CACHE_DEFAULT_TIMEOUT = DefaultCacheTimeout()
