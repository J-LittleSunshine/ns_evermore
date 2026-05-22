# -*- coding: utf-8 -*-
from __future__ import annotations

from ns_backend.logger import get_logger


def get_module_logger(log_name: str = "ns_backend"):
    """Low-intrusion logger helper that reuses existing logger infrastructure."""
    return get_logger(log_name)


__all__ = ["get_module_logger"]

