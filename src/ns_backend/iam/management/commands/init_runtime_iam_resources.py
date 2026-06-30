# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from django.core.management.base import (
    BaseCommand,
    CommandError,
)
from django.db import (
    connections,
    transaction,
)
from django.utils import timezone

from backend.common import BaseRepository
from ns_backend.iam.models import (
    IamResource,
    IamResourceAcl,
    IamResourceAction,
    IamUser
)
from ns_backend.iam.services.cache import IamCacheService

if TYPE_CHECKING:
    from argparse import ArgumentParser


class Command(BaseCommand):
    help = "Initialize IAM resources and ACLs required by ns_runtime."

    DEFAULT_RESOURCE_TYPE = "ns_runtime_connection"
    DEFAULT_RESOURCE_NAME = "NsRuntime Connection"
    DEFAULT_MODULE_CODE = "ns_runtime"
    DEFAULT_ACTION_CODE = "connect"
    DEFAULT_ACTION_NAME = "Connect to NsRuntime"
    DEFAULT_RESOURCE_ID = "ns_client"

    def add_arguments(self, parser: "ArgumentParser") -> None:
        parser.add_argument(
            "--database",
            default="",
            help="Django database alias. Default: resolve by IAM database router mapping.",
        )
        parser.add_argument(
            "--resource-id",
            default=self.DEFAULT_RESOURCE_ID,
            help=f"Runtime connection resource id to grant. Default: {self.DEFAULT_RESOURCE_ID}.",
        )
        parser.add_argument(
            "--grant-user",
            action="append",
            default=[],
            help=(
                "Username to grant runtime connection access. "
                "Can be specified multiple times, for example: --grant-user dev --grant-user alice."
            ),
        )

    def handle(self, *args: object, **options: object) -> None:
        database_alias = self.resolve_database_alias(
            str(options.get("database", "") or "").strip()
        )
        resource_id = self.normalize_required_text(
            options.get("resource_id"),
            "resource_id",
            max_length=128,
        )
        grant_usernames = self.normalize_grant_usernames(
            options.get("grant_user") or []
        )

        self.stdout.write(
            self.style.NOTICE(
                f"Initializing ns_runtime IAM resources on database alias '{database_alias}'."
            )
        )

        with transaction.atomic(using=database_alias):
            resource, resource_created = self.upsert_runtime_connection_resource(
                database_alias=database_alias,
            )
            action, action_created = self.upsert_connect_action(
                database_alias=database_alias,
                resource=resource,
            )
            acl_results = self.upsert_user_acls(
                database_alias=database_alias,
                resource_id=resource_id,
                grant_usernames=grant_usernames,
            )

        cache_version = IamCacheService.bump_authz_version()

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "NsRuntime IAM resource seed completed."
            )
        )
        self.stdout.write(
            f"Resource: {'created' if resource_created else 'updated'} "
            f"'{resource.resource_type}'."
        )
        self.stdout.write(
            f"Action: {'created' if action_created else 'updated'} "
            f"'{action.action_code}'."
        )
        self.stdout.write(
            f"ACLs: created={acl_results['created']}, updated={acl_results['updated']}, skipped={acl_results['skipped']}."
        )

        if cache_version is None:
            self.stdout.write(
                "IAM authz cache version: skipped or unavailable."
            )
        else:
            self.stdout.write(
                f"IAM authz cache version: bumped to {cache_version}."
            )

        if not grant_usernames:
            self.stdout.write(
                self.style.WARNING(
                    "No --grant-user specified. Non-superuser accounts will still be denied."
                )
            )

    @staticmethod
    def resolve_database_alias(database_alias: str) -> str:
        if database_alias:
            resolved_alias = database_alias
        else:
            resolved_alias = BaseRepository.resolve_db_alias(IamResource)

        if resolved_alias not in connections.databases:
            available_aliases = ", ".join(sorted(connections.databases))
            raise CommandError(
                f"Unknown database alias: {resolved_alias}. "
                f"Available aliases: {available_aliases}"
            )

        return resolved_alias

    @staticmethod
    def normalize_required_text(value: object, field_name: str, *, max_length: int) -> str:
        text = str(value or "").strip()

        if not text:
            raise CommandError(f"{field_name} must not be empty.")

        if len(text) > max_length:
            raise CommandError(f"{field_name} must not exceed {max_length} characters.")

        return text

    @classmethod
    def normalize_grant_usernames(cls, values: list[object]) -> tuple[str, ...]:
        result: list[str] = []
        seen: set[str] = set()

        for value in values:
            username = cls.normalize_required_text(
                value,
                "grant_user",
                max_length=64,
            )

            if username in seen:
                continue

            seen.add(username)
            result.append(username)

        return tuple(result)

    @classmethod
    def upsert_runtime_connection_resource(cls, *, database_alias: str) -> tuple[IamResource, bool]:
        now = timezone.now()

        resource = (
            IamResource.objects.using(database_alias)
            .filter(resource_type=cls.DEFAULT_RESOURCE_TYPE)
            .first()
        )

        if resource is None:
            resource = IamResource.objects.using(database_alias).create(
                resource_type=cls.DEFAULT_RESOURCE_TYPE,
                resource_name=cls.DEFAULT_RESOURCE_NAME,
                module_code=cls.DEFAULT_MODULE_CODE,
                access_mode=IamResource.ACCESS_MODE_RBAC_DEFAULT_ALLOW,
                status=1,
                created_by=None,
                updated_by=None,
                created_at=now,
                updated_at=now,
            )
            return resource, True

        resource.resource_name = cls.DEFAULT_RESOURCE_NAME
        resource.module_code = cls.DEFAULT_MODULE_CODE
        resource.access_mode = IamResource.ACCESS_MODE_RBAC_DEFAULT_ALLOW
        resource.status = 1
        resource.updated_at = now
        resource.save(
            using=database_alias,
            update_fields=[
                "resource_name",
                "module_code",
                "access_mode",
                "status",
                "updated_at",
            ],
        )

        return resource, False

    @classmethod
    def upsert_connect_action(cls, *, database_alias: str, resource: IamResource) -> tuple[IamResourceAction, bool]:
        now = timezone.now()

        action = (
            IamResourceAction.objects.using(database_alias)
            .filter(
                resource_id=resource.id,
                action_code=cls.DEFAULT_ACTION_CODE,
            )
            .first()
        )

        if action is None:
            action = IamResourceAction.objects.using(database_alias).create(
                resource_id=resource.id,
                action_code=cls.DEFAULT_ACTION_CODE,
                action_name=cls.DEFAULT_ACTION_NAME,
                status=1,
                created_by=None,
                updated_by=None,
                created_at=now,
                updated_at=now,
            )
            return action, True

        action.action_name = cls.DEFAULT_ACTION_NAME
        action.status = 1
        action.updated_at = now
        action.save(
            using=database_alias,
            update_fields=[
                "action_name",
                "status",
                "updated_at",
            ],
        )

        return action, False

    @classmethod
    def upsert_user_acls(
            cls,
            *,
            database_alias: str,
            resource_id: str,
            grant_usernames: tuple[str, ...],
    ) -> dict[str, int]:
        now = timezone.now()
        created_count = 0
        updated_count = 0
        skipped_count = 0

        for username in grant_usernames:
            user = (
                IamUser.objects.using(database_alias)
                .filter(username=username)
                .first()
            )

            if user is None:
                raise CommandError(
                    f"IAM user '{username}' does not exist. Run init_iam_users first."
                )

            if int(user.is_active) != 1:
                raise CommandError(
                    f"IAM user '{username}' is not active."
                )

            acl = (
                IamResourceAcl.objects.using(database_alias)
                .filter(
                    subject_type=IamResourceAcl.SUBJECT_USER,
                    subject_id=user.id,
                    resource_type=cls.DEFAULT_RESOURCE_TYPE,
                    resource_id=resource_id,
                    action_code=cls.DEFAULT_ACTION_CODE,
                )
                .first()
            )

            if acl is None:
                IamResourceAcl.objects.using(database_alias).create(
                    subject_type=IamResourceAcl.SUBJECT_USER,
                    subject_id=user.id,
                    resource_type=cls.DEFAULT_RESOURCE_TYPE,
                    resource_id=resource_id,
                    action_code=cls.DEFAULT_ACTION_CODE,
                    effect=IamResourceAcl.EFFECT_ALLOW,
                    data_scope=None,
                    expired_at=None,
                    created_by=None,
                    updated_by=None,
                    created_at=now,
                    updated_at=now,
                )
                created_count += 1
                continue

            if acl.effect == IamResourceAcl.EFFECT_ALLOW and acl.expired_at is None:
                skipped_count += 1
                continue

            acl.effect = IamResourceAcl.EFFECT_ALLOW
            acl.data_scope = None
            acl.expired_at = None
            acl.updated_at = now
            acl.save(
                using=database_alias,
                update_fields=[
                    "effect",
                    "data_scope",
                    "expired_at",
                    "updated_at",
                ],
            )
            updated_count += 1

        return {
            "created": created_count,
            "updated": updated_count,
            "skipped": skipped_count,
        }
