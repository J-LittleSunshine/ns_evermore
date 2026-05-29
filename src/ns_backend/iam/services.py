# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.contrib.auth.hashers import make_password
from django.db.models import Q
from django.utils import timezone

from ns_backend.backend.common import CrudRepository
from ns_backend.backend.exceptions import BusinessError
from ns_common.error_codes import NsErrorCode
from .constants import USER_TYPE_ENTERPRISE, PERMISSION_EFFECT_DENY, PERMISSION_EFFECT_ALLOW, USER_TYPE_PERSONAL, DATA_SCOPE_DEPARTMENT_TREE
from .models import (
    IamCompany,
    IamDepartment,
    IamDepartmentPermission,
    IamPermission,
    IamRole,
    IamRolePermission,
    IamSubsidiary,
    IamSubsidiaryPermission,
    IamUser,
    IamUserPermission,
    IamUserRole, IamUserToken, IamUserSession
)
from .policies import TenantPolicy, DataScopePolicy
from .schemas import TenantContext, DataScopeResult
from .validators import (
    CompanyValidator,
    DepartmentPermissionValidator,
    DepartmentValidator,
    PermissionValidator,
    RolePermissionValidator,
    RoleValidator,
    SubsidiaryPermissionValidator,
    SubsidiaryValidator,
    UserPermissionValidator,
    UserRoleValidator,
    UserValidator
)

if TYPE_CHECKING:
    pass


class TenantService:
    @classmethod
    def from_user(cls, user: Any) -> TenantContext:
        return TenantContext(
            user_id=user.id,
            user_type=getattr(user, "user_type", ""),
            company_id=getattr(user, "company_id", None),
            subsidiary_id=getattr(user, "subsidiary_id", None),
            department_id=getattr(user, "department_id", None),
            is_staff=bool(getattr(user, "is_staff", False)),
            is_superuser=bool(getattr(user, "is_superuser", False)),
        )


class IamCrudService:
    model_class: Any = None
    validator_class: Any = None

    list_fields: tuple[str, ...] = ()
    detail_fields: tuple[str, ...] = ()
    update_fields: tuple[str, ...] = ()

    tenant_scope_field: str | None = None
    tenant_create_field: str | None = None
    enterprise_resource_required: bool = False

    @classmethod
    async def list_items(cls, *, page: int | str | None = 1, page_size: int | str | None = 20, tenant_context: TenantContext | None = None) -> dict[str, Any]:
        tenant_filter = cls.get_tenant_filter(tenant_context=tenant_context)
        return await CrudRepository.list_items(model_class=cls.model_class, fields=cls.list_fields, page=page, page_size=page_size, tenant_filter=tenant_filter)

    @classmethod
    async def detail_item(cls, *, item_id: int | str | None, tenant_context: TenantContext | None = None) -> dict[str, Any]:
        tenant_filter = cls.get_tenant_filter(tenant_context=tenant_context)
        return await CrudRepository.detail_item(model_class=cls.model_class, item_id=item_id, fields=cls.detail_fields, tenant_filter=tenant_filter)

    @classmethod
    async def create_item(cls, *, data: dict[str, Any], operator_id: int | None = None, tenant_context: TenantContext | None = None) -> dict[str, Any]:
        validated_data = cls.validate_create_data(data)
        tenant_create_values = cls.get_tenant_create_values(tenant_context=tenant_context)
        return await CrudRepository.create_item_with_audit(model_class=cls.model_class, data=validated_data, operator_id=operator_id, tenant_create_values=tenant_create_values)

    @classmethod
    async def update_item(cls, *, item_id: int | str | None, data: dict[str, Any], operator_id: int | None = None, tenant_context: TenantContext | None = None) -> None:
        validated_data = cls.validate_update_data(data)
        tenant_filter = cls.get_tenant_filter(tenant_context=tenant_context)
        await CrudRepository.update_item_with_audit(model_class=cls.model_class, item_id=item_id, data=validated_data, operator_id=operator_id, tenant_filter=tenant_filter)

    @classmethod
    async def delete_item(cls, *, item_id: int | str | None, tenant_context: TenantContext | None = None) -> None:
        tenant_filter = cls.get_tenant_filter(tenant_context=tenant_context)
        await CrudRepository.delete_item_by_id(model_class=cls.model_class, item_id=item_id, tenant_filter=tenant_filter)

    @classmethod
    def validate_create_data(cls, data: dict[str, Any]) -> dict[str, Any]:
        if cls.validator_class:
            return cls.validator_class.validate_create(data)
        return data

    @classmethod
    def validate_update_data(cls, data: dict[str, Any]) -> dict[str, Any]:
        allowed_update_fields = set(cls.update_fields)
        for field in data.keys():
            if field == "id":
                continue
            if allowed_update_fields and field not in allowed_update_fields:
                raise BusinessError(f"Updating field is not allowed: {field}", NsErrorCode.UPDATE_FIELD_NOT_ALLOWED)

        if cls.validator_class:
            return cls.validator_class.validate_update(data)

        return {field: data[field] for field in cls.update_fields if field in data}

    @classmethod
    def get_tenant_filter(cls, *, tenant_context: TenantContext | None) -> dict[str, Any] | None:
        if cls.tenant_scope_field is None or tenant_context is None:
            return None

        if TenantPolicy.is_platform_admin(tenant_context):
            return None

        if cls.enterprise_resource_required:
            TenantPolicy.ensure_enterprise_context(tenant_context)

        if tenant_context.user_type == USER_TYPE_ENTERPRISE:
            company_id = tenant_context.company_id
            if company_id is None:
                raise BusinessError("Enterprise user is not bound to a company", NsErrorCode.ENTERPRISE_USER_COMPANY_NOT_BOUND)
            return {cls.tenant_scope_field: company_id}

        raise BusinessError("Personal users cannot access enterprise organization resources", NsErrorCode.ENTERPRISE_ORG_FORBIDDEN_PERSONAL)

    @classmethod
    def get_tenant_create_values(cls, *, tenant_context: TenantContext | None) -> dict[str, Any] | None:
        if cls.tenant_create_field is None or tenant_context is None:
            return None

        if TenantPolicy.is_platform_admin(tenant_context):
            return None

        if cls.enterprise_resource_required:
            TenantPolicy.ensure_enterprise_context(tenant_context)

        if tenant_context.user_type == USER_TYPE_ENTERPRISE:
            company_id = tenant_context.company_id
            if company_id is None:
                raise BusinessError("Enterprise user is not bound to a company", NsErrorCode.ENTERPRISE_USER_COMPANY_NOT_BOUND)
            return {cls.tenant_create_field: company_id}

        raise BusinessError("Personal users cannot access enterprise organization resources", NsErrorCode.ENTERPRISE_ORG_FORBIDDEN_PERSONAL)


class CompanyCrudService(IamCrudService):
    model_class = IamCompany
    validator_class = CompanyValidator
    tenant_scope_field = "id"
    tenant_create_field = None
    enterprise_resource_required = True

    list_fields = detail_fields = ("id", "company_code", "company_name", "legal_name", "status")
    update_fields = ("company_name", "legal_name", "status")


class SubsidiaryCrudService(IamCrudService):
    model_class = IamSubsidiary
    validator_class = SubsidiaryValidator
    tenant_scope_field = "company_id"
    tenant_create_field = "company_id"
    enterprise_resource_required = True

    list_fields = detail_fields = ("id", "company_id", "subsidiary_code", "subsidiary_name", "status")
    update_fields = ("subsidiary_name", "status")


class DepartmentCrudService(IamCrudService):
    model_class = IamDepartment
    validator_class = DepartmentValidator
    tenant_scope_field = "company_id"
    tenant_create_field = "company_id"
    enterprise_resource_required = True

    list_fields = detail_fields = ("id", "company_id", "subsidiary_id", "parent_id", "department_code", "department_name", "status")
    update_fields = ("department_name", "status")


class PermissionCrudService(IamCrudService):
    model_class = IamPermission
    validator_class = PermissionValidator
    list_fields = detail_fields = ("id", "permission_code", "permission_name", "permission_type", "parent_id", "status")
    update_fields = ("permission_name", "permission_type", "parent_id", "status")


class RoleCrudService(IamCrudService):
    model_class = IamRole
    validator_class = RoleValidator
    tenant_scope_field = "company_id"
    tenant_create_field = "company_id"
    enterprise_resource_required = False

    list_fields = detail_fields = ("id", "company_id", "role_code", "role_name", "role_scope", "status")
    update_fields = ("role_name", "status")


class UserCrudService(IamCrudService):
    model_class = IamUser
    validator_class = UserValidator
    tenant_scope_field = "company_id"
    tenant_create_field = "company_id"
    enterprise_resource_required = False

    list_fields = detail_fields = (
        "id",
        "username",
        "email",
        "phone",
        "display_name",
        "user_type",
        "company_id",
        "subsidiary_id",
        "department_id",
        "is_active",
        "is_staff",
        "is_superuser",
        "last_login",
        "created_at",
        "updated_at"
    )
    update_fields = ("email", "phone", "display_name", "company_id", "subsidiary_id", "department_id", "is_active", "is_staff", "is_superuser")

    @classmethod
    async def create_item(cls, *, data: dict[str, Any], operator_id: int | None = None, tenant_context: TenantContext | None = None) -> dict[str, Any]:
        validated_data = cls.validate_create_data(data)
        raw_password = validated_data.get("password")
        if raw_password is None or raw_password == "":
            raise BusinessError("password cannot be empty", NsErrorCode.USER_PASSWORD_EMPTY)

        create_data = dict(validated_data)
        create_data["password"] = make_password(str(raw_password))

        tenant_create_values = cls.get_tenant_create_values(tenant_context=tenant_context)
        return await CrudRepository.create_item_with_audit(
            model_class=cls.model_class,
            data=create_data,
            operator_id=operator_id,
            tenant_create_values=tenant_create_values,
        )

    @classmethod
    async def update_item(cls, *, item_id: int | str | None, data: dict[str, Any], operator_id: int | None = None, tenant_context: TenantContext | None = None) -> None:
        tenant_filter = cls.get_tenant_filter(tenant_context=tenant_context)
        item = await CrudRepository.get_required_by_id(
            model_class=cls.model_class,
            item_id=item_id,
            tenant_filter=tenant_filter,
        )
        prev_is_active = bool(getattr(item, "is_active", False))

        validated_data = cls.validate_update_data(data)
        await CrudRepository.update_item_with_audit(
            model_class=cls.model_class,
            item_id=item_id,
            data=validated_data,
            operator_id=operator_id,
            tenant_filter=tenant_filter,
        )

        next_is_active = validated_data.get("is_active")
        should_revoke = prev_is_active and str(next_is_active) == "0"
        if should_revoke:
            now = timezone.now()
            await IamUserSession.objects.filter(user_id=item.id, revoked_at__isnull=True).aupdate(revoked_at=now)
            await IamUserToken.objects.filter(user_id=item.id, revoked_at__isnull=True).aupdate(revoked_at=now)

    @classmethod
    async def delete_item(cls, *, item_id: int | str | None, tenant_context: TenantContext | None = None) -> None:
        tenant_filter = cls.get_tenant_filter(tenant_context=tenant_context)
        item = await CrudRepository.get_required_by_id(
            model_class=cls.model_class,
            item_id=item_id,
            tenant_filter=tenant_filter,
        )

        now = timezone.now()
        await IamUserSession.objects.filter(user_id=item.id, revoked_at__isnull=True).aupdate(revoked_at=now)
        await IamUserToken.objects.filter(user_id=item.id, revoked_at__isnull=True).aupdate(revoked_at=now)

        await CrudRepository.delete_item(item)

    @classmethod
    async def reset_password(cls, *, item_id: int | str | None, password: str | None, operator_id: int | None = None, tenant_context: TenantContext | None = None) -> None:
        if not isinstance(password, str) or not password:
            raise BusinessError("password cannot be empty", NsErrorCode.USER_PASSWORD_EMPTY)

        tenant_filter = cls.get_tenant_filter(tenant_context=tenant_context)
        item = await CrudRepository.get_required_by_id(
            model_class=cls.model_class,
            item_id=item_id,
            tenant_filter=tenant_filter,
        )

        now = timezone.now()
        await CrudRepository.update_item(
            instance=item,
            data={
                "password": make_password(password),
                "updated_by": operator_id,
                "updated_at": now,
            },
        )
        await IamUserSession.objects.filter(user_id=item.id, revoked_at__isnull=True).aupdate(revoked_at=now)
        await IamUserToken.objects.filter(user_id=item.id, revoked_at__isnull=True).aupdate(revoked_at=now)


class UserRoleCrudService(IamCrudService):
    model_class = IamUserRole
    validator_class = UserRoleValidator
    list_fields = detail_fields = ("id", "user_id", "role_id")
    update_fields = ("user_id", "role_id")


class RolePermissionCrudService(IamCrudService):
    model_class = IamRolePermission
    validator_class = RolePermissionValidator
    list_fields = detail_fields = ("id", "role_id", "permission_id", "data_scope", "granted_by_id", "expired_at")
    update_fields = ("role_id", "permission_id", "data_scope", "granted_by_id", "expired_at")


class UserPermissionCrudService(IamCrudService):
    model_class = IamUserPermission
    validator_class = UserPermissionValidator
    list_fields = detail_fields = ("id", "user_id", "permission_id", "effect", "data_scope", "granted_by_id", "expired_at")
    update_fields = ("user_id", "permission_id", "effect", "data_scope", "granted_by_id", "expired_at")


class DepartmentPermissionCrudService(IamCrudService):
    model_class = IamDepartmentPermission
    validator_class = DepartmentPermissionValidator
    list_fields = detail_fields = ("id", "department_id", "permission_id", "effect", "data_scope", "granted_by_id", "expired_at")
    update_fields = ("department_id", "permission_id", "effect", "data_scope", "granted_by_id", "expired_at")


class SubsidiaryPermissionCrudService(IamCrudService):
    model_class = IamSubsidiaryPermission
    validator_class = SubsidiaryPermissionValidator
    list_fields = detail_fields = ("id", "subsidiary_id", "permission_id", "effect", "data_scope", "granted_by_id", "expired_at")
    update_fields = ("subsidiary_id", "permission_id", "effect", "data_scope", "granted_by_id", "expired_at")


class VerifyService:
    @classmethod
    async def get_user_by_access_token(cls, access_token: str):
        from ns_backend.backend.utils.jwt import JwtService

        payload = JwtService.decode_access_token(access_token)
        if not payload:
            return None

        user_id = payload.get("uid")
        access_jti = payload.get("jti")

        if not isinstance(user_id, int) or not isinstance(access_jti, str):
            return None

        now = timezone.now()

        token_record = await IamUserToken.objects.select_related("user", "session").filter(
            user_id=user_id,
            access_jti=access_jti,
            revoked_at__isnull=True,
            expired_at__gt=now,
        ).afirst()
        if token_record is None:
            return None

        session = getattr(token_record, "session", None)
        if session is not None:
            if session.revoked_at is not None:
                return None
            if session.expired_at <= now:
                return None

        user = getattr(token_record, "user", None)
        if user is None:
            user = await IamUser.objects.filter(id=user_id).afirst()

        if user is None or not bool(getattr(user, "is_active", False)):
            return None

        return user


class PermissionService:
    MAX_ANCESTOR_DEPTH = 20

    @staticmethod
    def _valid_time_q(now):
        return Q(expired_at__isnull=True) | Q(expired_at__gt=now)

    @classmethod
    async def get_active_permission_ids_with_ancestors(cls, permission_code: str) -> list[int]:
        permission = await IamPermission.objects.filter(status=1, permission_code=permission_code).only("id", "parent_id").afirst()
        if not permission:
            return []

        permission_ids: list[int] = []
        seen_ids: set[int] = set()
        current = permission

        for _ in range(cls.MAX_ANCESTOR_DEPTH):
            current_id = current.id
            if current_id in seen_ids:
                break

            seen_ids.add(current_id)
            permission_ids.append(current_id)

            if not current.parent_id:
                break

            current = await IamPermission.objects.filter(id=current.parent_id, status=1).only("id", "parent_id").afirst()
            if not current:
                break

        return permission_ids

    @classmethod
    async def has_permission(cls, user, permission_code: str) -> bool:
        if not user or not bool(getattr(user, "is_active", False)):
            return False

        if bool(getattr(user, "is_superuser", False)):
            return True

        if not permission_code:
            return False

        permission_ids = await cls.get_active_permission_ids_with_ancestors(permission_code)
        if not permission_ids:
            return False

        now = timezone.now()

        if user.user_type == USER_TYPE_PERSONAL:
            return await cls._has_personal_permission(user=user, permission_ids=permission_ids, now=now)

        if user.user_type == USER_TYPE_ENTERPRISE:
            return await cls._has_enterprise_permission(user=user, permission_ids=permission_ids, now=now)

        return False

    @classmethod
    async def _has_direct_effect(cls, model_class, *, subject_field: str, subject_id: int, permission_ids: list[int], effect: str, now) -> bool:
        return await model_class.objects.filter(
            cls._valid_time_q(now),
            **{subject_field: subject_id},
            permission_id__in=permission_ids,
            permission__status=1,
            effect=effect,
        ).aexists()

    @classmethod
    async def _has_role_allow(cls, *, user_id: int, permission_ids: list[int], now, role_scope: str, company_id: int | None) -> bool:
        role_filter = {
            "user_id": user_id,
            "role__status": 1,
            "role__role_scope": role_scope,
        }

        if role_scope == USER_TYPE_PERSONAL:
            role_filter["role__company_id__isnull"] = True
        elif role_scope == USER_TYPE_ENTERPRISE:
            role_filter["role__company_id"] = company_id

        role_ids = IamUserRole.objects.filter(**role_filter).values("role_id")

        return await IamRolePermission.objects.filter(
            cls._valid_time_q(now),
            role_id__in=role_ids,
            permission_id__in=permission_ids,
            permission__status=1,
        ).aexists()

    @classmethod
    async def _has_personal_permission(cls, *, user, permission_ids: list[int], now) -> bool:
        if await cls._has_direct_effect(
                IamUserPermission,
                subject_field="user_id",
                subject_id=user.id,
                permission_ids=permission_ids,
                effect=PERMISSION_EFFECT_DENY,
                now=now,
        ):
            return False

        has_user_allow = await cls._has_direct_effect(
            IamUserPermission,
            subject_field="user_id",
            subject_id=user.id,
            permission_ids=permission_ids,
            effect=PERMISSION_EFFECT_ALLOW,
            now=now,
        )
        has_role_allow = await cls._has_role_allow(
            user_id=user.id,
            permission_ids=permission_ids,
            now=now,
            role_scope=USER_TYPE_PERSONAL,
            company_id=None,
        )
        return has_user_allow or has_role_allow

    @classmethod
    async def _has_enterprise_permission(cls, *, user, permission_ids: list[int], now) -> bool:
        if not user.company_id:
            return False

        has_user_deny = await cls._has_direct_effect(
            IamUserPermission,
            subject_field="user_id",
            subject_id=user.id,
            permission_ids=permission_ids,
            effect=PERMISSION_EFFECT_DENY,
            now=now,
        )
        has_department_deny = False
        has_subsidiary_deny = False

        if user.department_id:
            has_department_deny = await cls._has_direct_effect(
                IamDepartmentPermission,
                subject_field="department_id",
                subject_id=user.department_id,
                permission_ids=permission_ids,
                effect=PERMISSION_EFFECT_DENY,
                now=now,
            )

        if user.subsidiary_id:
            has_subsidiary_deny = await cls._has_direct_effect(
                IamSubsidiaryPermission,
                subject_field="subsidiary_id",
                subject_id=user.subsidiary_id,
                permission_ids=permission_ids,
                effect=PERMISSION_EFFECT_DENY,
                now=now,
            )

        if has_user_deny or has_department_deny or has_subsidiary_deny:
            return False

        has_user_allow = await cls._has_direct_effect(
            IamUserPermission,
            subject_field="user_id",
            subject_id=user.id,
            permission_ids=permission_ids,
            effect=PERMISSION_EFFECT_ALLOW,
            now=now,
        )
        has_role_allow = await cls._has_role_allow(
            user_id=user.id,
            permission_ids=permission_ids,
            now=now,
            role_scope=USER_TYPE_ENTERPRISE,
            company_id=user.company_id,
        )
        has_department_allow = False
        has_subsidiary_allow = False

        if user.department_id:
            has_department_allow = await cls._has_direct_effect(
                IamDepartmentPermission,
                subject_field="department_id",
                subject_id=user.department_id,
                permission_ids=permission_ids,
                effect=PERMISSION_EFFECT_ALLOW,
                now=now,
            )

        if user.subsidiary_id:
            has_subsidiary_allow = await cls._has_direct_effect(
                IamSubsidiaryPermission,
                subject_field="subsidiary_id",
                subject_id=user.subsidiary_id,
                permission_ids=permission_ids,
                effect=PERMISSION_EFFECT_ALLOW,
                now=now,
            )

        return has_user_allow or has_role_allow or has_department_allow or has_subsidiary_allow

    @classmethod
    async def list_permission_codes(cls, user) -> list[str]:
        active_permissions = await cls._list_active_permissions()
        effective_ids = await cls.resolve_effective_permission_ids(user=user, active_permissions=active_permissions)
        codes = [item["permission_code"] for item in active_permissions if item["id"] in effective_ids]
        return sorted(codes)

    @classmethod
    async def list_menu_tree(cls, user) -> list[dict]:
        active_permissions = await cls._list_active_permissions()
        effective_ids = await cls.resolve_effective_permission_ids(user=user, active_permissions=active_permissions)
        return cls.build_menu_tree(active_permissions, effective_ids)

    @classmethod
    async def _list_active_permissions(cls) -> list[dict]:
        queryset = IamPermission.objects.filter(status=1).values(
            "id",
            "permission_code",
            "permission_name",
            "permission_type",
            "parent_id",
        ).order_by("permission_code")
        return [row async for row in queryset]

    @classmethod
    async def resolve_effective_permission_ids(cls, *, user, active_permissions: list[dict] | None = None) -> set[int]:
        if not user or not bool(getattr(user, "is_active", False)):
            return set()

        if active_permissions is None:
            active_permissions = await cls._list_active_permissions()

        active_ids = {item["id"] for item in active_permissions}

        if bool(getattr(user, "is_superuser", False)):
            return active_ids

        now = timezone.now()

        if user.user_type == USER_TYPE_PERSONAL:
            deny_ids = await cls._list_user_permission_ids(user.id, now, effect=PERMISSION_EFFECT_DENY)
            allow_ids = await cls._list_user_permission_ids(user.id, now, effect=PERMISSION_EFFECT_ALLOW)
            allow_ids.update(
                await cls._list_role_permission_ids(
                    user_id=user.id,
                    now=now,
                    role_scope=USER_TYPE_PERSONAL,
                    company_id=None,
                ),
            )
            return cls.expand_effective_permission_ids(
                active_permissions=active_permissions,
                allow_ids=allow_ids,
                deny_ids=deny_ids,
            )

        if user.user_type == USER_TYPE_ENTERPRISE:
            if not user.company_id:
                return set()

            deny_ids = await cls._list_user_permission_ids(user.id, now, effect=PERMISSION_EFFECT_DENY)
            allow_ids = await cls._list_user_permission_ids(user.id, now, effect=PERMISSION_EFFECT_ALLOW)
            allow_ids.update(
                await cls._list_role_permission_ids(
                    user_id=user.id,
                    now=now,
                    role_scope=USER_TYPE_ENTERPRISE,
                    company_id=user.company_id,
                ),
            )

            if user.department_id:
                deny_ids.update(await cls._list_department_permission_ids(user.department_id, now, effect=PERMISSION_EFFECT_DENY))
                allow_ids.update(await cls._list_department_permission_ids(user.department_id, now, effect=PERMISSION_EFFECT_ALLOW))

            if user.subsidiary_id:
                deny_ids.update(await cls._list_subsidiary_permission_ids(user.subsidiary_id, now, effect=PERMISSION_EFFECT_DENY))
                allow_ids.update(await cls._list_subsidiary_permission_ids(user.subsidiary_id, now, effect=PERMISSION_EFFECT_ALLOW))

            return cls.expand_effective_permission_ids(
                active_permissions=active_permissions,
                allow_ids=allow_ids,
                deny_ids=deny_ids,
            )

        return set()

    @classmethod
    async def _list_user_permission_ids(cls, user_id: int, now, *, effect: str) -> set[int]:
        queryset = IamUserPermission.objects.filter(
            cls._valid_time_q(now),
            user_id=user_id,
            permission__status=1,
            effect=effect,
        ).values_list("permission_id", flat=True)
        return {item async for item in queryset}

    @classmethod
    async def _list_department_permission_ids(cls, department_id: int, now, *, effect: str) -> set[int]:
        queryset = IamDepartmentPermission.objects.filter(
            cls._valid_time_q(now),
            department_id=department_id,
            permission__status=1,
            effect=effect,
        ).values_list("permission_id", flat=True)
        return {item async for item in queryset}

    @classmethod
    async def _list_subsidiary_permission_ids(cls, subsidiary_id: int, now, *, effect: str) -> set[int]:
        queryset = IamSubsidiaryPermission.objects.filter(
            cls._valid_time_q(now),
            subsidiary_id=subsidiary_id,
            permission__status=1,
            effect=effect,
        ).values_list("permission_id", flat=True)
        return {item async for item in queryset}

    @classmethod
    async def _list_role_permission_ids(cls, *, user_id: int, now, role_scope: str, company_id: int | None) -> set[int]:
        role_filter = {
            "user_id": user_id,
            "role__status": 1,
            "role__role_scope": role_scope,
        }
        if role_scope == USER_TYPE_PERSONAL:
            role_filter["role__company_id__isnull"] = True
        elif company_id is not None:
            role_filter["role__company_id"] = company_id

        role_ids = IamUserRole.objects.filter(**role_filter).values("role_id")
        queryset = IamRolePermission.objects.filter(cls._valid_time_q(now), role_id__in=role_ids, permission__status=1).values_list("permission_id", flat=True)
        return {item async for item in queryset}

    @classmethod
    def expand_effective_permission_ids(cls, *, active_permissions: list[dict], allow_ids: set[int], deny_ids: set[int]) -> set[int]:
        permission_map = {item["id"]: item for item in active_permissions}
        active_ids = set(permission_map.keys())
        normalized_allow = allow_ids & active_ids
        normalized_deny = deny_ids & active_ids

        effective_ids: set[int] = set()
        for permission_id in active_ids:
            chain_ids = cls.get_permission_chain_ids(permission_id=permission_id, permission_map=permission_map)
            if any(chain_id in normalized_deny for chain_id in chain_ids):
                continue
            if any(chain_id in normalized_allow for chain_id in chain_ids):
                effective_ids.add(permission_id)

        return effective_ids

    @classmethod
    def get_permission_chain_ids(cls, *, permission_id: int, permission_map: dict[int, dict]) -> list[int]:
        chain_ids: list[int] = []
        visited_ids: set[int] = set()
        current_id = permission_id

        for _ in range(cls.MAX_ANCESTOR_DEPTH):
            if current_id in visited_ids:
                break

            permission = permission_map.get(current_id)
            if not permission:
                break

            visited_ids.add(current_id)
            chain_ids.append(current_id)

            parent_id = permission.get("parent_id")
            if not parent_id:
                break

            current_id = parent_id

        return chain_ids

    @staticmethod
    def build_menu_tree(permissions: list[dict], allowed_ids: set[int]) -> list[dict]:
        menu_permissions = {
            item["id"]: item
            for item in permissions
            if item.get("permission_type") == "MENU"
        }

        included_ids = {item_id for item_id in allowed_ids if item_id in menu_permissions}

        for permission_id in list(included_ids):
            current_id = permission_id
            visited_chain: set[int] = set()

            while current_id in menu_permissions and current_id not in visited_chain:
                visited_chain.add(current_id)
                parent_id = menu_permissions[current_id].get("parent_id")
                if not parent_id or parent_id not in menu_permissions:
                    break
                included_ids.add(parent_id)
                current_id = parent_id

        if not included_ids:
            return []

        children_map: dict[int, list[int]] = {}
        for node_id in included_ids:
            parent_id = menu_permissions[node_id].get("parent_id")
            if parent_id in included_ids and parent_id != node_id:
                children_map.setdefault(parent_id, []).append(node_id)

        root_ids = [
            node_id
            for node_id in included_ids
            if menu_permissions[node_id].get("parent_id") not in included_ids
               or menu_permissions[node_id].get("parent_id") == node_id
        ]

        built_ids: set[int] = set()

        def build_node(_node_id: int, path_ids: set[int]) -> dict:
            built_ids.add(_node_id)
            node = menu_permissions[_node_id]
            child_items: list[dict] = []

            next_path_ids = set(path_ids)
            next_path_ids.add(_node_id)

            child_ids = sorted(
                children_map.get(_node_id, []),
                key=lambda _child_id: menu_permissions[_child_id]["permission_code"],
            )
            for child_id in child_ids:
                if child_id in next_path_ids:
                    continue
                child_items.append(build_node(child_id, next_path_ids))

            return {
                "id": node["id"],
                "code": node["permission_code"],
                "name": node["permission_name"],
                "children": child_items,
            }

        tree: list[dict] = []
        for root_id in sorted(root_ids, key=lambda item_id: menu_permissions[item_id]["permission_code"]):
            tree.append(build_node(root_id, set()))

        remaining_ids = sorted(
            [node_id for node_id in included_ids if node_id not in built_ids],
            key=lambda item_id: menu_permissions[item_id]["permission_code"],
        )
        for node_id in remaining_ids:
            tree.append(build_node(node_id, set()))

        return tree


class DataScopeService:
    @staticmethod
    def _valid_time_q(now):
        return Q(expired_at__isnull=True) | Q(expired_at__gt=now)

    @classmethod
    async def resolve_scope(cls, *, user, permission_code: str) -> DataScopeResult:
        if not user or not bool(getattr(user, "is_active", False)):
            return DataScopePolicy.denied_result()

        if not permission_code:
            return DataScopePolicy.denied_result()

        if bool(getattr(user, "is_superuser", False)):
            return DataScopePolicy.platform_all_result()

        permission_ids = await PermissionService.get_active_permission_ids_with_ancestors(permission_code)
        if not permission_ids:
            return DataScopePolicy.denied_result()

        now = timezone.now()

        if user.user_type == USER_TYPE_PERSONAL:
            return await cls._resolve_personal_scope(user=user, permission_ids=permission_ids, now=now)

        if user.user_type == USER_TYPE_ENTERPRISE:
            return await cls._resolve_enterprise_scope(user=user, permission_ids=permission_ids, now=now)

        return DataScopePolicy.denied_result()

    @classmethod
    async def _resolve_personal_scope(cls, *, user, permission_ids: list[int], now) -> DataScopeResult:
        if await cls._has_direct_effect(IamUserPermission, subject_field="user_id", subject_id=user.id, permission_ids=permission_ids, effect=PERMISSION_EFFECT_DENY, now=now):
            return DataScopePolicy.denied_result()

        scopes: list[str] = []
        scopes.extend(await cls._list_user_scopes(user.id, permission_ids, now))
        scopes.extend(await cls._list_role_scopes(user.id, permission_ids, now, role_scope=USER_TYPE_PERSONAL, company_id=None))

        if not scopes:
            return DataScopePolicy.denied_result()

        scope = DataScopePolicy.normalize_personal_scope(scopes)
        return DataScopePolicy.build_result_for_user(user=user, scope=scope)

    @classmethod
    async def _resolve_enterprise_scope(cls, *, user, permission_ids: list[int], now) -> DataScopeResult:
        if not user.company_id:
            return DataScopePolicy.denied_result()

        if await cls._has_direct_effect(IamUserPermission, subject_field="user_id", subject_id=user.id, permission_ids=permission_ids, effect=PERMISSION_EFFECT_DENY, now=now):
            return DataScopePolicy.denied_result()

        if user.department_id and await cls._has_direct_effect(
                IamDepartmentPermission,
                subject_field="department_id",
                subject_id=user.department_id,
                permission_ids=permission_ids,
                effect=PERMISSION_EFFECT_DENY,
                now=now,
        ):
            return DataScopePolicy.denied_result()

        if user.subsidiary_id and await cls._has_direct_effect(
                IamSubsidiaryPermission,
                subject_field="subsidiary_id",
                subject_id=user.subsidiary_id,
                permission_ids=permission_ids,
                effect=PERMISSION_EFFECT_DENY,
                now=now,
        ):
            return DataScopePolicy.denied_result()

        scopes: list[str] = []
        scopes.extend(await cls._list_user_scopes(user.id, permission_ids, now))
        scopes.extend(await cls._list_role_scopes(user.id, permission_ids, now, role_scope=USER_TYPE_ENTERPRISE, company_id=user.company_id))

        if user.department_id:
            scopes.extend(await cls._list_department_scopes(user.department_id, permission_ids, now))

        if user.subsidiary_id:
            scopes.extend(await cls._list_subsidiary_scopes(user.subsidiary_id, permission_ids, now))

        scope = DataScopePolicy.select_max_scope(scopes)
        if not scope:
            return DataScopePolicy.denied_result()

        if scope == DATA_SCOPE_DEPARTMENT_TREE:
            department_ids = await cls._get_descendant_department_ids(company_id=user.company_id, department_id=user.department_id)
            return DataScopePolicy.build_result_for_user(user=user, scope=scope, department_ids=department_ids)

        return DataScopePolicy.build_result_for_user(user=user, scope=scope)

    @classmethod
    async def _has_direct_effect(cls, model_class, *, subject_field: str, subject_id: int, permission_ids: list[int], effect: str, now) -> bool:
        return await model_class.objects.filter(
            cls._valid_time_q(now),
            **{subject_field: subject_id},
            permission_id__in=permission_ids,
            permission__status=1,
            effect=effect,
        ).aexists()

    @classmethod
    async def _list_user_scopes(cls, user_id: int, permission_ids: list[int], now) -> list[str]:
        queryset = IamUserPermission.objects.filter(
            cls._valid_time_q(now),
            user_id=user_id,
            permission_id__in=permission_ids,
            permission__status=1,
            effect=PERMISSION_EFFECT_ALLOW,
        ).exclude(data_scope__isnull=True).values_list("data_scope", flat=True)
        return [item async for item in queryset if item]

    @classmethod
    async def _list_department_scopes(cls, department_id: int, permission_ids: list[int], now) -> list[str]:
        queryset = IamDepartmentPermission.objects.filter(
            cls._valid_time_q(now),
            department_id=department_id,
            permission_id__in=permission_ids,
            permission__status=1,
            effect=PERMISSION_EFFECT_ALLOW,
        ).exclude(data_scope__isnull=True).values_list("data_scope", flat=True)
        return [item async for item in queryset if item]

    @classmethod
    async def _list_subsidiary_scopes(cls, subsidiary_id: int, permission_ids: list[int], now) -> list[str]:
        queryset = IamSubsidiaryPermission.objects.filter(
            cls._valid_time_q(now),
            subsidiary_id=subsidiary_id,
            permission_id__in=permission_ids,
            permission__status=1,
            effect=PERMISSION_EFFECT_ALLOW,
        ).exclude(data_scope__isnull=True).values_list("data_scope", flat=True)
        return [item async for item in queryset if item]

    @classmethod
    async def _list_role_scopes(cls, user_id: int, permission_ids: list[int], now, *, role_scope: str, company_id: int | None) -> list[str]:
        role_filter = {
            "user_id": user_id,
            "role__status": 1,
            "role__role_scope": role_scope,
        }
        if role_scope == USER_TYPE_PERSONAL:
            role_filter["role__company_id__isnull"] = True
        elif company_id is not None:
            role_filter["role__company_id"] = company_id

        role_ids = IamUserRole.objects.filter(**role_filter).values("role_id")
        queryset = IamRolePermission.objects.filter(
            cls._valid_time_q(now),
            role_id__in=role_ids,
            permission_id__in=permission_ids,
            permission__status=1,
        ).exclude(data_scope__isnull=True).values_list("data_scope", flat=True)
        return [item async for item in queryset if item]

    @classmethod
    async def _get_descendant_department_ids(cls, *, company_id: int | None, department_id: int | None) -> list[int]:
        if not company_id or not department_id:
            return []

        seen: set[int] = {department_id}
        frontier: list[int] = [department_id]

        while frontier:
            queryset = IamDepartment.objects.filter(company_id=company_id, parent_id__in=frontier).values_list("id", flat=True)
            child_ids = [item async for item in queryset]

            next_frontier: list[int] = []
            for child_id in child_ids:
                if child_id in seen:
                    continue
                seen.add(child_id)
                next_frontier.append(child_id)

            frontier = next_frontier

        return list(seen)


class AuthContextService:
    @classmethod
    def build_profile(cls, user) -> dict:
        context = TenantService.from_user(user)
        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "display_name": user.display_name,
                "email": user.email,
                "phone": user.phone,
                "user_type": user.user_type,
                "company_id": user.company_id,
                "subsidiary_id": user.subsidiary_id,
                "department_id": user.department_id,
                "is_active": user.is_active,
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
            },
            "tenant": {
                "is_platform_admin": TenantPolicy.is_platform_admin(context),
                "is_enterprise_user": TenantPolicy.is_enterprise_user(context),
                "is_personal_user": TenantPolicy.is_personal_user(context),
                "company_id": context.company_id,
                "subsidiary_id": context.subsidiary_id,
                "department_id": context.department_id,
            },
        }

    @classmethod
    async def list_permission_codes(cls, user) -> list[str]:
        return await PermissionService.list_permission_codes(user)

    @classmethod
    async def list_menu_tree(cls, user) -> list[dict]:
        return await PermissionService.list_menu_tree(user)

    @classmethod
    async def list_data_scopes(cls, *, user, permission_codes: list[str]) -> list[dict]:
        if not user or not bool(getattr(user, "is_active", False)):
            return []

        items: list[dict] = []
        for permission_code in permission_codes:
            result = await DataScopeService.resolve_scope(user=user, permission_code=permission_code)
            items.append(
                {
                    "permission_code": permission_code,
                    "allowed": result.allowed,
                    "scope": result.scope,
                    "company_id": result.company_id,
                    "subsidiary_id": result.subsidiary_id,
                    "department_id": result.department_id,
                    "department_ids": list(result.department_ids),
                    "user_id": result.user_id,
                    "is_platform_scope": result.is_platform_scope,
                },
            )
        return items
