# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.apps import AppConfig

if TYPE_CHECKING:
    pass


class SystemConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ns_backend.system"
    label = "system"
