# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_common.logger import get_ns_logger

if TYPE_CHECKING:
    pass

logger = get_ns_logger("backend", True)
iam_logger = get_ns_logger("iam", True)
