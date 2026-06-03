# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import time
from collections import OrderedDict
from threading import RLock
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.core.cache import caches

from ns_backend.iam.constants import RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW
from ns_backend.iam.repositories import AuthorizeRepository
from ns_backend.iam.schemas import UserAuthorizationContext
from ns_backend.iam.services.backoff import retry_with_backoff
from ns_backend.iam.services.resource_access_filter import ResourceAccessFilterService
from ns_common.logger import get_ns_logger

if TYPE_CHECKING:
    pass

IAM_LOGGER = get_ns_logger("iam", True)


class AuthorizationContextService:
    """Build and cache user authorization context for high-concurrency checks."""

    GLOBAL_VERSION_KEY = "iam:auth_context:global_version"
    USER_VERSION_KEY_PREFIX = "iam:auth_context:user_version"
    CONTEXT_KEY_PREFIX = "iam:auth_context:user"
    DEFAULT_TTL_SECONDS = 300
    DEFAULT_AUTH_BACKOFF_ENABLED = True
    DEFAULT_AUTH_BACKOFF_MAX_RETRIES = 3
    DEFAULT_AUTH_BACKOFF_BASE_DELAY_MS = 50
    DEFAULT_AUTH_BACKOFF_MAX_DELAY_MS = 1000
    DEFAULT_AUTH_BACKOFF_JITTER_RATIO = 0.5
    DEFAULT_LOCAL_FALLBACK_CACHE_ENABLED = True
    DEFAULT_LOCAL_FALLBACK_CACHE_TTL_SECONDS = 3
    DEFAULT_LOCAL_FALLBACK_CACHE_MAX_SIZE = 1024
    DEFAULT_SINGLE_FLIGHT_ENABLED = True

    _LOCAL_CONTEXT_CACHE: OrderedDict[str, tuple[float, dict[str, Any]]] = OrderedDict()
    _LOCAL_CACHE_LOCK: RLock = RLock()
    _INFLIGHT_TASKS: dict[str, asyncio.Task[UserAuthorizationContext]] = {}
    _INFLIGHT_LOCK: RLock = RLock()

    @classmethod
    def _cache(cls):
        cache_alias = str(getattr(settings, "IAM_AUTH_CONTEXT_CACHE_ALIAS", "default") or "default")
        return caches[cache_alias]

    @classmethod
    def _ttl(cls) -> int:
        raw_value = getattr(settings, "IAM_AUTH_CONTEXT_TTL_SECONDS", cls.DEFAULT_TTL_SECONDS)
        try:
            parsed = int(raw_value)
        except (TypeError, ValueError):
            parsed = cls.DEFAULT_TTL_SECONDS
        return max(parsed, 30)

    @staticmethod
    def _coerce_non_negative_int(value: Any, default: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return max(parsed, 0)

    @staticmethod
    def _coerce_positive_int(value: Any, default: int) -> int:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return default
        return parsed if parsed > 0 else default

    @staticmethod
    def _coerce_float(value: Any, default: float, *, min_value: float, max_value: float) -> float:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            return default
        if parsed < min_value:
            return min_value
        if parsed > max_value:
            return max_value
        return parsed

    @classmethod
    def _backoff_enabled(cls) -> bool:
        return bool(getattr(settings, "IAM_AUTH_BACKOFF_ENABLED", cls.DEFAULT_AUTH_BACKOFF_ENABLED))

    @classmethod
    def _backoff_max_retries(cls) -> int:
        return cls._coerce_non_negative_int(
            getattr(settings, "IAM_AUTH_BACKOFF_MAX_RETRIES", cls.DEFAULT_AUTH_BACKOFF_MAX_RETRIES),
            cls.DEFAULT_AUTH_BACKOFF_MAX_RETRIES,
        )

    @classmethod
    def _backoff_base_delay_ms(cls) -> int:
        return cls._coerce_non_negative_int(
            getattr(settings, "IAM_AUTH_BACKOFF_BASE_DELAY_MS", cls.DEFAULT_AUTH_BACKOFF_BASE_DELAY_MS),
            cls.DEFAULT_AUTH_BACKOFF_BASE_DELAY_MS,
        )

    @classmethod
    def _backoff_max_delay_ms(cls) -> int:
        return cls._coerce_non_negative_int(
            getattr(settings, "IAM_AUTH_BACKOFF_MAX_DELAY_MS", cls.DEFAULT_AUTH_BACKOFF_MAX_DELAY_MS),
            cls.DEFAULT_AUTH_BACKOFF_MAX_DELAY_MS,
        )

    @classmethod
    def _backoff_jitter_ratio(cls) -> float:
        return cls._coerce_float(
            getattr(settings, "IAM_AUTH_BACKOFF_JITTER_RATIO", cls.DEFAULT_AUTH_BACKOFF_JITTER_RATIO),
            cls.DEFAULT_AUTH_BACKOFF_JITTER_RATIO,
            min_value=0.0,
            max_value=1.0,
        )

    @classmethod
    def _local_fallback_cache_enabled(cls) -> bool:
        return bool(getattr(settings, "IAM_AUTH_LOCAL_FALLBACK_CACHE_ENABLED", cls.DEFAULT_LOCAL_FALLBACK_CACHE_ENABLED))

    @classmethod
    def _local_fallback_cache_ttl_seconds(cls) -> int:
        return cls._coerce_positive_int(
            getattr(settings, "IAM_AUTH_LOCAL_FALLBACK_CACHE_TTL_SECONDS", cls.DEFAULT_LOCAL_FALLBACK_CACHE_TTL_SECONDS),
            cls.DEFAULT_LOCAL_FALLBACK_CACHE_TTL_SECONDS,
        )

    @classmethod
    def _local_fallback_cache_max_size(cls) -> int:
        return cls._coerce_positive_int(
            getattr(settings, "IAM_AUTH_LOCAL_FALLBACK_CACHE_MAX_SIZE", cls.DEFAULT_LOCAL_FALLBACK_CACHE_MAX_SIZE),
            cls.DEFAULT_LOCAL_FALLBACK_CACHE_MAX_SIZE,
        )

    @classmethod
    def _single_flight_enabled(cls) -> bool:
        return bool(getattr(settings, "IAM_AUTH_SINGLE_FLIGHT_ENABLED", cls.DEFAULT_SINGLE_FLIGHT_ENABLED))

    @classmethod
    def _safe_cache_get(cls, key: str, default: Any = None) -> Any:
        try:
            return cls._cache().get(key, default)
        except Exception as exc:  # noqa
            IAM_LOGGER.warning(
                "authorization context cache get failed | cache_key=%s exception_class=%s",
                key,
                exc.__class__.__name__,
            )
            return default

    @classmethod
    def _safe_cache_set(cls, key: str, value: Any, timeout: int | None) -> bool:
        try:
            cls._cache().set(key, value, timeout=timeout)
            return True
        except Exception as exc:  # noqa
            IAM_LOGGER.warning(
                "authorization context cache set failed | cache_key=%s exception_class=%s",
                key,
                exc.__class__.__name__,
            )
            return False

    @classmethod
    def _safe_cache_delete(cls, key: str) -> bool:
        try:
            cls._cache().delete(key)
            return True
        except Exception as exc:  # noqa
            IAM_LOGGER.warning(
                "authorization context cache delete failed | cache_key=%s exception_class=%s",
                key,
                exc.__class__.__name__,
            )
            return False

    @classmethod
    def _user_version_key(cls, user_id: int) -> str:
        return f"{cls.USER_VERSION_KEY_PREFIX}:{int(user_id)}"

    @classmethod
    def _context_cache_key(cls, *, user_id: int, version: int, resource_type: str, action_code: str, permission_code: str | None) -> str:
        permission_part = str(permission_code or "_").strip().lower() or "_"
        return f"{cls.CONTEXT_KEY_PREFIX}:{int(user_id)}:v{int(version)}:{resource_type}:{action_code}:{permission_part}"

    @classmethod
    def _prune_local_cache_unlocked(cls, *, now_monotonic: float) -> None:
        while cls._LOCAL_CONTEXT_CACHE:
            first_key = next(iter(cls._LOCAL_CONTEXT_CACHE.keys()))
            expires_at, _ = cls._LOCAL_CONTEXT_CACHE[first_key]
            if expires_at > now_monotonic:
                break
            cls._LOCAL_CONTEXT_CACHE.pop(first_key, None)

        max_size = cls._local_fallback_cache_max_size()
        while len(cls._LOCAL_CONTEXT_CACHE) > max_size:
            cls._LOCAL_CONTEXT_CACHE.popitem(last=False)

    @classmethod
    def _get_local_cache_payload(cls, cache_key: str) -> dict[str, Any] | None:
        if not cls._local_fallback_cache_enabled():
            return None

        now_monotonic = time.monotonic()
        with cls._LOCAL_CACHE_LOCK:
            cls._prune_local_cache_unlocked(now_monotonic=now_monotonic)
            entry = cls._LOCAL_CONTEXT_CACHE.get(cache_key)
            if entry is None:
                return None

            expires_at, payload = entry
            if expires_at <= now_monotonic:
                cls._LOCAL_CONTEXT_CACHE.pop(cache_key, None)
                return None

            cls._LOCAL_CONTEXT_CACHE.move_to_end(cache_key)

        IAM_LOGGER.debug("authorization context local cache hit | cache_key=%s", cache_key)
        return dict(payload)

    @classmethod
    def _set_local_cache_payload(cls, cache_key: str, payload: dict[str, Any]) -> None:
        if not cls._local_fallback_cache_enabled():
            return

        ttl_seconds = cls._local_fallback_cache_ttl_seconds()
        now_monotonic = time.monotonic()
        expires_at = now_monotonic + ttl_seconds
        with cls._LOCAL_CACHE_LOCK:
            cls._LOCAL_CONTEXT_CACHE[cache_key] = (expires_at, dict(payload))
            cls._LOCAL_CONTEXT_CACHE.move_to_end(cache_key)
            cls._prune_local_cache_unlocked(now_monotonic=now_monotonic)

    @classmethod
    def _clear_local_cache_for_user(cls, user_id: int) -> None:
        key_prefix = f"{cls.CONTEXT_KEY_PREFIX}:{int(user_id)}:"
        with cls._LOCAL_CACHE_LOCK:
            for cache_key in list(cls._LOCAL_CONTEXT_CACHE.keys()):
                if cache_key.startswith(key_prefix):
                    cls._LOCAL_CONTEXT_CACHE.pop(cache_key, None)

    @classmethod
    def _clear_local_cache_all(cls) -> None:
        with cls._LOCAL_CACHE_LOCK:
            cls._LOCAL_CONTEXT_CACHE.clear()

    @classmethod
    async def _run_with_single_flight(cls, *, cache_key: str, operation) -> UserAuthorizationContext:
        if not cls._single_flight_enabled():
            return await operation()

        owner = False
        with cls._INFLIGHT_LOCK:
            inflight = cls._INFLIGHT_TASKS.get(cache_key)
            if inflight is None:
                inflight = asyncio.create_task(operation())
                cls._INFLIGHT_TASKS[cache_key] = inflight
                owner = True
            else:
                IAM_LOGGER.debug("authorization context single-flight wait | cache_key=%s", cache_key)

        try:
            return await inflight
        finally:
            if owner:
                with cls._INFLIGHT_LOCK:
                    cls._INFLIGHT_TASKS.pop(cache_key, None)

    @classmethod
    async def _build_context_with_backoff(
        cls,
        *,
        user: Any,
        resource_type: str,
        action_code: str,
        permission_code: str | None,
        version: int,
    ) -> tuple[UserAuthorizationContext, int]:
        attempt_count = 0

        async def _operation() -> UserAuthorizationContext:
            nonlocal attempt_count
            attempt_count += 1
            return await cls._build_context_once(
                user=user,
                resource_type=resource_type,
                action_code=action_code,
                permission_code=permission_code,
                version=version,
            )

        if cls._backoff_enabled():
            context = await retry_with_backoff(
                _operation,
                max_retries=cls._backoff_max_retries(),
                base_delay_ms=cls._backoff_base_delay_ms(),
                max_delay_ms=cls._backoff_max_delay_ms(),
                jitter_ratio=cls._backoff_jitter_ratio(),
                retryable_exceptions=(Exception,),
                logger_name="iam",
                operation_name="authorization_context_build",
            )
        else:
            context = await _operation()

        return context, max(attempt_count - 1, 0)

    @classmethod
    def _build_deny_context(cls, *, user_id: int, version: int, reason: str) -> UserAuthorizationContext:
        return UserAuthorizationContext(
            user_id=user_id,
            role_ids=[],
            readable_resource_ids=[],
            readable_resource_filters={
                "deny_all": True,
                "allow_all": False,
                "default_allow": False,
                "access_mode": RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW,
                "reason": reason,
                "orm": {"include": {"resource_id__in": []}, "exclude": {}},
                "vector": {"must": {"terms": {"resource_id": []}}, "must_not": {}},
                "data_scope": {},
            },
            access_mode=RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW,
            version=max(int(version), 1),
        )

    @classmethod
    def _get_global_version(cls) -> int:
        current = cls._safe_cache_get(cls.GLOBAL_VERSION_KEY)
        if current is None:
            cls._safe_cache_set(cls.GLOBAL_VERSION_KEY, 1, None)
            return 1
        try:
            return max(int(current), 1)
        except (TypeError, ValueError):
            cls._safe_cache_set(cls.GLOBAL_VERSION_KEY, 1, None)
            return 1

    @classmethod
    def _get_user_version(cls, *, user_id: int) -> int:
        version_key = cls._user_version_key(user_id)
        current = cls._safe_cache_get(version_key)
        if current is None:
            current = cls._get_global_version()
            cls._safe_cache_set(version_key, current, None)
            return int(current)

        try:
            parsed = int(current)
        except (TypeError, ValueError):
            parsed = cls._get_global_version()
            cls._safe_cache_set(version_key, parsed, None)
        return max(parsed, 1)

    @staticmethod
    def _serialize(context: UserAuthorizationContext) -> dict[str, Any]:
        return {
            "user_id": context.user_id,
            "role_ids": list(context.role_ids),
            "readable_resource_ids": list(context.readable_resource_ids),
            "readable_resource_filters": dict(context.readable_resource_filters),
            "access_mode": context.access_mode,
            "version": context.version,
        }

    @staticmethod
    def _deserialize(payload: dict[str, Any]) -> UserAuthorizationContext:
        return UserAuthorizationContext(
            user_id=int(payload.get("user_id")),
            role_ids=[int(item) for item in payload.get("role_ids", [])],
            readable_resource_ids=[str(item) for item in payload.get("readable_resource_ids", [])],
            readable_resource_filters=dict(payload.get("readable_resource_filters") or {}),
            access_mode=str(payload.get("access_mode") or RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW),
            version=max(int(payload.get("version") or 1), 1),
        )

    @classmethod
    async def _build_context_once(
        cls,
        *,
        user: Any,
        resource_type: str,
        action_code: str,
        permission_code: str | None,
        version: int,
    ) -> UserAuthorizationContext:
        """Build one fresh authorization context from repository/service sources."""
        user_id = int(getattr(user, "id"))
        role_ids = await AuthorizeRepository.list_active_role_ids_for_user(user_id=user_id)
        retrieval_filter = await ResourceAccessFilterService.resolve_retrieval_filter(
            user=user,
            resource_type=resource_type,
            action_code=action_code,
            permission_code=permission_code,
        )

        return UserAuthorizationContext(
            user_id=user_id,
            role_ids=role_ids,
            readable_resource_ids=[str(item) for item in retrieval_filter.get("allowed_resource_ids", [])],
            readable_resource_filters=dict(retrieval_filter.get("filters") or {}),
            access_mode=str(retrieval_filter.get("access_mode") or RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW),
            version=version,
        )

    @classmethod
    async def build_context(
        cls,
        *,
        user: Any,
        resource_type: str,
        action_code: str,
        permission_code: str | None,
        version: int,
    ) -> UserAuthorizationContext:
        """Build one fresh authorization context from repository/service sources."""
        return await cls._build_context_once(
            user=user,
            resource_type=resource_type,
            action_code=action_code,
            permission_code=permission_code,
            version=version,
        )

    @classmethod
    async def get_or_build(
        cls,
        *,
        user: Any,
        resource_type: str,
        action_code: str,
        permission_code: str | None = None,
    ) -> UserAuthorizationContext:
        """Get authorization context from cache, or build and cache it."""
        if user is None or not bool(getattr(user, "is_active", False)):
            user_id = cls._coerce_non_negative_int(getattr(user, "id", 0), 0)
            return cls._build_deny_context(user_id=user_id, version=1, reason="USER_INACTIVE")

        user_id = int(getattr(user, "id"))
        version = cls._get_user_version(user_id=user_id)
        cache_key = cls._context_cache_key(
            user_id=user_id,
            version=version,
            resource_type=resource_type,
            action_code=action_code,
            permission_code=permission_code,
        )

        cached_payload = cls._safe_cache_get(cache_key)
        if isinstance(cached_payload, dict):
            try:
                return cls._deserialize(cached_payload)
            except Exception:  # noqa
                cls._safe_cache_delete(cache_key)

        local_payload = cls._get_local_cache_payload(cache_key)
        if isinstance(local_payload, dict):
            try:
                return cls._deserialize(local_payload)
            except Exception:  # noqa
                pass

        async def _build_and_cache() -> UserAuthorizationContext:
            context, retry_count = await cls._build_context_with_backoff(
                user=user,
                resource_type=resource_type,
                action_code=action_code,
                permission_code=permission_code,
                version=version,
            )
            serialized = cls._serialize(context)
            cls._safe_cache_set(cache_key, serialized, timeout=cls._ttl())
            cls._set_local_cache_payload(cache_key, serialized)
            if retry_count > 0:
                IAM_LOGGER.debug(
                    "authorization context build retried | user_id=%s resource_type=%s action_code=%s retry_count=%s",
                    user_id,
                    resource_type,
                    action_code,
                    retry_count,
                )
            return context

        try:
            return await cls._run_with_single_flight(cache_key=cache_key, operation=_build_and_cache)
        except Exception as exc:  # noqa
            IAM_LOGGER.error(
                "authorization context build failed | user_id=%s resource_type=%s action_code=%s exception_class=%s",
                user_id,
                resource_type,
                action_code,
                exc.__class__.__name__,
                exc_info=True,
            )
            deny_context = cls._build_deny_context(user_id=user_id, version=version, reason="AUTH_CONTEXT_BUILD_FAILED")
            cls._set_local_cache_payload(cache_key, cls._serialize(deny_context))
            return deny_context

    @classmethod
    def invalidate_user(cls, user_id: int) -> int:
        """Invalidate one user's cached authorization context by version bump."""
        version_key = cls._user_version_key(user_id)
        current = cls._get_user_version(user_id=user_id)
        next_version = current + 1
        cls._safe_cache_set(version_key, next_version, None)
        cls._clear_local_cache_for_user(user_id)
        return next_version

    @classmethod
    def invalidate_all(cls) -> int:
        """Invalidate all cached authorization contexts by bumping global version."""
        current = cls._get_global_version()
        next_version = current + 1
        cls._safe_cache_set(cls.GLOBAL_VERSION_KEY, next_version, None)
        cls._clear_local_cache_all()
        return next_version

