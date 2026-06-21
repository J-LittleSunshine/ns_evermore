# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import django
from django.conf import settings as django_settings

if not django_settings.configured:
    django_settings.configure(
        SECRET_KEY="test-secret-key",
        INSTALLED_APPS=[
            "django.contrib.contenttypes",
            "ns_backend.iam.apps.IamConfig",
        ],
        DATABASES={
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": ":memory:",
            }
        },
        DEFAULT_AUTO_FIELD="django.db.models.BigAutoField",
        IAM_AUTH_BACKOFF_ENABLED=True,
        IAM_AUTH_BACKOFF_MAX_RETRIES=3,
        IAM_AUTH_BACKOFF_BASE_DELAY_MS=0,
        IAM_AUTH_BACKOFF_MAX_DELAY_MS=1,
        IAM_AUTH_BACKOFF_JITTER_RATIO=0.0,
        IAM_AUTH_CONTEXT_CACHE_ALIAS="default",
        IAM_AUTH_CONTEXT_TTL_SECONDS=300,
        IAM_AUTH_LOCAL_FALLBACK_CACHE_ENABLED=True,
        IAM_AUTH_LOCAL_FALLBACK_CACHE_TTL_SECONDS=3,
        IAM_AUTH_LOCAL_FALLBACK_CACHE_MAX_SIZE=1024,
        IAM_AUTH_SINGLE_FLIGHT_ENABLED=True,
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.locmem.LocMemCache"
            }
        },
        USE_TZ=True,
        TIME_ZONE="UTC",
    )

django.setup()

from ns_backend.iam.constants import (
    RESOURCE_ACCESS_MODE_ACL_REQUIRED,
    RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW,
)
from ns_backend.iam.schemas import DataScopeFilterPlan, UserAuthorizationContext
from ns_backend.iam.services.authorize import AuthorizeService
from ns_backend.iam.services.authorization_context import AuthorizationContextService
from ns_backend.iam.services.resource_access_filter import ResourceAccessFilterService
from ns_backend.iam.services.resource_acl import ResourceAclService


def _build_user(*, user_id: int = 1, is_active: bool = True, is_superuser: bool = False) -> SimpleNamespace:
    return SimpleNamespace(
        id=user_id,
        is_active=is_active,
        is_superuser=is_superuser,
        department_id=None,
        company_id=None,
        subsidiary_id=None,
        user_type="PERSONAL",
    )


class AccessModeServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_rbac_default_allow_rbac_allow_without_acl(self) -> None:
        user = _build_user()

        with (
            patch("ns_backend.iam.services.authorize.ResourceRepository.has_action_for_resource_type", new=AsyncMock(return_value=True)),
            patch("ns_backend.iam.services.authorize.ResourceRepository.get_resource_access_mode", new=AsyncMock(return_value=RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW)),
            patch("ns_backend.iam.services.authorize.AuthorizeRepository.list_active_role_ids_for_user", new=AsyncMock(return_value=[])),
            patch("ns_backend.iam.services.authorize.ResourceAclService.resolve_acl_effect", new=AsyncMock(return_value=None)),
            patch("ns_backend.iam.services.authorize.PolicyEngineService.evaluate", new=AsyncMock(return_value=None)),
            patch("ns_backend.iam.services.authorize.PermissionService.has_permission", new=AsyncMock(return_value=True)),
            patch("ns_backend.iam.services.authorize.DataScopeService.resolve_filter_plan", new=AsyncMock(return_value=DataScopeFilterPlan(allowed=True, filters={}))),
            patch("ns_backend.iam.services.authorize.DecisionAuditService.record_decision_safe", new=AsyncMock(return_value=None)),
        ):
            decision = await AuthorizeService.check(
                user=user,
                data={
                    "resource_type": "knowledge.chunk",
                    "resource_id": "chunk-1",
                    "action_code": "read",
                    "permission_code": "knowledge:chunk:read",
                },
            )

        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["matched_source"], AuthorizeService.MATCHED_SOURCE_RBAC)
        self.assertEqual(decision["access_mode"], RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW)

        with (
            patch("ns_backend.iam.services.resource_access_filter.ResourceRepository.get_resource_by_type", new=AsyncMock(return_value=SimpleNamespace(access_mode=RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW))),
            patch("ns_backend.iam.services.resource_access_filter.AuthorizeRepository.list_active_role_ids_for_user", new=AsyncMock(return_value=[])),
            patch("ns_backend.iam.services.resource_access_filter.ResourceAclRepository.list_active_effects_for_resource_type_action", new=AsyncMock(return_value=[])),
            patch("ns_backend.iam.services.resource_access_filter.ResourceRelationRepository.list_ancestor_resource_types", new=AsyncMock(return_value=[])),
            patch("ns_backend.iam.services.resource_access_filter.PermissionService.has_permission", new=AsyncMock(return_value=True)),
            patch("ns_backend.iam.services.resource_access_filter.DataScopeService.resolve_filter_plan", new=AsyncMock(return_value=DataScopeFilterPlan(allowed=True, filters={}))),
        ):
            result = await ResourceAccessFilterService.resolve_retrieval_filter(
                user=user,
                resource_type="knowledge.chunk",
                action_code="read",
                permission_code="knowledge:chunk:read",
            )

        self.assertTrue(result["filters"]["default_allow"])
        self.assertFalse(result["filters"]["deny_all"])

    async def test_rbac_default_allow_with_acl_deny(self) -> None:
        user = _build_user()

        with (
            patch("ns_backend.iam.services.authorize.ResourceRepository.has_action_for_resource_type", new=AsyncMock(return_value=True)),
            patch("ns_backend.iam.services.authorize.ResourceRepository.get_resource_access_mode", new=AsyncMock(return_value=RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW)),
            patch("ns_backend.iam.services.authorize.AuthorizeRepository.list_active_role_ids_for_user", new=AsyncMock(return_value=[])),
            patch(
                "ns_backend.iam.services.authorize.ResourceAclService.resolve_acl_effect",
                new=AsyncMock(
                    return_value={
                        "effect": "DENY",
                        "matched_acl_id": 11,
                        "matched_source": "acl:self",
                        "reason": "ACL_DENY",
                    }
                ),
            ),
            patch("ns_backend.iam.services.authorize.PolicyEngineService.evaluate", new=AsyncMock(return_value=None)),
            patch("ns_backend.iam.services.authorize.DecisionAuditService.record_decision_safe", new=AsyncMock(return_value=None)),
        ):
            decision = await AuthorizeService.check(
                user=user,
                data={
                    "resource_type": "knowledge.chunk",
                    "resource_id": "chunk-1",
                    "action_code": "read",
                    "permission_code": "knowledge:chunk:read",
                },
            )

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason"], "ACL_DENY")

        with (
            patch("ns_backend.iam.services.resource_access_filter.ResourceRepository.get_resource_by_type", new=AsyncMock(return_value=SimpleNamespace(access_mode=RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW))),
            patch("ns_backend.iam.services.resource_access_filter.AuthorizeRepository.list_active_role_ids_for_user", new=AsyncMock(return_value=[])),
            patch(
                "ns_backend.iam.services.resource_access_filter.ResourceAclRepository.list_active_effects_for_resource_type_action",
                new=AsyncMock(
                    return_value=[
                        {
                            "resource_id": "chunk-1",
                            "effect": "DENY"
                        }
                    ]
                ),
            ),
            patch("ns_backend.iam.services.resource_access_filter.ResourceRelationRepository.list_ancestor_resource_types", new=AsyncMock(return_value=[])),
            patch("ns_backend.iam.services.resource_access_filter.PermissionService.has_permission", new=AsyncMock(return_value=True)),
            patch("ns_backend.iam.services.resource_access_filter.DataScopeService.resolve_filter_plan", new=AsyncMock(return_value=DataScopeFilterPlan(allowed=True, filters={}))),
        ):
            result = await ResourceAccessFilterService.resolve_retrieval_filter(
                user=user,
                resource_type="knowledge.chunk",
                action_code="read",
                permission_code="knowledge:chunk:read",
            )

        self.assertIn("chunk-1", result["denied_resource_ids"])
        self.assertIn("chunk-1", result["filters"]["orm"]["exclude"]["resource_id__in"])
        self.assertIn("chunk-1", result["filters"]["vector"]["must_not"]["terms"]["resource_id"])

    async def test_acl_required_rbac_allow_without_acl(self) -> None:
        user = _build_user()

        with (
            patch("ns_backend.iam.services.authorize.ResourceRepository.has_action_for_resource_type", new=AsyncMock(return_value=True)),
            patch("ns_backend.iam.services.authorize.ResourceRepository.get_resource_access_mode", new=AsyncMock(return_value=RESOURCE_ACCESS_MODE_ACL_REQUIRED)),
            patch("ns_backend.iam.services.authorize.AuthorizeRepository.list_active_role_ids_for_user", new=AsyncMock(return_value=[])),
            patch("ns_backend.iam.services.authorize.ResourceAclService.resolve_acl_effect", new=AsyncMock(return_value=None)),
            patch("ns_backend.iam.services.authorize.PolicyEngineService.evaluate", new=AsyncMock(return_value=None)),
            patch("ns_backend.iam.services.authorize.PermissionService.has_permission", new=AsyncMock(return_value=True)),
            patch("ns_backend.iam.services.authorize.DecisionAuditService.record_decision_safe", new=AsyncMock(return_value=None)),
        ):
            decision = await AuthorizeService.check(
                user=user,
                data={
                    "resource_type": "knowledge.chunk",
                    "resource_id": "chunk-1",
                    "action_code": "read",
                    "permission_code": "knowledge:chunk:read",
                },
            )

        self.assertFalse(decision["allowed"])
        self.assertEqual(decision["reason"], "ACL_REQUIRED_NO_RESOURCE_ALLOW")
        self.assertTrue(any(item.get("reason") == "RBAC_ALLOW_BLOCKED_BY_ACL_REQUIRED" for item in decision["decision_chain"]))

        with (
            patch("ns_backend.iam.services.resource_access_filter.ResourceRepository.get_resource_by_type", new=AsyncMock(return_value=SimpleNamespace(access_mode=RESOURCE_ACCESS_MODE_ACL_REQUIRED))),
            patch("ns_backend.iam.services.resource_access_filter.AuthorizeRepository.list_active_role_ids_for_user", new=AsyncMock(return_value=[])),
            patch("ns_backend.iam.services.resource_access_filter.ResourceAclRepository.list_active_effects_for_resource_type_action", new=AsyncMock(return_value=[])),
            patch("ns_backend.iam.services.resource_access_filter.ResourceRelationRepository.list_ancestor_resource_types", new=AsyncMock(return_value=[])),
            patch("ns_backend.iam.services.resource_access_filter.PermissionService.has_permission", new=AsyncMock(return_value=True)),
            patch("ns_backend.iam.services.resource_access_filter.DataScopeService.resolve_filter_plan", new=AsyncMock(return_value=DataScopeFilterPlan(allowed=True, filters={}))),
        ):
            result = await ResourceAccessFilterService.resolve_retrieval_filter(
                user=user,
                resource_type="knowledge.chunk",
                action_code="read",
                permission_code="knowledge:chunk:read",
            )

        self.assertTrue(result["filters"]["deny_all"])
        self.assertFalse(result["filters"]["default_allow"])
        self.assertEqual(result["access_mode"], RESOURCE_ACCESS_MODE_ACL_REQUIRED)

    async def test_acl_required_acl_allow(self) -> None:
        user = _build_user()

        with (
            patch("ns_backend.iam.services.authorize.ResourceRepository.has_action_for_resource_type", new=AsyncMock(return_value=True)),
            patch("ns_backend.iam.services.authorize.ResourceRepository.get_resource_access_mode", new=AsyncMock(return_value=RESOURCE_ACCESS_MODE_ACL_REQUIRED)),
            patch("ns_backend.iam.services.authorize.AuthorizeRepository.list_active_role_ids_for_user", new=AsyncMock(return_value=[])),
            patch(
                "ns_backend.iam.services.authorize.ResourceAclService.resolve_acl_effect",
                new=AsyncMock(
                    return_value={
                        "effect": "ALLOW",
                        "matched_acl_id": 12,
                        "matched_source": "acl:self",
                        "matched_acl_depth": 0,
                        "reason": "ACL_ALLOW",
                    }
                ),
            ),
            patch("ns_backend.iam.services.authorize.PolicyEngineService.evaluate", new=AsyncMock(return_value=None)),
            patch("ns_backend.iam.services.authorize.DataScopeService.resolve_filter_plan", new=AsyncMock(return_value=DataScopeFilterPlan(allowed=True, filters={}))),
            patch("ns_backend.iam.services.authorize.DecisionAuditService.record_decision_safe", new=AsyncMock(return_value=None)),
        ):
            decision = await AuthorizeService.check(
                user=user,
                data={
                    "resource_type": "knowledge.chunk",
                    "resource_id": "chunk-1",
                    "action_code": "read",
                    "permission_code": "knowledge:chunk:read",
                },
            )

        self.assertTrue(decision["allowed"])
        self.assertEqual(decision["matched_source"], AuthorizeService.MATCHED_SOURCE_ACL)

        with (
            patch("ns_backend.iam.services.resource_access_filter.ResourceRepository.get_resource_by_type", new=AsyncMock(return_value=SimpleNamespace(access_mode=RESOURCE_ACCESS_MODE_ACL_REQUIRED))),
            patch("ns_backend.iam.services.resource_access_filter.AuthorizeRepository.list_active_role_ids_for_user", new=AsyncMock(return_value=[])),
            patch(
                "ns_backend.iam.services.resource_access_filter.ResourceAclRepository.list_active_effects_for_resource_type_action",
                new=AsyncMock(
                    return_value=[
                        {
                            "resource_id": "chunk-1",
                            "effect": "ALLOW"
                        }
                    ]
                ),
            ),
            patch("ns_backend.iam.services.resource_access_filter.ResourceRelationRepository.list_ancestor_resource_types", new=AsyncMock(return_value=[])),
            patch("ns_backend.iam.services.resource_access_filter.PermissionService.has_permission", new=AsyncMock(return_value=False)),
            patch("ns_backend.iam.services.resource_access_filter.DataScopeService.resolve_filter_plan", new=AsyncMock(return_value=DataScopeFilterPlan(allowed=True, filters={}))),
        ):
            result = await ResourceAccessFilterService.resolve_retrieval_filter(
                user=user,
                resource_type="knowledge.chunk",
                action_code="read",
                permission_code="knowledge:chunk:read",
            )

        self.assertIn("chunk-1", result["allowed_resource_ids"])

    async def test_acl_required_parent_allow_child_inherited(self) -> None:
        with (
            patch(
                "ns_backend.iam.services.resource_acl.ResourceRelationRepository.list_ancestor_chain",
                new=AsyncMock(
                    return_value=[
                        {
                            "resource_type": "knowledge.chunk",
                            "resource_id": "chunk-1",
                            "depth": 0
                        },
                        {
                            "resource_type": "knowledge.document",
                            "resource_id": "doc-1",
                            "depth": 1
                        },
                    ]
                ),
            ),
            patch(
                "ns_backend.iam.services.resource_acl.ResourceAclRepository.list_active_effects_for_resources",
                new=AsyncMock(
                    return_value=[
                        {
                            "id": 100,
                            "resource_type": "knowledge.document",
                            "resource_id": "doc-1",
                            "effect": "ALLOW",
                        }
                    ]
                ),
            ),
        ):
            result = await ResourceAclService.resolve_acl_effect(
                subject_bindings=[
                    (
                        "USER",
                        1
                    )
                ],
                resource_type="knowledge.chunk",
                resource_id="chunk-1",
                action_code="read",
            )

        self.assertIsNotNone(result)
        self.assertEqual(result["effect"], ResourceAclService.EFFECT_ALLOW)
        self.assertGreater(int(result.get("matched_acl_depth") or 0), 0)

    async def test_acl_required_parent_deny_overrides_child_allow(self) -> None:
        with (
            patch(
                "ns_backend.iam.services.resource_acl.ResourceRelationRepository.list_ancestor_chain",
                new=AsyncMock(
                    return_value=[
                        {
                            "resource_type": "knowledge.chunk",
                            "resource_id": "chunk-1",
                            "depth": 0
                        },
                        {
                            "resource_type": "knowledge.document",
                            "resource_id": "doc-1",
                            "depth": 1
                        },
                    ]
                ),
            ),
            patch(
                "ns_backend.iam.services.resource_acl.ResourceAclRepository.list_active_effects_for_resources",
                new=AsyncMock(
                    return_value=[
                        {
                            "id": 200,
                            "resource_type": "knowledge.chunk",
                            "resource_id": "chunk-1",
                            "effect": "ALLOW",
                        },
                        {
                            "id": 201,
                            "resource_type": "knowledge.document",
                            "resource_id": "doc-1",
                            "effect": "DENY",
                        },
                    ]
                ),
            ),
        ):
            result = await ResourceAclService.resolve_acl_effect(
                subject_bindings=[
                    (
                        "USER",
                        1
                    )
                ],
                resource_type="knowledge.chunk",
                resource_id="chunk-1",
                action_code="read",
            )

        self.assertIsNotNone(result)
        self.assertEqual(result["effect"], ResourceAclService.EFFECT_DENY)


class BackoffFallbackTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        AuthorizationContextService._clear_local_cache_all()
        with AuthorizationContextService._INFLIGHT_LOCK:
            AuthorizationContextService._INFLIGHT_TASKS.clear()

    async def test_cache_get_exception_fallback_build(self) -> None:
        class _BrokenGetCache:
            def get(self, *_args, **_kwargs):
                raise RuntimeError("cache get failed")

            def set(self, *_args, **_kwargs):
                return None

            def delete(self, *_args, **_kwargs):
                return None

        user = _build_user()
        built_context = UserAuthorizationContext(
            user_id=1, role_ids=[], readable_resource_ids=[
                "chunk-1"
            ], readable_resource_filters={}, version=1
        )

        with (
            patch("ns_backend.iam.services.authorization_context.AuthorizationContextService._cache", return_value=_BrokenGetCache()),
            patch(
                "ns_backend.iam.services.authorization_context.AuthorizationContextService._build_context_with_backoff", new=AsyncMock(
                    return_value=(
                            built_context,
                            0
                    )
                )
            ) as build_mock,
            patch("ns_backend.iam.services.authorization_context.IAM_LOGGER.warning") as warning_mock,
        ):
            result = await AuthorizationContextService.get_or_build(
                user=user,
                resource_type="knowledge.chunk",
                action_code="read",
                permission_code="knowledge:chunk:read",
            )

        self.assertEqual(result.user_id, 1)
        self.assertEqual(build_mock.await_count, 1)
        self.assertGreaterEqual(warning_mock.call_count, 1)

    async def test_cache_set_exception_does_not_break_main_flow(self) -> None:
        class _BrokenSetCache:
            def get(self, *_args, **_kwargs):
                return None

            def set(self, *_args, **_kwargs):
                raise RuntimeError("cache set failed")

            def delete(self, *_args, **_kwargs):
                return None

        user = _build_user()
        built_context = UserAuthorizationContext(
            user_id=1, role_ids=[], readable_resource_ids=[
                "chunk-1"
            ], readable_resource_filters={}, version=1
        )

        with (
            patch("ns_backend.iam.services.authorization_context.AuthorizationContextService._cache", return_value=_BrokenSetCache()),
            patch(
                "ns_backend.iam.services.authorization_context.AuthorizationContextService._build_context_with_backoff", new=AsyncMock(
                    return_value=(
                            built_context,
                            0
                    )
                )
            ) as build_mock,
            patch("ns_backend.iam.services.authorization_context.IAM_LOGGER.warning") as warning_mock,
        ):
            result = await AuthorizationContextService.get_or_build(
                user=user,
                resource_type="knowledge.chunk",
                action_code="read",
                permission_code="knowledge:chunk:read",
            )

        self.assertEqual(result.user_id, 1)
        self.assertEqual(build_mock.await_count, 1)
        self.assertGreaterEqual(warning_mock.call_count, 1)

    async def test_retry_success_after_one_failure(self) -> None:
        user = _build_user()
        success_payload = {
            "access_mode": RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW,
            "allowed_resource_ids": [],
            "denied_resource_ids": [],
            "filters": {
                "deny_all": False,
                "allow_all": False,
                "default_allow": True,
                "access_mode": RESOURCE_ACCESS_MODE_RBAC_DEFAULT_ALLOW,
                "reason": "RBAC_DEFAULT_ALLOW",
                "orm": {
                    "include": {},
                    "exclude": {}
                },
                "vector": {
                    "must": {},
                    "must_not": {}
                },
                "data_scope": {},
            },
        }

        with patch(
                "ns_backend.iam.services.resource_access_filter.ResourceAccessFilterService._resolve_retrieval_filter_once",
                new=AsyncMock(
                    side_effect=[
                        RuntimeError("temporary failure"),
                        success_payload
                    ]
                ),
        ):
            result = await ResourceAccessFilterService.resolve_retrieval_filter(
                user=user,
                resource_type="knowledge.chunk",
                action_code="read",
                permission_code="knowledge:chunk:read",
            )

        self.assertGreaterEqual(int(result.get("retry_count") or 0), 1)
        self.assertFalse(result["filters"]["deny_all"])

    async def test_retry_exhausted_returns_safe_deny(self) -> None:
        user = _build_user()

        with patch(
                "ns_backend.iam.services.resource_access_filter.ResourceAccessFilterService._resolve_retrieval_filter_once",
                new=AsyncMock(side_effect=RuntimeError("db unavailable")),
        ):
            result = await ResourceAccessFilterService.resolve_retrieval_filter(
                user=user,
                resource_type="knowledge.chunk",
                action_code="read",
                permission_code="knowledge:chunk:read",
            )

        self.assertTrue(result["filters"]["deny_all"])
        self.assertFalse(result["filters"]["default_allow"])
        self.assertEqual(result["filters"]["reason"], "AUTH_FILTER_BUILD_FAILED")

    async def test_single_flight_merges_same_key_concurrency(self) -> None:
        user = _build_user()
        call_count = 0

        async def _build_once(*_args, **_kwargs):
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return (
                UserAuthorizationContext(
                    user_id=1,
                    role_ids=[],
                    readable_resource_ids=[
                        "chunk-1"
                    ],
                    readable_resource_filters={},
                    version=1,
                ),
                0,
            )

        with (
            patch("ns_backend.iam.services.authorization_context.AuthorizationContextService._safe_cache_get", return_value=None),
            patch("ns_backend.iam.services.authorization_context.AuthorizationContextService._safe_cache_set", return_value=False),
            patch("ns_backend.iam.services.authorization_context.AuthorizationContextService._get_user_version", return_value=1),
            patch("ns_backend.iam.services.authorization_context.AuthorizationContextService._build_context_with_backoff", new=AsyncMock(side_effect=_build_once)),
        ):
            results = await asyncio.gather(
                *[
                    AuthorizationContextService.get_or_build(
                        user=user,
                        resource_type="knowledge.chunk",
                        action_code="read",
                        permission_code="knowledge:chunk:read",
                    )
                    for _ in range(6)
                ]
            )

        self.assertEqual(call_count, 1)
        self.assertEqual(len(results), 6)
        self.assertTrue(all(item.user_id == 1 for item in results))

    async def test_local_fallback_cache_hit_avoids_rebuild(self) -> None:
        user = _build_user()
        built_context = UserAuthorizationContext(
            user_id=1,
            role_ids=[],
            readable_resource_ids=[
                "chunk-1"
            ],
            readable_resource_filters={
                "deny_all": False
            },
            version=1,
        )

        with (
            patch("ns_backend.iam.services.authorization_context.AuthorizationContextService._safe_cache_get", return_value=None),
            patch("ns_backend.iam.services.authorization_context.AuthorizationContextService._safe_cache_set", return_value=False),
            patch("ns_backend.iam.services.authorization_context.AuthorizationContextService._get_user_version", return_value=1),
            patch(
                "ns_backend.iam.services.authorization_context.AuthorizationContextService._build_context_with_backoff", new=AsyncMock(
                    return_value=(
                            built_context,
                            0
                    )
                )
            ) as build_mock,
        ):
            first = await AuthorizationContextService.get_or_build(
                user=user,
                resource_type="knowledge.chunk",
                action_code="read",
                permission_code="knowledge:chunk:read",
            )
            second = await AuthorizationContextService.get_or_build(
                user=user,
                resource_type="knowledge.chunk",
                action_code="read",
                permission_code="knowledge:chunk:read",
            )

        self.assertEqual(first.user_id, 1)
        self.assertEqual(second.user_id, 1)
        self.assertEqual(build_mock.await_count, 1)


if __name__ == "__main__":
    unittest.main()
