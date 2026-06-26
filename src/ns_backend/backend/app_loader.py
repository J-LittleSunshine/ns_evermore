# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib
import importlib.util
import inspect
from typing import TYPE_CHECKING

from django.apps import AppConfig
from django.urls import (
    include,
    path
)

from ns_common.exceptions import NsConfigError

if TYPE_CHECKING:
    from django.urls.resolvers import (
        URLPattern,
        URLResolver
    )

BASE_DJANGO_APPS: tuple[str, ...] = (
    "rest_framework",
    "adrf",
)


def normalize_backend_app_keys(app_keys: list[str]) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()

    for app_key in app_keys:
        normalized_app_key = app_key.strip()

        if normalized_app_key in seen:
            raise NsConfigError(
                "backend.installed_apps contains duplicated item.",
                details={
                    "field": "backend.installed_apps",
                    "value": normalized_app_key,
                },
            )

        seen.add(normalized_app_key)
        normalized.append(normalized_app_key)

    return normalized


def assert_backend_app_package_exists(app_key: str) -> None:
    package_name = f"ns_backend.{app_key}"

    if importlib.util.find_spec(package_name) is None:
        raise NsConfigError(
            "backend.installed_apps contains unknown backend app.",
            details={
                "field": "backend.installed_apps",
                "value": app_key,
                "expected_package": package_name,
            },
        )


def discover_app_config_path(app_key: str) -> str | None:
    apps_module_name = f"ns_backend.{app_key}.apps"

    if importlib.util.find_spec(apps_module_name) is None:
        return None

    apps_module = importlib.import_module(apps_module_name)

    app_config_classes: list[type[AppConfig]] = []

    for _, value in inspect.getmembers(apps_module, inspect.isclass):
        if not issubclass(value, AppConfig):
            continue

        if value is AppConfig:
            continue

        if value.__module__ != apps_module.__name__:
            continue

        app_config_classes.append(value)

    if not app_config_classes:
        raise NsConfigError(
            "backend app apps.py exists but AppConfig was not found.",
            details={
                "field": "backend.installed_apps",
                "value": app_key,
                "module": apps_module_name,
            },
        )

    if len(app_config_classes) > 1:
        raise NsConfigError(
            "backend app apps.py contains multiple AppConfig classes.",
            details={
                "field": "backend.installed_apps",
                "value": app_key,
                "module": apps_module_name,
                "classes": [
                    app_config_class.__name__
                    for app_config_class in app_config_classes
                ],
            },
        )

    app_config_class = app_config_classes[0]
    return f"{apps_module_name}.{app_config_class.__name__}"


def discover_urlconf(app_key: str) -> str | None:
    urlconf = f"ns_backend.{app_key}.urls"

    if importlib.util.find_spec(urlconf) is None:
        return None

    return urlconf


def build_installed_apps(app_keys: list[str]) -> list[str]:
    installed_apps = list(BASE_DJANGO_APPS)

    for app_key in normalize_backend_app_keys(app_keys):
        assert_backend_app_package_exists(app_key)

        app_config_path = discover_app_config_path(app_key)

        if app_config_path:
            installed_apps.append(app_config_path)

    return installed_apps


def build_urlpatterns(app_keys: list[str]) -> list["URLPattern | URLResolver"]:
    urlpatterns: list[URLPattern | URLResolver] = []

    for app_key in normalize_backend_app_keys(app_keys):
        assert_backend_app_package_exists(app_key)

        urlconf = discover_urlconf(app_key)

        if urlconf:
            urlpatterns.append(
                path(f"api/{app_key}/", include(urlconf))
            )

    return urlpatterns
