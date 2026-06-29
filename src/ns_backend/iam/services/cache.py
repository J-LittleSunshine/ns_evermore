# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import json
from collections.abc import (
    Awaitable,
    Callable,
)
from inspect import isawaitable
from threading import RLock
from typing import (
    Any,
    TYPE_CHECKING,
    TypeVar,
)

from ns_common import (
    get_ns_logger,
    ns_config,
)
from ns_common.cache import (
    get_async_cache_client,
    get_cache_client,
)
from ns_common.cache.keys import validate_cache_key_part
from ns_common.exceptions import NsValidationError

if TYPE_CHECKING:
    from ns_common.cache import (
        AsyncCacheClient,
        CacheClient,
    )

T = TypeVar("T")

logger = get_ns_logger("ns_backend.iam.cache", True)


class IamCacheService:
    NAMESPACE = "iam"

    AUTHZ_VERSION_KEY = "authz_version"
    AVAILABILITY_PROBE_KEY = "availability.probe"
    AVAILABILITY_PROBE_TTL_SECONDS = 5

    _MISS = object()

    _availability_lock = RLock()
    _availability_checked: bool = False
    _available: bool = False

    EVENT_HIT = "hit"
    EVENT_MISS = "miss"
    EVENT_BYPASS = "bypass"

    _stats_lock = RLock()
    _stats: dict[str, int] = {
        EVENT_HIT: 0,
        EVENT_MISS: 0,
        EVENT_BYPASS: 0,
    }

    @classmethod
    def enabled(cls) -> bool:
        return bool(getattr(ns_config.backend, "iam_cache_enabled", False))

    @classmethod
    def cache_ttl_seconds(cls) -> int:
        return max(int(getattr(ns_config.backend, "iam_cache_ttl_seconds", 300)), 1)

    @classmethod
    def user_cache_ttl_seconds(cls) -> int:
        return max(int(getattr(ns_config.backend, "iam_user_cache_ttl_seconds", 120)), 1)

    @classmethod
    def authz_cache_ttl_seconds(cls) -> int:
        return max(int(getattr(ns_config.backend, "iam_authz_cache_ttl_seconds", 300)), 1)

    @classmethod
    def get_client(cls) -> "CacheClient | None":
        if not cls.enabled():
            return None

        try:
            return get_cache_client(namespace=cls.NAMESPACE)
        except Exception as exc:  # noqa
            logger.warning(
                "iam cache client initialization failed",
                exc_info=True,
                extra={
                    "namespace": cls.NAMESPACE,
                    "exception_class": exc.__class__.__name__,
                },
            )
            return None

    @classmethod
    def get_async_client(cls) -> "AsyncCacheClient | None":
        if not cls.enabled():
            return None

        try:
            return get_async_cache_client(namespace=cls.NAMESPACE)
        except Exception as exc:  # noqa
            logger.warning(
                "iam async cache client initialization failed",
                exc_info=True,
                extra={
                    "namespace": cls.NAMESPACE,
                    "exception_class": exc.__class__.__name__,
                },
            )
            return None

    @classmethod
    def is_available(cls, *, force_check: bool = False) -> bool:
        if not cls.enabled():
            return False

        with cls._availability_lock:
            if cls._availability_checked and not force_check:
                return cls._available

            available = cls._probe_available()
            cls._availability_checked = True
            cls._available = available

            if not available:
                logger.warning(
                    "iam cache is not available and will be bypassed",
                    extra={
                        "namespace": cls.NAMESPACE,
                        "cache_backend": getattr(ns_config.cache, "backend", None),
                    },
                )

            return cls._available

    @classmethod
    def _probe_available(cls) -> bool:
        client = cls.get_client()
        if client is None:
            return False

        probe_value = {
            "available": True,
            "namespace": cls.NAMESPACE,
        }

        try:
            if not client.set(
                    cls.AVAILABILITY_PROBE_KEY,
                    probe_value,
                    ttl=cls.AVAILABILITY_PROBE_TTL_SECONDS,
            ):
                return False

            cached_value = client.get(cls.AVAILABILITY_PROBE_KEY, default=None)
            return cached_value == probe_value
        except Exception as exc:  # noqa
            logger.warning(
                "iam cache availability probe failed",
                exc_info=True,
                extra={
                    "namespace": cls.NAMESPACE,
                    "exception_class": exc.__class__.__name__,
                },
            )
            return False
        finally:
            try:
                client.delete(cls.AVAILABILITY_PROBE_KEY)
            except Exception:  # noqa
                pass

    @classmethod
    def _mark_unavailable(cls, *, operation: str, exc: Exception) -> None:
        with cls._availability_lock:
            cls._availability_checked = True
            cls._available = False

        cls._record_cache_event(
            cls.EVENT_BYPASS,
            operation=operation,
            reason="operation_failed",
        )

        logger.warning(
            "iam cache operation failed and cache will be bypassed",
            exc_info=True,
            extra={
                "operation": operation,
                "namespace": cls.NAMESPACE,
                "exception_class": exc.__class__.__name__,
            },
        )

    @classmethod
    def _record_cache_event(cls, event: str, *, operation: str, key: Any = None, reason: str | None = None, authz_version: int | None = None) -> None:
        if event in cls._stats:
            with cls._stats_lock:
                cls._stats[event] = cls._stats.get(event, 0) + 1

        logger.debug(
            "iam cache %s",
            event,
            extra={
                "event": event,
                "operation": operation,
                "reason": reason,
                "namespace": cls.NAMESPACE,
                "key_hash": cls._build_observable_key_hash(key),
                "authz_version": authz_version,
            },
        )

    @classmethod
    def _record_cache_bypass(cls, *, operation: str, key: Any = None, reason: str, authz_version: int | None = None) -> None:
        cls._record_cache_event(
            cls.EVENT_BYPASS,
            operation=operation,
            key=key,
            reason=reason,
            authz_version=authz_version,
        )

    @classmethod
    def _build_observable_key_hash(cls, key: Any) -> str | None:
        if key is None:
            return None

        try:
            return cls.build_hash_key_part(key)[:16]
        except Exception:  # noqa
            return None

    @classmethod
    def get_stats(cls) -> dict[str, Any]:
        with cls._stats_lock:
            hit_count = int(cls._stats.get(cls.EVENT_HIT, 0))
            miss_count = int(cls._stats.get(cls.EVENT_MISS, 0))
            bypass_count = int(cls._stats.get(cls.EVENT_BYPASS, 0))

        total = hit_count + miss_count + bypass_count
        cache_lookup_total = hit_count + miss_count

        return {
            "hit": hit_count,
            "miss": miss_count,
            "bypass": bypass_count,
            "total": total,
            "cache_lookup_total": cache_lookup_total,
            "hit_rate": round(hit_count / cache_lookup_total, 6) if cache_lookup_total else 0.0,
            "miss_rate": round(miss_count / cache_lookup_total, 6) if cache_lookup_total else 0.0,
            "bypass_rate": round(bypass_count / total, 6) if total else 0.0,
        }

    @classmethod
    def reset_stats(cls) -> None:
        with cls._stats_lock:
            cls._stats = {
                cls.EVENT_HIT: 0,
                cls.EVENT_MISS: 0,
                cls.EVENT_BYPASS: 0,
            }

    @staticmethod
    def build_hash_key_part(value: Any) -> str:
        raw_text = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            default=str,
            separators=(",", ":"),
        )
        return hashlib.sha256(raw_text.encode("utf-8")).hexdigest()

    @classmethod
    def _normalize_key_part(cls, key: Any) -> str:
        if isinstance(key, str):
            try:
                return validate_cache_key_part(key, "iam_cache_key")
            except NsValidationError:
                pass

        return cls.build_hash_key_part(key)

    @classmethod
    def _build_versioned_key(cls, key: Any, authz_version: int) -> str:
        key_part = cls._normalize_key_part(key)
        return f"v{authz_version}.{key_part}"

    @staticmethod
    def _parse_positive_int(value: Any) -> int | None:
        if isinstance(value, bool):
            return None

        if isinstance(value, int):
            return value if value > 0 else None

        if isinstance(value, str):
            try:
                parsed_value = int(value)
            except ValueError:
                return None

            return parsed_value if parsed_value > 0 else None

        return None

    @classmethod
    def get_authz_version(cls) -> int | None:
        if not cls.is_available():
            return None

        client = cls.get_client()
        if client is None:
            return None

        try:
            cached_value = client.get(cls.AUTHZ_VERSION_KEY, default=cls._MISS)
            version = cls._parse_positive_int(cached_value)

            if version is not None:
                client.touch(
                    cls.AUTHZ_VERSION_KEY,
                    ttl=cls.authz_cache_ttl_seconds(),
                )
                return version

            client.add(
                cls.AUTHZ_VERSION_KEY,
                1,
                ttl=cls.authz_cache_ttl_seconds(),
            )

            cached_value = client.get(cls.AUTHZ_VERSION_KEY, default=1)
            version = cls._parse_positive_int(cached_value)
            return version or 1
        except Exception as exc:  # noqa
            cls._mark_unavailable(operation="get_authz_version", exc=exc)
            return None

    @classmethod
    def bump_authz_version(cls) -> int | None:
        if not cls.is_available(force_check=True):
            return None

        client = cls.get_client()
        if client is None:
            return None

        try:
            client.add(
                cls.AUTHZ_VERSION_KEY,
                1,
                ttl=cls.authz_cache_ttl_seconds(),
            )
            version = client.incr(cls.AUTHZ_VERSION_KEY, 1)
            client.touch(
                cls.AUTHZ_VERSION_KEY,
                ttl=cls.authz_cache_ttl_seconds(),
            )
            return version
        except Exception as exc:  # noqa
            logger.error(
                "iam authz cache version bump failed",
                exc_info=True,
                extra={
                    "namespace": cls.NAMESPACE,
                    "exception_class": exc.__class__.__name__,
                },
            )
            cls._mark_unavailable(operation="bump_authz_version", exc=exc)
            return None

    @classmethod
    async def aget_authz_version(cls) -> int | None:
        if not cls.is_available():
            return None

        client = cls.get_async_client()
        if client is None:
            return None

        try:
            cached_value = await client.get(cls.AUTHZ_VERSION_KEY, default=cls._MISS)
            version = cls._parse_positive_int(cached_value)

            if version is not None:
                await client.touch(
                    cls.AUTHZ_VERSION_KEY,
                    ttl=cls.authz_cache_ttl_seconds(),
                )
                return version

            await client.add(
                cls.AUTHZ_VERSION_KEY,
                1,
                ttl=cls.authz_cache_ttl_seconds(),
            )

            cached_value = await client.get(cls.AUTHZ_VERSION_KEY, default=1)
            version = cls._parse_positive_int(cached_value)
            return version or 1
        except Exception as exc:  # noqa
            cls._mark_unavailable(operation="aget_authz_version", exc=exc)
            return None

    @classmethod
    async def abump_authz_version(cls) -> int | None:
        if not cls.is_available(force_check=True):
            return None

        client = cls.get_async_client()
        if client is None:
            return None

        try:
            await client.add(
                cls.AUTHZ_VERSION_KEY,
                1,
                ttl=cls.authz_cache_ttl_seconds(),
            )
            version = await client.incr(cls.AUTHZ_VERSION_KEY, 1)
            await client.touch(
                cls.AUTHZ_VERSION_KEY,
                ttl=cls.authz_cache_ttl_seconds(),
            )
            return version
        except Exception as exc:  # noqa
            logger.error(
                "iam authz cache version bump failed",
                exc_info=True,
                extra={
                    "namespace": cls.NAMESPACE,
                    "exception_class": exc.__class__.__name__,
                },
            )
            cls._mark_unavailable(operation="abump_authz_version", exc=exc)
            return None

    @classmethod
    def build_user_fingerprint(cls, user: Any) -> str:
        payload = {
            "user_id": cls._get_user_value(user, "id"),
            "user_type": cls._get_user_value(user, "user_type"),
            "company_id": cls._get_user_value(user, "company_id"),
            "subsidiary_id": cls._get_user_value(user, "subsidiary_id"),
            "department_id": cls._get_user_value(user, "department_id"),
            "is_staff": bool(cls._get_user_value(user, "is_staff")),
            "is_superuser": bool(cls._get_user_value(user, "is_superuser")),
            "is_active": bool(cls._get_user_value(user, "is_active")),
        }
        return cls.build_hash_key_part(payload)

    @staticmethod
    def _get_user_value(user: Any, field_name: str) -> Any:
        if user is None:
            return None

        if isinstance(user, dict):
            return user.get(field_name)

        return getattr(user, field_name, None)

    @classmethod
    def get(cls, key: Any, default: Any = None) -> Any:
        operation = "get"

        if not cls.enabled():
            cls._record_cache_bypass(
                operation=operation,
                key=key,
                reason="disabled",
            )
            return default

        if not cls.is_available():
            cls._record_cache_bypass(
                operation=operation,
                key=key,
                reason="unavailable",
            )
            return default

        authz_version = cls.get_authz_version()
        if authz_version is None:
            cls._record_cache_bypass(
                operation=operation,
                key=key,
                reason="authz_version_unavailable",
            )
            return default

        client = cls.get_client()
        if client is None:
            cls._record_cache_bypass(
                operation=operation,
                key=key,
                reason="client_unavailable",
                authz_version=authz_version,
            )
            return default

        try:
            cache_key = cls._build_versioned_key(key, authz_version)
            cached_value = client.get(
                cache_key,
                default=cls._MISS,
            )

            if cached_value is cls._MISS:
                cls._record_cache_event(
                    cls.EVENT_MISS,
                    operation=operation,
                    key=key,
                    authz_version=authz_version,
                )
                return default

            cls._record_cache_event(
                cls.EVENT_HIT,
                operation=operation,
                key=key,
                authz_version=authz_version,
            )
            return cached_value
        except Exception as exc:  # noqa
            cls._mark_unavailable(operation=operation, exc=exc)
            return default

    @classmethod
    def set(cls, key: Any, value: Any, *, ttl: int | None = None) -> bool:
        operation = "set"

        if not cls.enabled():
            cls._record_cache_bypass(
                operation=operation,
                key=key,
                reason="disabled",
            )
            return False

        if not cls.is_available():
            cls._record_cache_bypass(
                operation=operation,
                key=key,
                reason="unavailable",
            )
            return False

        authz_version = cls.get_authz_version()
        if authz_version is None:
            cls._record_cache_bypass(
                operation=operation,
                key=key,
                reason="authz_version_unavailable",
            )
            return False

        client = cls.get_client()
        if client is None:
            cls._record_cache_bypass(
                operation=operation,
                key=key,
                reason="client_unavailable",
                authz_version=authz_version,
            )
            return False

        resolved_ttl = cls._resolve_ttl(ttl, default_ttl=cls.cache_ttl_seconds())

        try:
            return client.set(
                cls._build_versioned_key(key, authz_version),
                value,
                ttl=resolved_ttl,
            )
        except Exception as exc:  # noqa
            cls._mark_unavailable(operation=operation, exc=exc)
            return False

    @classmethod
    def get_or_set(cls, key: Any, factory: Callable[[], T], *, ttl: int | None = None) -> T:
        operation = "get_or_set"

        if not cls.enabled():
            cls._record_cache_bypass(
                operation=operation,
                key=key,
                reason="disabled",
            )
            return factory()

        if not cls.is_available():
            cls._record_cache_bypass(
                operation=operation,
                key=key,
                reason="unavailable",
            )
            return factory()

        cached_value = cls.get(key, default=cls._MISS)
        if cached_value is not cls._MISS:
            return cached_value

        value = factory()
        cls.set(key, value, ttl=ttl)
        return value

    @classmethod
    async def aget(cls, key: Any, default: Any = None) -> Any:
        operation = "aget"

        if not cls.enabled():
            cls._record_cache_bypass(
                operation=operation,
                key=key,
                reason="disabled",
            )
            return default

        if not cls.is_available():
            cls._record_cache_bypass(
                operation=operation,
                key=key,
                reason="unavailable",
            )
            return default

        authz_version = await cls.aget_authz_version()
        if authz_version is None:
            cls._record_cache_bypass(
                operation=operation,
                key=key,
                reason="authz_version_unavailable",
            )
            return default

        client = cls.get_async_client()
        if client is None:
            cls._record_cache_bypass(
                operation=operation,
                key=key,
                reason="client_unavailable",
                authz_version=authz_version,
            )
            return default

        try:
            cache_key = cls._build_versioned_key(key, authz_version)
            cached_value = await client.get(
                cache_key,
                default=cls._MISS,
            )

            if cached_value is cls._MISS:
                cls._record_cache_event(
                    cls.EVENT_MISS,
                    operation=operation,
                    key=key,
                    authz_version=authz_version,
                )
                return default

            cls._record_cache_event(
                cls.EVENT_HIT,
                operation=operation,
                key=key,
                authz_version=authz_version,
            )
            return cached_value
        except Exception as exc:  # noqa
            cls._mark_unavailable(operation=operation, exc=exc)
            return default

    @classmethod
    async def aset(cls, key: Any, value: Any, *, ttl: int | None = None) -> bool:
        operation = "aset"

        if not cls.enabled():
            cls._record_cache_bypass(
                operation=operation,
                key=key,
                reason="disabled",
            )
            return False

        if not cls.is_available():
            cls._record_cache_bypass(
                operation=operation,
                key=key,
                reason="unavailable",
            )
            return False

        authz_version = await cls.aget_authz_version()
        if authz_version is None:
            cls._record_cache_bypass(
                operation=operation,
                key=key,
                reason="authz_version_unavailable",
            )
            return False

        client = cls.get_async_client()
        if client is None:
            cls._record_cache_bypass(
                operation=operation,
                key=key,
                reason="client_unavailable",
                authz_version=authz_version,
            )
            return False

        resolved_ttl = cls._resolve_ttl(ttl, default_ttl=cls.cache_ttl_seconds())

        try:
            return await client.set(
                cls._build_versioned_key(key, authz_version),
                value,
                ttl=resolved_ttl,
            )
        except Exception as exc:  # noqa
            cls._mark_unavailable(operation=operation, exc=exc)
            return False

    @classmethod
    async def aget_or_set(cls, key: Any, factory: Callable[[], T | Awaitable[T]], *, ttl: int | None = None) -> T:
        operation = "aget_or_set"

        if not cls.enabled():
            cls._record_cache_bypass(
                operation=operation,
                key=key,
                reason="disabled",
            )
            return await cls._resolve_async_factory(factory)

        if not cls.is_available():
            cls._record_cache_bypass(
                operation=operation,
                key=key,
                reason="unavailable",
            )
            return await cls._resolve_async_factory(factory)

        cached_value = await cls.aget(key, default=cls._MISS)
        if cached_value is not cls._MISS:
            return cached_value

        value = await cls._resolve_async_factory(factory)
        await cls.aset(key, value, ttl=ttl)
        return value

    @staticmethod
    def _resolve_ttl(ttl: int | None, *, default_ttl: int) -> int:
        if ttl is None:
            return max(int(default_ttl), 1)

        if isinstance(ttl, bool):
            return max(int(default_ttl), 1)

        try:
            return max(int(ttl), 1)
        except (TypeError, ValueError):
            return max(int(default_ttl), 1)

    @staticmethod
    async def _resolve_async_factory(factory: Callable[[], T | Awaitable[T]]) -> T:
        value = factory()
        if isawaitable(value):
            return await value

        return value
