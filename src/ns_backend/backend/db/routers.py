# -*- coding: utf-8 -*-
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    pass


class AppDatabaseRouter:
    DEFAULT_DB_ALIAS = "default"

    @classmethod
    def get_target_db(cls, app_label: str) -> str | None:
        database_router_map = getattr(settings, "DATABASE_ROUTER_MAP", {})

        if not isinstance(database_router_map, Mapping):
            return None

        return database_router_map.get(app_label)

    def db_for_read(self, model: Any, **hints: Any) -> str | None:  # noqa
        return self.get_target_db(model._meta.app_label)  # noqa

    def db_for_write(self, model: Any, **hints: Any) -> str | None:  # noqa
        return self.get_target_db(model._meta.app_label)  # noqa

    def allow_relation(self, obj1: Any, obj2: Any, **hints: Any) -> bool | None:  # noqa
        db1 = self.get_target_db(obj1._meta.app_label)  # noqa
        db2 = self.get_target_db(obj2._meta.app_label)  # noqa

        if db1 is None and db2 is None:
            return None

        return (db1 or self.DEFAULT_DB_ALIAS) == (db2 or self.DEFAULT_DB_ALIAS)

    def allow_migrate(self, db: str, app_label: str, model_name: str | None = None, **hints: Any) -> bool:
        target_db = self.get_target_db(app_label)

        if target_db:
            return db == target_db

        return db == self.DEFAULT_DB_ALIAS
