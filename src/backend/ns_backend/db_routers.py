# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.conf import settings

if TYPE_CHECKING:
    pass


class AppDatabaseRouter:
    INFRA_DEFAULT_DB_ALIAS = "default"
    IAM_APP_LABEL = "iam"

    @classmethod
    def get_target_db(cls, app_label: str):
        if app_label == cls.IAM_APP_LABEL:
            return settings.INFRA_DB_ROUTER_MAP[cls.IAM_APP_LABEL]

        return settings.DATABASE_ROUTER_MAP.get(app_label)

    def db_for_read(self, model, **hints):  # noqa
        return self.get_target_db(model._meta.app_label)  # noqa

    def db_for_write(self, model, **hints):  # noqa
        return self.get_target_db(model._meta.app_label)  # noqa

    def allow_relation(self, obj1, obj2, **hints):  # noqa
        db1 = self.get_target_db(obj1._meta.app_label) or self.INFRA_DEFAULT_DB_ALIAS  # noqa
        db2 = self.get_target_db(obj2._meta.app_label) or self.INFRA_DEFAULT_DB_ALIAS  # noqa
        return db1 == db2

    def allow_migrate(self, db, app_label, model_name=None, **hints):  # noqa
        target_db = self.get_target_db(app_label)

        if target_db:
            return db == target_db

        return db == self.INFRA_DEFAULT_DB_ALIAS
