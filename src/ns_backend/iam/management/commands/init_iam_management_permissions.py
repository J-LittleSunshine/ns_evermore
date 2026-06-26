# -*- coding: utf-8 -*-
from __future__ import annotations

from dataclasses import dataclass
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
    IamPermission,
    IamRole,
    IamRolePermission,
    IamUser,
    IamUserRole,
)

if TYPE_CHECKING:
    from argparse import ArgumentParser


@dataclass(slots=True, kw_only=True)
class SeedPermissionSpec:
    permission_code: str
    permission_name: str


class Command(BaseCommand):
    help = "Initialize IAM management action permissions and built-in IAM manager role."

    DEFAULT_ADMIN_USERNAME = "admin"
    DEFAULT_ROLE_CODE = "iam_manager"
    DEFAULT_ROLE_NAME = "IAM Manager"

    MANAGEMENT_PERMISSION_SPECS = (
        SeedPermissionSpec(permission_code="iam:company:read", permission_name="Read companies"),
        SeedPermissionSpec(permission_code="iam:company:create", permission_name="Create companies"),
        SeedPermissionSpec(permission_code="iam:company:update", permission_name="Update companies"),
        SeedPermissionSpec(permission_code="iam:company:delete", permission_name="Delete companies"),

        SeedPermissionSpec(permission_code="iam:subsidiary:read", permission_name="Read subsidiaries"),
        SeedPermissionSpec(permission_code="iam:subsidiary:create", permission_name="Create subsidiaries"),
        SeedPermissionSpec(permission_code="iam:subsidiary:update", permission_name="Update subsidiaries"),
        SeedPermissionSpec(permission_code="iam:subsidiary:delete", permission_name="Delete subsidiaries"),

        SeedPermissionSpec(permission_code="iam:department:read", permission_name="Read departments"),
        SeedPermissionSpec(permission_code="iam:department:create", permission_name="Create departments"),
        SeedPermissionSpec(permission_code="iam:department:update", permission_name="Update departments"),
        SeedPermissionSpec(permission_code="iam:department:delete", permission_name="Delete departments"),

        SeedPermissionSpec(permission_code="iam:permission:read", permission_name="Read permissions"),
        SeedPermissionSpec(permission_code="iam:permission:create", permission_name="Create permissions"),
        SeedPermissionSpec(permission_code="iam:permission:update", permission_name="Update permissions"),
        SeedPermissionSpec(permission_code="iam:permission:delete", permission_name="Delete permissions"),

        SeedPermissionSpec(permission_code="iam:resource:read", permission_name="Read resources"),
        SeedPermissionSpec(permission_code="iam:resource:create", permission_name="Create resources"),
        SeedPermissionSpec(permission_code="iam:resource:update", permission_name="Update resources"),
        SeedPermissionSpec(permission_code="iam:resource:delete", permission_name="Delete resources"),

        SeedPermissionSpec(permission_code="iam:resource_acl:read", permission_name="Read resource ACLs"),
        SeedPermissionSpec(permission_code="iam:resource_acl:create", permission_name="Create resource ACLs"),
        SeedPermissionSpec(permission_code="iam:resource_acl:delete", permission_name="Delete resource ACLs"),

        SeedPermissionSpec(permission_code="iam:resource_action:read", permission_name="Read resource actions"),
        SeedPermissionSpec(permission_code="iam:resource_action:create", permission_name="Create resource actions"),
        SeedPermissionSpec(permission_code="iam:resource_action:update", permission_name="Update resource actions"),
        SeedPermissionSpec(permission_code="iam:resource_action:delete", permission_name="Delete resource actions"),

        SeedPermissionSpec(permission_code="iam:resource_relation:read", permission_name="Read resource relations"),
        SeedPermissionSpec(permission_code="iam:resource_relation:create", permission_name="Create resource relations"),
        SeedPermissionSpec(permission_code="iam:resource_relation:delete", permission_name="Delete resource relations"),

        SeedPermissionSpec(permission_code="iam:audit:decision:read", permission_name="Read decision audit logs"),

        SeedPermissionSpec(permission_code="iam:role:read", permission_name="Read roles"),
        SeedPermissionSpec(permission_code="iam:role:create", permission_name="Create roles"),
        SeedPermissionSpec(permission_code="iam:role:update", permission_name="Update roles"),
        SeedPermissionSpec(permission_code="iam:role:delete", permission_name="Delete roles"),

        SeedPermissionSpec(permission_code="iam:user:read", permission_name="Read users"),
        SeedPermissionSpec(permission_code="iam:user:create", permission_name="Create users"),
        SeedPermissionSpec(permission_code="iam:user:update", permission_name="Update users"),
        SeedPermissionSpec(permission_code="iam:user:delete", permission_name="Delete users"),
        SeedPermissionSpec(permission_code="iam:user:reset_password", permission_name="Reset user password"),

        SeedPermissionSpec(permission_code="iam:user_role:read", permission_name="Read user role grants"),
        SeedPermissionSpec(permission_code="iam:user_role:create", permission_name="Create user role grants"),
        SeedPermissionSpec(permission_code="iam:user_role:delete", permission_name="Delete user role grants"),

        SeedPermissionSpec(permission_code="iam:role_permission:read", permission_name="Read role permission grants"),
        SeedPermissionSpec(permission_code="iam:role_permission:create", permission_name="Create role permission grants"),
        SeedPermissionSpec(permission_code="iam:role_permission:delete", permission_name="Delete role permission grants"),

        SeedPermissionSpec(permission_code="iam:user_permission:read", permission_name="Read user direct permission grants"),
        SeedPermissionSpec(permission_code="iam:user_permission:create", permission_name="Create user direct permission grants"),
        SeedPermissionSpec(permission_code="iam:user_permission:delete", permission_name="Delete user direct permission grants"),

        SeedPermissionSpec(permission_code="iam:department_permission:read", permission_name="Read department permission grants"),
        SeedPermissionSpec(permission_code="iam:department_permission:create", permission_name="Create department permission grants"),
        SeedPermissionSpec(permission_code="iam:department_permission:delete", permission_name="Delete department permission grants"),

        SeedPermissionSpec(permission_code="iam:subsidiary_permission:read", permission_name="Read subsidiary permission grants"),
        SeedPermissionSpec(permission_code="iam:subsidiary_permission:create", permission_name="Create subsidiary permission grants"),
        SeedPermissionSpec(permission_code="iam:subsidiary_permission:delete", permission_name="Delete subsidiary permission grants"),
    )

    def add_arguments(self, parser: "ArgumentParser") -> None:
        parser.add_argument(
            "--database",
            default="",
            help="Django database alias. Default: resolve by IAM database router mapping.",
        )
        parser.add_argument(
            "--admin-username",
            default=self.DEFAULT_ADMIN_USERNAME,
            help=f"Grantor username and default assignee. Default: {self.DEFAULT_ADMIN_USERNAME}.",
        )
        parser.add_argument(
            "--role-code",
            default=self.DEFAULT_ROLE_CODE,
            help=f"Built-in IAM manager role code. Default: {self.DEFAULT_ROLE_CODE}.",
        )
        parser.add_argument(
            "--role-name",
            default=self.DEFAULT_ROLE_NAME,
            help=f"Built-in IAM manager role name. Default: {self.DEFAULT_ROLE_NAME}.",
        )
        parser.add_argument(
            "--grant-user",
            action="append",
            default=[],
            help=(
                "Additional PERSONAL username to bind to the IAM manager role. "
                "Can be specified multiple times, for example: --grant-user dev --grant-user alice."
            ),
        )

    def handle(self, *args: object, **options: object) -> None:
        database_alias = self.resolve_database_alias(
            str(options.get("database", "") or "").strip()
        )

        admin_username = self.normalize_username(
            options.get("admin_username"),
            "admin_username",
        )
        role_code = self.normalize_code(
            options.get("role_code"),
            "role_code",
            max_length=64,
        )
        role_name = self.normalize_code(
            options.get("role_name"),
            "role_name",
            max_length=128,
        )
        grant_usernames = self.resolve_grant_usernames(
            admin_username=admin_username,
            extra_usernames=options.get("grant_user") or [],
        )

        self.stdout.write(
            self.style.NOTICE(
                f"Initializing IAM management permissions on database alias '{database_alias}'."
            )
        )

        with transaction.atomic(using=database_alias):
            grantor = self.get_grantor(
                database_alias=database_alias,
                username=admin_username,
            )

            permission_results = self.upsert_permissions(
                database_alias=database_alias,
                grantor=grantor,
            )

            role, role_created = self.upsert_manager_role(
                database_alias=database_alias,
                role_code=role_code,
                role_name=role_name,
                grantor=grantor,
            )

            role_permission_results = self.bind_permissions_to_role(
                database_alias=database_alias,
                role=role,
                grantor=grantor,
            )

            user_role_results = self.bind_role_to_users(
                database_alias=database_alias,
                role=role,
                grantor=grantor,
                usernames=grant_usernames,
            )

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                "IAM management permission seed completed."
            )
        )
        self.stdout.write(
            f"Permissions: created={permission_results['created']}, updated={permission_results['updated']}."
        )
        self.stdout.write(
            f"Role: {'created' if role_created else 'updated'} '{role.role_code}'."
        )
        self.stdout.write(
            f"Role permissions: created={role_permission_results['created']}, updated={role_permission_results['updated']}."
        )
        self.stdout.write(
            f"User roles: created={user_role_results['created']}, existing={user_role_results['existing']}."
        )

    @staticmethod
    def resolve_database_alias(database_alias: str) -> str:
        if database_alias:
            resolved_alias = database_alias
        else:
            resolved_alias = BaseRepository.resolve_db_alias(IamPermission)

        if resolved_alias not in connections.databases:
            available_aliases = ", ".join(sorted(connections.databases))
            raise CommandError(
                f"Unknown database alias: {resolved_alias}. "
                f"Available aliases: {available_aliases}"
            )

        return resolved_alias

    @staticmethod
    def normalize_username(value: object, field_name: str) -> str:
        username = str(value or "").strip()

        if not username:
            raise CommandError(f"{field_name} must not be empty.")

        if len(username) > 64:
            raise CommandError(f"{field_name} must not exceed 64 characters.")

        return username

    @staticmethod
    def normalize_code(value: object, field_name: str, *, max_length: int) -> str:
        code = str(value or "").strip()

        if not code:
            raise CommandError(f"{field_name} must not be empty.")

        if len(code) > max_length:
            raise CommandError(f"{field_name} must not exceed {max_length} characters.")

        return code

    @classmethod
    def resolve_grant_usernames(cls, *, admin_username: str, extra_usernames: list[object]) -> tuple[str, ...]:
        """
        解析需要绑定 iam_manager 角色的用户。

        规则：
        - admin 默认绑定，满足 Step 8.4 的 admin -> role。
        - dev 或其他用户通过 --grant-user 显式绑定，避免默认把 dev 从无权限测试账号变成管理员。
        - 去重并保持顺序。
        """
        usernames: list[str] = [
            admin_username
        ]

        for raw_username in extra_usernames:
            usernames.append(
                cls.normalize_username(raw_username, "grant_user")
            )

        seen = set()
        result = []

        for username in usernames:
            if username in seen:
                continue
            seen.add(username)
            result.append(username)

        return tuple(result)

    @staticmethod
    def get_grantor(*, database_alias: str, username: str) -> IamUser:
        grantor = (
            IamUser.objects.using(database_alias)
            .filter(username=username)
            .first()
        )

        if grantor is None:
            raise CommandError(
                f"IAM user '{username}' does not exist. "
                f"Run init_iam_users first or specify --admin-username."
            )

        if int(grantor.is_active) != 1:
            raise CommandError(f"IAM user '{username}' is not active.")

        return grantor

    @classmethod
    def upsert_permissions(cls, *, database_alias: str, grantor: IamUser) -> dict[str, int]:
        now = timezone.now()
        created_count = 0
        updated_count = 0

        for spec in cls.MANAGEMENT_PERMISSION_SPECS:
            permission = (
                IamPermission.objects.using(database_alias)
                .filter(permission_code=spec.permission_code)
                .first()
            )

            if permission is None:
                IamPermission.objects.using(database_alias).create(
                    permission_code=spec.permission_code,
                    permission_name=spec.permission_name,
                    permission_type=IamPermission.TYPE_ACTION,
                    parent_id=None,
                    status=1,
                    created_by=grantor.id,
                    updated_by=grantor.id,
                    created_at=now,
                    updated_at=now,
                )
                created_count += 1
                continue

            permission.permission_name = spec.permission_name
            permission.permission_type = IamPermission.TYPE_ACTION
            permission.parent_id = None
            permission.status = 1
            permission.updated_by = grantor.id
            permission.updated_at = now
            permission.save(
                using=database_alias,
                update_fields=[
                    "permission_name",
                    "permission_type",
                    "parent_id",
                    "status",
                    "updated_by",
                    "updated_at",
                ],
            )
            updated_count += 1

        return {
            "created": created_count,
            "updated": updated_count,
        }

    @staticmethod
    def upsert_manager_role(*, database_alias: str, role_code: str, role_name: str, grantor: IamUser) -> tuple[IamRole, bool]:
        """
        初始化 PERSONAL 域 IAM 管理角色。

        说明：
        - 当前内置 admin/dev 都是 PERSONAL 用户。
        - ENTERPRISE 公司域角色后续应由管理接口按 company 创建，不在种子命令里默认生成。
        """
        now = timezone.now()

        role = (
            IamRole.objects.using(database_alias)
            .filter(
                role_scope=IamRole.SCOPE_PERSONAL,
                company_id__isnull=True,
                role_code=role_code,
            )
            .first()
        )

        if role is None:
            role = IamRole.objects.using(database_alias).create(
                role_code=role_code,
                role_name=role_name,
                role_scope=IamRole.SCOPE_PERSONAL,
                company_id=None,
                status=1,
                created_by=grantor.id,
                updated_by=grantor.id,
                created_at=now,
                updated_at=now,
            )
            return role, True

        role.role_name = role_name
        role.status = 1
        role.updated_by = grantor.id
        role.updated_at = now
        role.save(
            using=database_alias,
            update_fields=[
                "role_name",
                "status",
                "updated_by",
                "updated_at",
            ],
        )

        return role, False

    @classmethod
    def bind_permissions_to_role(cls, *, database_alias: str, role: IamRole, grantor: IamUser) -> dict[str, int]:
        now = timezone.now()
        created_count = 0
        updated_count = 0

        permissions = {
            item.permission_code: item
            for item in IamPermission.objects.using(database_alias).filter(
                permission_code__in=[
                    spec.permission_code
                    for spec in cls.MANAGEMENT_PERMISSION_SPECS
                ]
            )
        }

        for spec in cls.MANAGEMENT_PERMISSION_SPECS:
            permission = permissions.get(spec.permission_code)

            if permission is None:
                raise CommandError(
                    f"Permission '{spec.permission_code}' was not created correctly."
                )

            relation = (
                IamRolePermission.objects.using(database_alias)
                .filter(
                    role_id=role.id,
                    permission_id=permission.id,
                )
                .first()
            )

            if relation is None:
                IamRolePermission.objects.using(database_alias).create(
                    role_id=role.id,
                    permission_id=permission.id,
                    data_scope=None,
                    granted_by_id=grantor.id,
                    expired_at=None,
                    created_by=grantor.id,
                    updated_by=grantor.id,
                    created_at=now,
                    updated_at=now,
                )
                created_count += 1
                continue

            relation.data_scope = None
            relation.granted_by_id = grantor.id
            relation.expired_at = None
            relation.updated_by = grantor.id
            relation.updated_at = now
            relation.save(
                using=database_alias,
                update_fields=[
                    "data_scope",
                    "granted_by",
                    "expired_at",
                    "updated_by",
                    "updated_at",
                ],
            )
            updated_count += 1

        return {
            "created": created_count,
            "updated": updated_count,
        }

    @staticmethod
    def bind_role_to_users(*, database_alias: str, role: IamRole, grantor: IamUser, usernames: tuple[str, ...]) -> dict[str, int]:
        now = timezone.now()
        created_count = 0
        existing_count = 0

        for username in usernames:
            user = (
                IamUser.objects.using(database_alias)
                .filter(username=username)
                .first()
            )

            if user is None:
                raise CommandError(f"IAM user '{username}' does not exist.")

            if int(user.is_active) != 1:
                raise CommandError(f"IAM user '{username}' is not active.")

            if user.user_type != IamUser.USER_TYPE_PERSONAL:
                raise CommandError(
                    f"IAM user '{username}' is not a PERSONAL user. "
                    f"The built-in role '{role.role_code}' is PERSONAL scope."
                )

            relation = (
                IamUserRole.objects.using(database_alias)
                .filter(
                    user_id=user.id,
                    role_id=role.id,
                )
                .first()
            )

            if relation is not None:
                existing_count += 1
                continue

            IamUserRole.objects.using(database_alias).create(
                user_id=user.id,
                role_id=role.id,
                created_by=grantor.id,
                updated_by=grantor.id,
                created_at=now,
                updated_at=now,
            )
            created_count += 1

        return {
            "created": created_count,
            "existing": existing_count,
        }
