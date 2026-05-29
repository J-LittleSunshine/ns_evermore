# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.conf import settings

if TYPE_CHECKING:
    pass


class AppDatabaseRouter:
    INFRA_DEFAULT_DB_ALIAS = "default"

    @classmethod
    def get_target_db(cls, app_label: str) -> str | None:
        if app_label in settings.INFRA_DB_ROUTER_MAP:
            return settings.INFRA_DB_ROUTER_MAP[app_label]

        return settings.DATABASE_ROUTER_MAP.get(app_label)

    def db_for_read(self, model: Any, **hints: Any) -> str | None:  # noqa
        return self.get_target_db(model._meta.app_label)  # noqa

    def db_for_write(self, model: Any, **hints: Any) -> str | None:  # noqa
        return self.get_target_db(model._meta.app_label)  # noqa

    def allow_relation(self, obj1: Any, obj2: Any, **hints: Any) -> bool:  # noqa
        db1 = self.get_target_db(obj1._meta.app_label) or self.INFRA_DEFAULT_DB_ALIAS  # noqa
        db2 = self.get_target_db(obj2._meta.app_label) or self.INFRA_DEFAULT_DB_ALIAS  # noqa
        return db1 == db2

    def allow_migrate(self, db: str, app_label: str, model_name: str | None = None, **hints: Any) -> bool:  # noqa
        target_db = self.get_target_db(app_label)
        if target_db:
            return db == target_db
        return db == self.INFRA_DEFAULT_DB_ALIAS
