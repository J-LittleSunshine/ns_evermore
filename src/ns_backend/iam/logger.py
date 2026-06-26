# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_common import get_ns_logger

if TYPE_CHECKING:
    pass

IAM_LOGGER = get_ns_logger("ns_backend.iam", True)

__all__ = [
    "IAM_LOGGER",
]