# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.apps import AppConfig

if TYPE_CHECKING:
    pass


class RuntimeConnectorConfig(AppConfig):
    """Django app config for backend runtime connector commands."""

    name = "ns_backend.runtime_connector"
    label = "ns_backend_runtime_connector"
    verbose_name = "NsEvermore Backend Runtime Connector"
