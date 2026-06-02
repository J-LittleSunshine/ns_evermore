# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.core.cache import caches

from ns_backend.iam.repositories import AuthorizeRepository
from ns_backend.iam.schemas import UserAuthorizationContext
from ns_backend.iam.services.resource_access_filter import ResourceAccessFilterService

if TYPE_CHECKING:
    pass


class AuthorizationContextService:
    """Build and cache user authorization context for high-concurrency checks."""

    GLOBAL_VERSION_KEY = "iam:auth_context:global_version"
    USER_VERSION_KEY_PREFIX = "iam:auth_context:user_version"
    CONTEXT_KEY_PREFIX = "iam:auth_context:user"
    DEFAULT_TTL_SECONDS = 300

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

    @classmethod
    def _user_version_key(cls, user_id: int) -> str:
        return f"{cls.USER_VERSION_KEY_PREFIX}:{int(user_id)}"

    @classmethod
    def _context_cache_key(cls, *, user_id: int, version: int, resource_type: str, action_code: str) -> str:
        return f"{cls.CONTEXT_KEY_PREFIX}:{int(user_id)}:v{int(version)}:{resource_type}:{action_code}"

    @classmethod
    def _get_global_version(cls) -> int:
        cache = cls._cache()
        current = cache.get(cls.GLOBAL_VERSION_KEY)
        if current is None:
            cache.set(cls.GLOBAL_VERSION_KEY, 1, None)
            return 1
        try:
            return max(int(current), 1)
        except (TypeError, ValueError):
            cache.set(cls.GLOBAL_VERSION_KEY, 1, None)
            return 1

    @classmethod
    def _get_user_version(cls, *, user_id: int) -> int:
        cache = cls._cache()
        version_key = cls._user_version_key(user_id)
        current = cache.get(version_key)
        if current is None:
            current = cls._get_global_version()
            cache.set(version_key, current, None)
            return int(current)

        try:
            parsed = int(current)
        except (TypeError, ValueError):
            parsed = cls._get_global_version()
            cache.set(version_key, parsed, None)
        return max(parsed, 1)

    @staticmethod
    def _serialize(context: UserAuthorizationContext) -> dict[str, Any]:
        return {
            "user_id": context.user_id,
            "role_ids": list(context.role_ids),
            "readable_resource_ids": list(context.readable_resource_ids),
            "readable_resource_filters": dict(context.readable_resource_filters),
            "version": context.version,
        }

    @staticmethod
    def _deserialize(payload: dict[str, Any]) -> UserAuthorizationContext:
        return UserAuthorizationContext(
            user_id=int(payload.get("user_id")),
            role_ids=[int(item) for item in payload.get("role_ids", [])],
            readable_resource_ids=[str(item) for item in payload.get("readable_resource_ids", [])],
            readable_resource_filters=dict(payload.get("readable_resource_filters") or {}),
            version=max(int(payload.get("version") or 1), 1),
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
        user_id = int(getattr(user, "id"))
        version = cls._get_user_version(user_id=user_id)
        cache_key = cls._context_cache_key(
            user_id=user_id,
            version=version,
            resource_type=resource_type,
            action_code=action_code,
        )

        cache = cls._cache()
        cached_payload = cache.get(cache_key)
        if isinstance(cached_payload, dict):
            try:
                return cls._deserialize(cached_payload)
            except Exception:  # noqa
                cache.delete(cache_key)

        context = await cls.build_context(
            user=user,
            resource_type=resource_type,
            action_code=action_code,
            permission_code=permission_code,
            version=version,
        )
        cache.set(cache_key, cls._serialize(context), timeout=cls._ttl())
        return context

    @classmethod
    def invalidate_user(cls, user_id: int) -> int:
        """Invalidate one user's cached authorization context by version bump."""
        cache = cls._cache()
        version_key = cls._user_version_key(user_id)
        current = cls._get_user_version(user_id=user_id)
        next_version = current + 1
        cache.set(version_key, next_version, None)
        return next_version

    @classmethod
    def invalidate_all(cls) -> int:
        """Invalidate all cached authorization contexts by bumping global version."""
        cache = cls._cache()
        current = cls._get_global_version()
        next_version = current + 1
        cache.set(cls.GLOBAL_VERSION_KEY, next_version, None)
        return next_version

