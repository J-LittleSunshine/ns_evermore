# -*- coding: utf-8 -*-
from __future__ import annotations

from django.conf import settings

IAM_DB_ALIAS = settings.DATABASE_ROUTER_MAP.get("iam", "default")

