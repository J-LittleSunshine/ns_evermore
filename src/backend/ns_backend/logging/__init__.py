# -*- coding: utf-8 -*-
from __future__ import annotations

from ns_backend.logging.django import get_django_logger
from ns_backend.logging.runtime import safe_emit_log_event, short_identifier

__all__ = ["get_django_logger", "safe_emit_log_event", "short_identifier"]

