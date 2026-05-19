# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    pass


class AppDatabaseRouter:
    def db_for_read(self, model, **hints):
        return settings.DATABASE_ROUTER_MAP.get(model._meta.app_label)

    def db_for_write(self, model, **hints):
        return settings.DATABASE_ROUTER_MAP.get(model._meta.app_label)

    def allow_relation(self, obj1, obj2, **hints):
        db1 = settings.DATABASE_ROUTER_MAP.get(obj1._meta.app_label, "default")
        db2 = settings.DATABASE_ROUTER_MAP.get(obj2._meta.app_label, "default")
        return db1 == db2

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        target_db = settings.DATABASE_ROUTER_MAP.get(app_label)

        if target_db:
            return db == target_db

        return db == "default"
