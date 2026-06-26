# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    ClassVar,
    TYPE_CHECKING,
)

from asgiref.sync import sync_to_async
from django.contrib.auth.hashers import make_password
from django.utils import timezone

from backend.utils.password_transport import PasswordTransportService
from ns_backend.iam.constants import (
    PERMISSION_TYPE_ACTION,
    PERMISSION_TYPE_DATA,
    PERMISSION_TYPE_MENU,
    ROLE_SCOPE_ENTERPRISE,
    ROLE_SCOPE_PERSONAL,
    USER_TYPE_ENTERPRISE,
    USER_TYPE_PERSONAL,
)
from ns_backend.iam.errors import (
    IamInvalidRelationError,
    IamManagementAccessDeniedError,
    IamManagementRequestInvalidError,
    IamResourceAlreadyExistsError,
    IamResourceNotFoundError,
)
from ns_backend.iam.models import (
    IamCompany,
    IamDepartment,
    IamDepartmentPermission,
    IamPermission,
    IamResource,
    IamResourceAction,
    IamResourceRelation,
    IamRole,
    IamRolePermission,
    IamSubsidiary,
    IamSubsidiaryPermission,
    IamUser,
    IamUserPermission,
    IamUserRole
)
from ns_backend.iam.repositories import (
    IamManagementRepository,
    UserSessionRepository,
)
from ns_backend.iam.validators import (
    CompanyValidator,
    DepartmentPermissionValidator,
    DepartmentValidator,
    IamManagementValidator,
    PermissionValidator,
    ResourceActionValidator,
    ResourceRelationValidator,
    ResourceValidator,
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


class IamManagementService:
    model_class: ClassVar[Any] = None
    validator_class: ClassVar[type[IamManagementValidator]] = IamManagementValidator
    repository_class: ClassVar[type[IamManagementRepository]] = IamManagementRepository

    list_fields: ClassVar[tuple[str, ...]] = ()
    detail_fields: ClassVar[tuple[str, ...]] = ()
    filter_fields: ClassVar[tuple[str, ...]] = ()
    keyword_fields: ClassVar[tuple[str, ...]] = ()
    order_fields: ClassVar[tuple[str, ...]] = ("id",)

    unique_fields: ClassVar[tuple[str, ...]] = ()

    default_page_size = 20
    max_page_size = 200

    tenant_scope_field: ClassVar[str | None] = None
    tenant_create_field: ClassVar[str | None] = None

    enterprise_resource_required: ClassVar[bool] = False

    platform_create_only: ClassVar[bool] = False
    platform_update_only: ClassVar[bool] = False
    platform_delete_only: ClassVar[bool] = False

    @classmethod
    async def list_items(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        page = cls.parse_positive_int(
            value=data.get("page", 1),
            field="page",
            default=1,
        )
        page_size = cls.parse_positive_int(
            value=data.get("page_size", data.get("limit", cls.default_page_size)),
            field="page_size",
            default=cls.default_page_size,
        )

        if page_size > cls.max_page_size:
            page_size = cls.max_page_size

        filters = cls.apply_tenant_filters(
            filters=cls.build_filters(data=data),
            operator=operator,
        )
        keyword_conditions = cls.build_keyword_conditions(data=data)
        order_by = cls.build_order_by(data=data)

        return await cls.repository_class.list_items(
            model_class=cls.model_class,
            fields=cls.list_fields,
            page=page,
            page_size=page_size,
            filters=filters,
            keyword_conditions=keyword_conditions,
            order_by=order_by,
        )

    @classmethod
    async def list_all_items_for_operator(cls, *, data: dict[str, Any], operator: Any, fields: tuple[str, ...] | None = None, extra_filters: dict[str, Any] | None = None, default_order_by: tuple[str, ...] | None = None) -> list[dict[str, Any]]:
        filters = cls.build_filters(data=data)

        if extra_filters:
            filters.update(extra_filters)

        filters = cls.apply_tenant_filters(
            filters=filters,
            operator=operator,
        )

        keyword_conditions = cls.build_keyword_conditions(data=data)

        if data.get("order_by") or data.get("ordering"):
            order_by = cls.build_order_by(data=data)
        else:
            order_by = default_order_by or ("id",)

        return await cls.repository_class.list_all_items(
            model_class=cls.model_class,
            fields=fields or cls.detail_fields,
            filters=filters,
            keyword_conditions=keyword_conditions,
            order_by=order_by,
        )

    @classmethod
    async def detail_item(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        item_id = cls.get_required_id(data=data)

        await cls.ensure_item_accessible(
            item_id=item_id,
            operator=operator,
        )

        item = await cls.repository_class.detail_item(
            model_class=cls.model_class,
            item_id=item_id,
            fields=cls.detail_fields,
        )

        if item is None:
            raise IamResourceNotFoundError(
                details={
                    "model": cls.model_class.__name__,
                    "id": item_id,
                },
            )

        return item

    @classmethod
    async def create_item(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        cls.ensure_platform_operation_allowed(
            action_name="create",
            operator=operator,
        )

        prepared_data = cls.prepare_create_data_for_operator(
            data=data,
            operator=operator,
        )
        validated_data = cls.validator_class.validate_create(prepared_data)

        await cls.validate_create_business_rules(
            data=validated_data,
            operator=operator,
        )
        await cls.validate_unique_fields(
            data=validated_data,
            exclude_id=None,
        )

        return await cls.repository_class.create_item(
            model_class=cls.model_class,
            data=validated_data,
            fields=cls.detail_fields,
            operator_id=cls.get_operator_id(operator),
        )

    @classmethod
    async def update_item(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        cls.ensure_platform_operation_allowed(
            action_name="update",
            operator=operator,
        )

        item_id = cls.get_required_id(data=data)

        await cls.ensure_item_accessible(
            item_id=item_id,
            operator=operator,
        )

        prepared_data = cls.prepare_update_data_for_operator(
            data=data,
            operator=operator,
        )
        validated_data = cls.validator_class.validate_update(prepared_data)

        existing_item = await cls.repository_class.get_by_id(
            model_class=cls.model_class,
            item_id=item_id,
        )

        if existing_item is None:
            raise IamResourceNotFoundError(
                details={
                    "model": cls.model_class.__name__,
                    "id": item_id,
                },
            )

        await cls.validate_update_business_rules(
            item=existing_item,
            data=validated_data,
            operator=operator,
        )
        await cls.validate_unique_fields(
            data=validated_data,
            exclude_id=item_id,
        )

        item = await cls.repository_class.update_item(
            model_class=cls.model_class,
            item_id=item_id,
            data=validated_data,
            fields=cls.detail_fields,
            operator_id=cls.get_operator_id(operator),
        )

        if item is None:
            raise IamResourceNotFoundError(
                details={
                    "model": cls.model_class.__name__,
                    "id": item_id,
                },
            )

        return item

    @classmethod
    async def delete_item(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        item_id = cls.get_required_id(data=data)

        cls.ensure_platform_operation_allowed(
            action_name="delete",
            operator=operator,
        )

        await cls.ensure_item_accessible(
            item_id=item_id,
            operator=operator,
        )

        existing_item = await cls.repository_class.get_by_id(
            model_class=cls.model_class,
            item_id=item_id,
        )

        if existing_item is None:
            raise IamResourceNotFoundError(
                details={
                    "model": cls.model_class.__name__,
                    "id": item_id,
                },
            )

        await cls.validate_delete_business_rules(
            item=existing_item,
            operator=operator,
        )

        deleted = await cls.repository_class.delete_item(
            model_class=cls.model_class,
            item_id=item_id,
        )

        if not deleted:
            raise IamResourceNotFoundError(
                details={
                    "model": cls.model_class.__name__,
                    "id": item_id,
                },
            )

        return {
            "id": item_id,
            "deleted": True,
        }

    @classmethod
    async def validate_create_business_rules(cls, *, data: dict[str, Any], operator: Any) -> None:
        return None

    @classmethod
    async def validate_update_business_rules(cls, *, item: Any, data: dict[str, Any], operator: Any) -> None:
        return None

    @classmethod
    async def validate_delete_business_rules(cls, *, item: Any, operator: Any) -> None:
        return None

    @classmethod
    async def validate_unique_fields(cls, *, data: dict[str, Any], exclude_id: int | None) -> None:
        for field in cls.unique_fields:
            value = data.get(field)
            if value in (None, ""):
                continue

            exists = await cls.repository_class.exists_by_filters(
                model_class=cls.model_class,
                filters={
                    field: value,
                },
                exclude_id=exclude_id,
            )

            if exists:
                raise IamResourceAlreadyExistsError(
                    details={
                        "model": cls.model_class.__name__,
                        "field": field,
                        "value": value,
                    },
                )

    @classmethod
    def build_filters(cls, *, data: dict[str, Any]) -> dict[str, Any]:
        raw_filters = data.get("filters")

        if raw_filters is None:
            raw_filters = {}
        elif not isinstance(raw_filters, dict):
            raise IamManagementRequestInvalidError(
                "filters must be an object.",
            )

        filters = dict(raw_filters)

        # 允许前端在 list 请求中直接把白名单过滤字段放在顶层。
        for field in cls.filter_fields:
            if field in data and field not in filters:
                filters[field] = data[field]

        return cls.validator_class.validate_filter(
            filters,
            allowed_fields=cls.filter_fields,
        )

    @classmethod
    def build_keyword_conditions(cls, *, data: dict[str, Any]) -> list[dict[str, Any]]:
        raw_keyword = data.get("keyword", data.get("search"))

        if raw_keyword in (None, ""):
            return []

        keyword = str(raw_keyword).strip()
        if not keyword:
            return []

        return [
            {
                f"{field}__icontains": keyword,
            }
            for field in cls.keyword_fields
        ]

    @classmethod
    def build_order_by(cls, *, data: dict[str, Any]) -> tuple[str, ...]:
        raw_order_by = data.get("order_by", data.get("ordering"))

        if raw_order_by in (None, ""):
            return ("-id",)

        if isinstance(raw_order_by, str):
            raw_items = [
                item.strip()
                for item in raw_order_by.split(",")
            ]
        elif isinstance(raw_order_by, (list, tuple)):
            raw_items = [
                str(item).strip()
                for item in raw_order_by
            ]
        else:
            raise IamManagementRequestInvalidError(
                "order_by must be a string or list.",
            )

        allowed_order_fields = set(cls.order_fields)
        order_items: list[str] = []

        for item in raw_items:
            if not item:
                continue

            field_name = item[1:] if item.startswith("-") else item
            if field_name not in allowed_order_fields:
                raise IamManagementRequestInvalidError(
                    "Ordering field is not allowed.",
                    details={
                        "field": field_name,
                        "allowed_fields": sorted(allowed_order_fields),
                    },
                )

            order_items.append(item)

        return tuple(order_items) if order_items else ("-id",)

    @classmethod
    def get_required_id(cls, *, data: dict[str, Any]) -> int:
        raw_id = data.get("id", data.get("item_id"))
        return cls.parse_positive_int(
            value=raw_id,
            field="id",
            default=None,
        )

    @staticmethod
    def parse_positive_int(*, value: Any, field: str, default: int | None) -> int:
        if value in (None, ""):
            if default is not None:
                return default

            raise IamManagementRequestInvalidError(
                "ID field cannot be empty.",
                details={
                    "field": field,
                },
            )

        try:
            normalized = int(value)
        except (TypeError, ValueError) as exc:
            raise IamManagementRequestInvalidError(
                "Integer field has invalid format.",
                details={
                    "field": field,
                },
            ) from exc

        if normalized <= 0:
            raise IamManagementRequestInvalidError(
                "Integer field must be positive.",
                details={
                    "field": field,
                    "value": normalized,
                },
            )

        return normalized

    @staticmethod
    def get_operator_id(operator: Any) -> int | None:
        operator_id = getattr(operator, "id", None)

        if isinstance(operator_id, int):
            return operator_id

        return None

    @classmethod
    def ensure_platform_operation_allowed(cls, *, action_name: str, operator: Any) -> None:
        action_flag_map = {
            "create": cls.platform_create_only,
            "update": cls.platform_update_only,
            "delete": cls.platform_delete_only,
        }

        if not action_flag_map.get(action_name, False):
            return

        if cls.operator_is_superuser(operator):
            return

        raise IamManagementAccessDeniedError(
            "Only platform superuser can perform this IAM management operation.",
            details={
                "model": cls.model_class.__name__,
                "action": action_name,
            },
        )

    @classmethod
    def prepare_create_data_for_operator(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        create_data = dict(data)

        if not cls.tenant_create_field:
            return create_data

        if cls.operator_is_superuser(operator):
            return create_data

        company_id = cls.get_operator_company_id_or_raise(operator)

        raw_company_id = create_data.get(cls.tenant_create_field)
        if raw_company_id not in (None, ""):
            requested_company_id = cls.normalize_company_id(raw_company_id)
            if requested_company_id != company_id:
                raise IamManagementAccessDeniedError(
                    "Cannot create IAM resource for another company.",
                    details={
                        "field": cls.tenant_create_field,
                        "operator_company_id": company_id,
                        "request_company_id": requested_company_id,
                    },
                )

        create_data[cls.tenant_create_field] = company_id
        return create_data

    @classmethod
    def prepare_update_data_for_operator(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        return dict(data)

    @classmethod
    def apply_tenant_filters(cls, *, filters: dict[str, Any], operator: Any) -> dict[str, Any]:
        tenant_filters = cls.build_tenant_filters(operator=operator)

        if not tenant_filters:
            return filters

        result = dict(filters)

        for field, value in tenant_filters.items():
            current_value = result.get(field)

            if current_value not in (None, ""):
                normalized_current_value = cls.normalize_company_id(current_value)

                if normalized_current_value != value:
                    raise IamManagementAccessDeniedError(
                        "Cannot query IAM resource from another company.",
                        details={
                            "field": field,
                            "operator_value": value,
                            "request_value": current_value,
                        },
                    )

            result[field] = value

        return result

    @classmethod
    def build_tenant_filters(cls, *, operator: Any) -> dict[str, Any]:
        if not cls.tenant_scope_field:
            return {}

        return cls.build_company_boundary_filter(
            scope_field=cls.tenant_scope_field,
            operator=operator,
        )

    @classmethod
    def build_company_boundary_filter(cls, *, scope_field: str, operator: Any) -> dict[str, Any]:
        if cls.operator_is_superuser(operator):
            return {}

        company_id = cls.get_operator_company_id_or_raise(operator)

        return {
            scope_field: company_id,
        }

    @classmethod
    async def ensure_item_accessible(cls, *, item_id: int, operator: Any) -> None:
        tenant_filters = cls.build_tenant_filters(operator=operator)

        if not tenant_filters:
            return

        exists = await cls.repository_class.exists_by_filters(
            model_class=cls.model_class,
            filters={
                "id": item_id,
                **tenant_filters,
            },
            exclude_id=None,
        )

        if exists:
            return

        raise IamResourceNotFoundError(
            details={
                "model": cls.model_class.__name__,
                "id": item_id,
            },
        )

    @classmethod
    async def ensure_model_item_company_access(cls, *, model_class: Any, item_id: int, scope_field: str, operator: Any, label: str) -> None:
        tenant_filters = cls.build_company_boundary_filter(
            scope_field=scope_field,
            operator=operator,
        )

        if not tenant_filters:
            return

        exists = await cls.repository_class.exists_by_filters(
            model_class=model_class,
            filters={
                "id": item_id,
                **tenant_filters,
            },
            exclude_id=None,
        )

        if exists:
            return

        raise IamManagementAccessDeniedError(
            f"Cannot operate {label} from another company.",
            details={
                "model": model_class.__name__,
                "id": item_id,
                "scope_field": scope_field,
            },
        )

    @classmethod
    def get_operator_company_id_or_raise(cls, operator: Any) -> int:
        if cls.enterprise_resource_required and not cls.operator_is_enterprise_user(operator):
            raise IamManagementAccessDeniedError(
                "Personal users cannot access enterprise IAM resources.",
                details={
                    "model": cls.model_class.__name__,
                    "operator_user_type": getattr(operator, "user_type", None),
                },
            )

        if not cls.operator_is_enterprise_user(operator):
            raise IamManagementAccessDeniedError(
                "Operator must be an enterprise user.",
                details={
                    "model": cls.model_class.__name__,
                    "operator_user_type": getattr(operator, "user_type", None),
                },
            )

        company_id = getattr(operator, "company_id", None)
        if company_id in (None, ""):
            raise IamManagementAccessDeniedError(
                "Enterprise user is not bound to company.",
                details={
                    "operator_id": getattr(operator, "id", None),
                },
            )

        return cls.normalize_company_id(company_id)

    @staticmethod
    def normalize_company_id(value: Any) -> int:
        try:
            company_id = int(value)
        except (TypeError, ValueError) as exc:
            raise IamManagementRequestInvalidError(
                "company_id has invalid format.",
                details={
                    "company_id": value,
                },
            ) from exc

        if company_id <= 0:
            raise IamManagementRequestInvalidError(
                "company_id must be positive.",
                details={
                    "company_id": company_id,
                },
            )

        return company_id

    @staticmethod
    def operator_is_superuser(operator: Any) -> bool:
        return getattr(operator, "is_superuser", 0) in (
            True,
            1,
            "1",
        )

    @staticmethod
    def operator_is_enterprise_user(operator: Any) -> bool:
        return getattr(operator, "user_type", None) == USER_TYPE_ENTERPRISE


class CompanyManagementService(IamManagementService):
    model_class = IamCompany
    validator_class = CompanyValidator

    list_fields = detail_fields = (
        "id",
        "company_code",
        "company_name",
        "legal_name",
        "status",
    )
    filter_fields = (
        "id",
        "company_code",
        "company_name",
        "legal_name",
        "status",
    )
    keyword_fields = (
        "company_code",
        "company_name",
        "legal_name",
    )
    order_fields = (
        "id",
        "company_code",
        "company_name",
        "status",
        "created_at",
        "updated_at",
    )
    unique_fields = (
        "company_code",
    )
    tenant_scope_field = "id"
    tenant_create_field = None
    enterprise_resource_required = True
    platform_create_only = True
    platform_delete_only = True

    @classmethod
    async def tree_items(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        companies = await cls.list_all_items_for_operator(
            data=data,
            operator=operator,
            default_order_by=(
                "company_code",
                "id",
            ),
        )

        if not companies:
            return {
                "tree": [],
                "total": 0,
            }

        company_ids = [
            item["id"]
            for item in companies
            if isinstance(item.get("id"), int)
        ]

        subsidiaries = await SubsidiaryManagementService.list_all_items_for_operator(
            data={},
            operator=operator,
            extra_filters={
                "company_id__in": company_ids,
            },
            default_order_by=(
                "company_id",
                "subsidiary_code",
                "id",
            ),
        )

        departments = await DepartmentManagementService.list_all_items_for_operator(
            data={},
            operator=operator,
            extra_filters={
                "company_id__in": company_ids,
            },
            default_order_by=(
                "company_id",
                "subsidiary_id",
                "parent_id",
                "department_code",
                "id",
            ),
        )

        return {
            "tree": cls.build_company_tree(
                companies=companies,
                subsidiaries=subsidiaries,
                departments=departments,
            ),
            "total": len(companies),
        }

    @classmethod
    async def org_tree_items(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        return await cls.tree_items(
            data=data,
            operator=operator,
        )

    @classmethod
    def build_company_tree(cls, *, companies: list[dict[str, Any]], subsidiaries: list[dict[str, Any]], departments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        subsidiaries_by_company: dict[int, list[dict[str, Any]]] = {}
        departments_by_company: dict[int, list[dict[str, Any]]] = {}

        for subsidiary in subsidiaries:
            company_id = subsidiary.get("company_id")
            if isinstance(company_id, int):
                subsidiaries_by_company.setdefault(company_id, []).append(subsidiary)

        for department in departments:
            company_id = department.get("company_id")
            if isinstance(company_id, int):
                departments_by_company.setdefault(company_id, []).append(department)

        tree: list[dict[str, Any]] = []

        for company in companies:
            company_id = company.get("id")
            if not isinstance(company_id, int):
                continue

            company_subsidiaries = subsidiaries_by_company.get(company_id, [])
            company_departments = departments_by_company.get(company_id, [])

            departments_by_subsidiary: dict[int | None, list[dict[str, Any]]] = {}

            for department in company_departments:
                subsidiary_id = department.get("subsidiary_id")
                if subsidiary_id is not None and not isinstance(subsidiary_id, int):
                    subsidiary_id = None

                departments_by_subsidiary.setdefault(subsidiary_id, []).append(department)

            company_node = {
                **company,
                "node_type": "COMPANY",
                "children": [],
            }

            for subsidiary in company_subsidiaries:
                subsidiary_id = subsidiary.get("id")
                if not isinstance(subsidiary_id, int):
                    continue

                company_node["children"].append(
                    {
                        **subsidiary,
                        "node_type": "SUBSIDIARY",
                        "children": DepartmentManagementService.build_department_tree(
                            departments_by_subsidiary.get(subsidiary_id, [])
                        ),
                    }
                )

            # 未绑定 subsidiary 的部门，直接挂在 company 下。
            company_node["children"].extend(
                DepartmentManagementService.build_department_tree(
                    departments_by_subsidiary.get(None, [])
                )
            )

            tree.append(company_node)

        return tree


class SubsidiaryManagementService(IamManagementService):
    model_class = IamSubsidiary
    validator_class = SubsidiaryValidator

    list_fields = detail_fields = (
        "id",
        "company_id",
        "subsidiary_code",
        "subsidiary_name",
        "status",
    )
    filter_fields = (
        "id",
        "company_id",
        "subsidiary_code",
        "subsidiary_name",
        "status",
    )
    keyword_fields = (
        "subsidiary_code",
        "subsidiary_name",
    )
    order_fields = (
        "id",
        "company_id",
        "subsidiary_code",
        "subsidiary_name",
        "status",
        "created_at",
        "updated_at",
    )
    unique_fields = (
        "subsidiary_code",
    )
    tenant_scope_field = "company_id"
    tenant_create_field = "company_id"
    enterprise_resource_required = True

    @classmethod
    async def validate_create_business_rules(cls, *, data: dict[str, Any], operator: Any) -> None:
        company_id = data.get("company_id")
        company = await cls.repository_class.get_by_id(
            model_class=IamCompany,
            item_id=company_id,
        )

        if company is None:
            raise IamInvalidRelationError(
                "Company does not exist.",
                details={
                    "company_id": company_id,
                },
            )

    @classmethod
    async def tree_items(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        subsidiaries = await cls.list_all_items_for_operator(
            data=data,
            operator=operator,
            default_order_by=(
                "company_id",
                "subsidiary_code",
                "id",
            ),
        )

        if not subsidiaries:
            return {
                "tree": [],
                "total": 0,
            }

        subsidiary_ids = [
            item["id"]
            for item in subsidiaries
            if isinstance(item.get("id"), int)
        ]

        departments = await DepartmentManagementService.list_all_items_for_operator(
            data={},
            operator=operator,
            extra_filters={
                "subsidiary_id__in": subsidiary_ids,
            },
            default_order_by=(
                "company_id",
                "subsidiary_id",
                "parent_id",
                "department_code",
                "id",
            ),
        )

        departments_by_subsidiary: dict[int, list[dict[str, Any]]] = {}

        for department in departments:
            subsidiary_id = department.get("subsidiary_id")
            if isinstance(subsidiary_id, int):
                departments_by_subsidiary.setdefault(subsidiary_id, []).append(department)

        tree: list[dict[str, Any]] = []

        for subsidiary in subsidiaries:
            subsidiary_id = subsidiary.get("id")
            if not isinstance(subsidiary_id, int):
                continue

            tree.append(
                {
                    **subsidiary,
                    "node_type": "SUBSIDIARY",
                    "children": DepartmentManagementService.build_department_tree(
                        departments_by_subsidiary.get(subsidiary_id, [])
                    ),
                }
            )

        return {
            "tree": tree,
            "total": len(subsidiaries),
        }


class DepartmentManagementService(IamManagementService):
    model_class = IamDepartment
    validator_class = DepartmentValidator

    list_fields = detail_fields = (
        "id",
        "company_id",
        "subsidiary_id",
        "parent_id",
        "department_code",
        "department_name",
        "status",
    )
    filter_fields = (
        "id",
        "company_id",
        "subsidiary_id",
        "parent_id",
        "department_code",
        "department_name",
        "status",
    )
    keyword_fields = (
        "department_code",
        "department_name",
    )
    order_fields = (
        "id",
        "company_id",
        "subsidiary_id",
        "parent_id",
        "department_code",
        "department_name",
        "status",
        "created_at",
        "updated_at",
    )
    unique_fields = (
        "department_code",
    )
    tenant_scope_field = "company_id"
    tenant_create_field = "company_id"
    enterprise_resource_required = True

    @classmethod
    async def validate_create_business_rules(cls, *, data: dict[str, Any], operator: Any) -> None:
        company_id = data.get("company_id")
        company = await cls.repository_class.get_by_id(
            model_class=IamCompany,
            item_id=company_id,
        )

        if company is None:
            raise IamInvalidRelationError(
                "Company does not exist.",
                details={
                    "company_id": company_id,
                },
            )

        subsidiary_id = data.get("subsidiary_id")
        if subsidiary_id is not None:
            subsidiary = await cls.repository_class.get_by_id(
                model_class=IamSubsidiary,
                item_id=subsidiary_id,
            )

            if subsidiary is None:
                raise IamInvalidRelationError(
                    "Subsidiary does not exist.",
                    details={
                        "subsidiary_id": subsidiary_id,
                    },
                )

            if subsidiary.company_id != company_id:
                raise IamInvalidRelationError(
                    "Subsidiary does not belong to company.",
                    details={
                        "company_id": company_id,
                        "subsidiary_id": subsidiary_id,
                    },
                )

        parent_id = data.get("parent_id")
        if parent_id is not None:
            parent = await cls.repository_class.get_by_id(
                model_class=IamDepartment,
                item_id=parent_id,
            )

            if parent is None:
                raise IamInvalidRelationError(
                    "Parent department does not exist.",
                    details={
                        "parent_id": parent_id,
                    },
                )

            if parent.company_id != company_id:
                raise IamInvalidRelationError(
                    "Parent department does not belong to company.",
                    details={
                        "company_id": company_id,
                        "parent_id": parent_id,
                    },
                )

    @classmethod
    async def tree_items(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        departments = await cls.list_all_items_for_operator(
            data=data,
            operator=operator,
            default_order_by=(
                "company_id",
                "subsidiary_id",
                "parent_id",
                "department_code",
                "id",
            ),
        )

        return {
            "tree": cls.build_department_tree(departments),
            "total": len(departments),
        }

    @classmethod
    def build_department_tree(cls, departments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not departments:
            return []

        node_map: dict[int, dict[str, Any]] = {}

        for department in departments:
            department_id = department.get("id")
            if not isinstance(department_id, int):
                continue

            node_map[department_id] = {
                **department,
                "node_type": "DEPARTMENT",
                "children": [],
            }

        if not node_map:
            return []

        children_map: dict[int, list[int]] = {}

        for node_id, node in node_map.items():
            parent_id = node.get("parent_id")

            if (
                    isinstance(parent_id, int)
                    and parent_id in node_map
                    and parent_id != node_id
            ):
                children_map.setdefault(parent_id, []).append(node_id)

        root_ids = [
            node_id
            for node_id, node in node_map.items()
            if node.get("parent_id") not in node_map
               or node.get("parent_id") == node_id
        ]

        if not root_ids:
            root_ids = list(node_map)

        def sort_key(_node_id: int) -> tuple[int, int, str, int]:
            _node = node_map[_node_id]
            company_id = _node.get("company_id")
            subsidiary_id = _node.get("subsidiary_id")
            return (
                company_id if isinstance(company_id, int) else 0,
                subsidiary_id if isinstance(subsidiary_id, int) else 0,
                str(_node.get("department_code") or ""),
                _node_id,
            )

        def build_node(_node_id: int, _path_ids: set[int]) -> dict[str, Any]:
            _node = {
                **node_map[_node_id],
                "children": [],
            }

            next_path_ids = set(_path_ids)
            next_path_ids.add(_node_id)

            for child_id in sorted(children_map.get(_node_id, []), key=sort_key):
                if child_id in next_path_ids:
                    continue

                _node["children"].append(
                    build_node(child_id, next_path_ids)
                )

            return _node

        tree: list[dict[str, Any]] = []
        built_root_ids: set[int] = set()

        for root_id in sorted(root_ids, key=sort_key):
            if root_id in built_root_ids:
                continue

            tree.append(
                build_node(root_id, set())
            )
            built_root_ids.add(root_id)

        return tree


class PermissionManagementService(IamManagementService):
    model_class = IamPermission
    validator_class = PermissionValidator

    list_fields = detail_fields = (
        "id",
        "permission_code",
        "permission_name",
        "permission_type",
        "parent_id",
        "status",
    )
    filter_fields = (
        "id",
        "permission_code",
        "permission_name",
        "permission_type",
        "parent_id",
        "status",
    )
    keyword_fields = (
        "permission_code",
        "permission_name",
    )
    order_fields = (
        "id",
        "permission_code",
        "permission_name",
        "permission_type",
        "parent_id",
        "status",
        "created_at",
        "updated_at",
    )
    unique_fields = (
        "permission_code",
    )

    @classmethod
    async def validate_create_business_rules(cls, *, data: dict[str, Any], operator: Any) -> None:
        parent_id = data.get("parent_id")
        if parent_id is None:
            return

        parent = await cls.repository_class.get_by_id(
            model_class=IamPermission,
            item_id=parent_id,
        )

        if parent is None:
            raise IamInvalidRelationError(
                "Parent permission does not exist.",
                details={
                    "parent_id": parent_id,
                },
            )

    @classmethod
    async def validate_update_business_rules(cls, *, item: Any, data: dict[str, Any], operator: Any) -> None:
        parent_id = data.get("parent_id")
        if parent_id is None:
            return

        item_id = getattr(item, "id", None)
        if parent_id == item_id:
            raise IamInvalidRelationError(
                "Permission cannot use itself as parent.",
                details={
                    "id": item_id,
                    "parent_id": parent_id,
                },
            )

        parent = await cls.repository_class.get_by_id(
            model_class=IamPermission,
            item_id=parent_id,
        )

        if parent is None:
            raise IamInvalidRelationError(
                "Parent permission does not exist.",
                details={
                    "parent_id": parent_id,
                },
            )

    @classmethod
    async def tree_items(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        items = await cls.list_all_permission_items(
            data=data,
            forced_permission_type=None,
        )

        return {
            "tree": cls.build_permission_tree(items),
            "total": len(items),
        }

    @classmethod
    async def menu_tree_items(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        items = await cls.list_all_permission_items(
            data=data,
            forced_permission_type=PERMISSION_TYPE_MENU,
        )

        return {
            "tree": cls.build_permission_tree(items),
            "total": len(items),
        }

    @classmethod
    async def action_items(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        items = await cls.list_all_permission_items(
            data=data,
            forced_permission_type=PERMISSION_TYPE_ACTION,
        )

        return {
            "items": items,
            "total": len(items),
        }

    @classmethod
    async def data_items(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        items = await cls.list_all_permission_items(
            data=data,
            forced_permission_type=PERMISSION_TYPE_DATA,
        )

        return {
            "items": items,
            "total": len(items),
        }

    @classmethod
    async def list_all_permission_items(cls, *, data: dict[str, Any], forced_permission_type: str | None) -> list[dict[str, Any]]:
        filters = cls.build_filters(data=data)

        if forced_permission_type is not None:
            filters["permission_type"] = forced_permission_type

        keyword_conditions = cls.build_keyword_conditions(data=data)

        if data.get("order_by") or data.get("ordering"):
            order_by = cls.build_order_by(data=data)
        else:
            order_by = (
                "permission_type",
                "permission_code",
                "id",
            )

        return await cls.repository_class.list_all_items(
            model_class=cls.model_class,
            fields=cls.detail_fields,
            filters=filters,
            keyword_conditions=keyword_conditions,
            order_by=order_by,
        )

    @classmethod
    def build_permission_tree(cls, items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not items:
            return []

        node_map: dict[int, dict[str, Any]] = {}

        for item in items:
            item_id = item.get("id")
            if not isinstance(item_id, int):
                continue

            node_map[item_id] = {
                **item,
                "children": [],
            }

        if not node_map:
            return []

        children_map: dict[int, list[int]] = {}

        for node_id, node in node_map.items():
            parent_id = node.get("parent_id")

            if (
                    isinstance(parent_id, int)
                    and parent_id in node_map
                    and parent_id != node_id
            ):
                children_map.setdefault(parent_id, []).append(node_id)

        root_ids = [
            node_id
            for node_id, node in node_map.items()
            if node.get("parent_id") not in node_map
               or node.get("parent_id") == node_id
        ]

        if not root_ids:
            root_ids = list(node_map)

        def sort_key(_node_id: int) -> tuple[str, str, int]:
            _node = node_map[_node_id]
            return (
                str(_node.get("permission_type") or ""),
                str(_node.get("permission_code") or ""),
                _node_id,
            )

        def build_node(_node_id: int, _path_ids: set[int]) -> dict[str, Any]:
            _node = {
                **node_map[_node_id],
                "children": [],
            }

            next_path_ids = set(_path_ids)
            next_path_ids.add(_node_id)

            for child_id in sorted(children_map.get(_node_id, []), key=sort_key):
                if child_id in next_path_ids:
                    continue

                _node["children"].append(
                    build_node(child_id, next_path_ids)
                )

            return _node

        tree: list[dict[str, Any]] = []
        built_root_ids: set[int] = set()

        for root_id in sorted(root_ids, key=sort_key):
            if root_id in built_root_ids:
                continue

            tree.append(
                build_node(root_id, set())
            )
            built_root_ids.add(root_id)

        return tree


class ResourceManagementService(IamManagementService):
    model_class = IamResource
    validator_class = ResourceValidator

    list_fields = detail_fields = (
        "id",
        "resource_type",
        "resource_name",
        "module_code",
        "access_mode",
        "status",
    )
    filter_fields = (
        "id",
        "resource_type",
        "resource_name",
        "module_code",
        "access_mode",
        "status",
    )
    keyword_fields = (
        "resource_type",
        "resource_name",
        "module_code",
    )
    order_fields = (
        "id",
        "resource_type",
        "resource_name",
        "module_code",
        "access_mode",
        "status",
        "created_at",
        "updated_at",
    )
    unique_fields = (
        "resource_type",
    )

    @classmethod
    async def detail_item(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        item = await super().detail_item(
            data=data,
            operator=operator,
        )

        item["actions"] = await ResourceActionManagementService.list_actions_by_resource_id(
            resource_id=item["id"],
        )

        return item

    @classmethod
    async def list_items(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        result = await super().list_items(
            data=data,
            operator=operator,
        )

        items = result.get("items", [])
        resource_ids = [
            item["id"]
            for item in items
            if isinstance(item.get("id"), int)
        ]

        action_rows = await ResourceActionManagementService.list_actions_by_resource_ids(
            resource_ids=resource_ids,
        )

        action_map: dict[int, list[dict[str, Any]]] = {}
        for action in action_rows:
            resource_id = action.get("resource_id")
            if isinstance(resource_id, int):
                action_map.setdefault(resource_id, []).append(action)

        for item in items:
            resource_id = item.get("id")
            if isinstance(resource_id, int):
                item["actions"] = action_map.get(resource_id, [])

        return result

    @classmethod
    async def validate_delete_business_rules(cls, *, item: Any, operator: Any) -> None:
        has_actions = await cls.repository_class.exists_by_filters(
            model_class=IamResourceAction,
            filters={
                "resource_id": item.id,
            },
            exclude_id=None,
        )

        if has_actions:
            raise IamInvalidRelationError(
                "Resource has actions and cannot be deleted.",
                details={
                    "resource_id": item.id,
                },
            )


class ResourceActionManagementService(IamManagementService):
    model_class = IamResourceAction
    validator_class = ResourceActionValidator

    list_fields = detail_fields = (
        "id",
        "resource_id",
        "action_code",
        "action_name",
        "status",
    )
    filter_fields = (
        "id",
        "resource_id",
        "action_code",
        "action_name",
        "status",
    )
    keyword_fields = (
        "action_code",
        "action_name",
    )
    order_fields = (
        "id",
        "resource_id",
        "action_code",
        "action_name",
        "status",
        "created_at",
        "updated_at",
    )

    @classmethod
    async def validate_create_business_rules(cls, *, data: dict[str, Any], operator: Any) -> None:
        resource_id = data.get("resource_id")

        resource = await cls.repository_class.get_by_id(
            model_class=IamResource,
            item_id=resource_id,
        )

        if resource is None:
            raise IamInvalidRelationError(
                "Resource does not exist.",
                details={
                    "resource_id": resource_id,
                },
            )

        exists = await cls.repository_class.exists_by_filters(
            model_class=IamResourceAction,
            filters={
                "resource_id": resource_id,
                "action_code": data.get("action_code"),
            },
            exclude_id=None,
        )

        if exists:
            raise IamResourceAlreadyExistsError(
                details={
                    "model": cls.model_class.__name__,
                    "fields": [
                        "resource_id",
                        "action_code",
                    ],
                    "resource_id": resource_id,
                    "action_code": data.get("action_code"),
                },
            )

    @classmethod
    async def validate_update_business_rules(cls, *, item: Any, data: dict[str, Any], operator: Any) -> None:
        return None

    @classmethod
    async def list_actions_by_resource_id(cls, *, resource_id: int) -> list[dict[str, Any]]:
        return await cls.list_actions_by_resource_ids(
            resource_ids=[
                resource_id
            ],
        )

    @classmethod
    async def list_actions_by_resource_ids(cls, *, resource_ids: list[int]) -> list[dict[str, Any]]:
        if not resource_ids:
            return []

        return await cls.repository_class.list_all_items(
            model_class=cls.model_class,
            fields=cls.detail_fields,
            filters={
                "resource_id__in": resource_ids,
            },
            keyword_conditions=[],
            order_by=(
                "resource_id",
                "action_code",
                "id",
            ),
        )


class ResourceRelationManagementService(IamManagementService):
    model_class = IamResourceRelation
    validator_class = ResourceRelationValidator

    list_fields = detail_fields = (
        "id",
        "resource_type",
        "resource_id",
        "parent_resource_type",
        "parent_resource_id",
        "relation_type",
    )
    filter_fields = (
        "id",
        "resource_type",
        "resource_id",
        "parent_resource_type",
        "parent_resource_id",
        "relation_type",
    )
    keyword_fields = (
        "resource_type",
        "resource_id",
        "parent_resource_type",
        "parent_resource_id",
    )
    order_fields = (
        "id",
        "resource_type",
        "resource_id",
        "parent_resource_type",
        "parent_resource_id",
        "relation_type",
        "created_at",
        "updated_at",
    )

    @classmethod
    async def validate_create_business_rules(cls, *, data: dict[str, Any], operator: Any) -> None:
        resource_type = data.get("resource_type")
        resource_id = data.get("resource_id")
        parent_resource_type = data.get("parent_resource_type")
        parent_resource_id = data.get("parent_resource_id")

        if resource_type == parent_resource_type and resource_id == parent_resource_id:
            raise IamInvalidRelationError(
                "Resource cannot inherit from itself.",
                details={
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                },
            )

        resource_exists = await cls.repository_class.exists_by_filters(
            model_class=IamResource,
            filters={
                "resource_type": resource_type,
            },
            exclude_id=None,
        )

        if not resource_exists:
            raise IamInvalidRelationError(
                "Resource type does not exist.",
                details={
                    "resource_type": resource_type,
                },
            )

        parent_resource_exists = await cls.repository_class.exists_by_filters(
            model_class=IamResource,
            filters={
                "resource_type": parent_resource_type,
            },
            exclude_id=None,
        )

        if not parent_resource_exists:
            raise IamInvalidRelationError(
                "Parent resource type does not exist.",
                details={
                    "parent_resource_type": parent_resource_type,
                },
            )

        exists = await cls.repository_class.exists_by_filters(
            model_class=IamResourceRelation,
            filters={
                "resource_type": resource_type,
                "resource_id": resource_id,
                "parent_resource_type": parent_resource_type,
                "parent_resource_id": parent_resource_id,
            },
            exclude_id=None,
        )

        if exists:
            raise IamResourceAlreadyExistsError(
                details={
                    "model": cls.model_class.__name__,
                    "resource_type": resource_type,
                    "resource_id": resource_id,
                    "parent_resource_type": parent_resource_type,
                    "parent_resource_id": parent_resource_id,
                },
            )


class RoleManagementService(IamManagementService):
    model_class = IamRole
    validator_class = RoleValidator

    list_fields = detail_fields = (
        "id",
        "role_code",
        "role_name",
        "role_scope",
        "company_id",
        "status",
    )
    filter_fields = (
        "id",
        "role_code",
        "role_name",
        "role_scope",
        "company_id",
        "status",
    )
    keyword_fields = (
        "role_code",
        "role_name",
    )
    order_fields = (
        "id",
        "role_code",
        "role_name",
        "role_scope",
        "company_id",
        "status",
        "created_at",
        "updated_at",
    )

    unique_fields = ()
    tenant_scope_field = "company_id"
    tenant_create_field = None

    @classmethod
    async def validate_create_business_rules(cls, *, data: dict[str, Any], operator: Any) -> None:
        role_scope = data.get("role_scope")
        company_id = data.get("company_id")

        if role_scope == ROLE_SCOPE_PERSONAL:
            if company_id is not None:
                raise IamInvalidRelationError(
                    "Personal role must not bind to company.",
                    details={
                        "role_scope": role_scope,
                        "company_id": company_id,
                    },
                )
            return

        if role_scope == ROLE_SCOPE_ENTERPRISE:
            if company_id is None:
                raise IamInvalidRelationError(
                    "Enterprise role must bind to company.",
                    details={
                        "role_scope": role_scope,
                    },
                )

            company = await cls.repository_class.get_by_id(
                model_class=IamCompany,
                item_id=company_id,
            )

            if company is None:
                raise IamInvalidRelationError(
                    "Company does not exist.",
                    details={
                        "company_id": company_id,
                    },
                )
            return

        raise IamInvalidRelationError(
            "Role scope is invalid.",
            details={
                "role_scope": role_scope,
            },
        )

    @classmethod
    async def validate_unique_fields(cls, *, data: dict[str, Any], exclude_id: int | None) -> None:
        role_code = data.get("role_code")
        role_scope = data.get("role_scope")
        company_id = data.get("company_id")

        if role_code in (None, "") or role_scope in (None, ""):
            return

        exists = await cls.repository_class.exists_by_filters(
            model_class=cls.model_class,
            filters={
                "role_code": role_code,
                "role_scope": role_scope,
                "company_id": company_id,
            },
            exclude_id=exclude_id,
        )

        if exists:
            raise IamResourceAlreadyExistsError(
                details={
                    "model": cls.model_class.__name__,
                    "fields": [
                        "role_scope",
                        "company_id",
                        "role_code",
                    ],
                    "role_scope": role_scope,
                    "company_id": company_id,
                    "role_code": role_code,
                },
            )

    @classmethod
    def prepare_create_data_for_operator(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        create_data = dict(data)

        if cls.operator_is_superuser(operator):
            return create_data

        if create_data.get("role_scope") == ROLE_SCOPE_PERSONAL:
            raise IamManagementAccessDeniedError(
                "Only platform superuser can create personal role.",
                details={
                    "role_scope": ROLE_SCOPE_PERSONAL,
                },
            )

        if create_data.get("role_scope") == ROLE_SCOPE_ENTERPRISE:
            create_data["company_id"] = cls.get_operator_company_id_or_raise(operator)

        return create_data


class UserManagementService(IamManagementService):
    model_class = IamUser
    validator_class = UserValidator

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
        "updated_at",
    )
    filter_fields = (
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
    )
    keyword_fields = (
        "username",
        "display_name",
        "email",
        "phone",
    )
    order_fields = (
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
        "updated_at",
    )
    unique_fields = (
        "username",
        "email",
        "phone",
    )
    tenant_scope_field = "company_id"
    tenant_create_field = None

    @classmethod
    async def create_item(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        prepared_data = cls.prepare_create_data_for_operator(
            data=data,
            operator=operator,
        )
        validated_data = cls.validator_class.validate_create(prepared_data)

        cls.ensure_can_write_privileged_flags(
            data=validated_data,
            operator=operator,
        )

        raw_password = PasswordTransportService.resolve(str(validated_data.pop("password", "") or ""))

        hashed_password = await sync_to_async(make_password, thread_sensitive=False)(raw_password)
        validated_data["password"] = hashed_password

        await cls.validate_create_business_rules(
            data=validated_data,
            operator=operator,
        )
        await cls.validate_unique_fields(
            data=validated_data,
            exclude_id=None,
        )

        return await cls.repository_class.create_item(
            model_class=cls.model_class,
            data=validated_data,
            fields=cls.detail_fields,
            operator_id=cls.get_operator_id(operator),
        )

    @classmethod
    async def update_item(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        cls.ensure_can_write_privileged_flags(
            data=data,
            operator=operator,
        )
        return await super().update_item(
            data=cls.prepare_update_data_for_operator(
                data=data,
                operator=operator,
            ),
            operator=operator,
        )

    @classmethod
    async def reset_password(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        if not cls.operator_is_superuser(operator):
            raise IamManagementAccessDeniedError("Only superuser can reset user password.")

        user_id = cls.get_required_id(data=data)
        password_payload = cls.get_password_payload(data=data)

        user = await cls.repository_class.get_by_id(
            model_class=cls.model_class,
            item_id=user_id,
        )

        if user is None:
            raise IamResourceNotFoundError(
                details={
                    "model": cls.model_class.__name__,
                    "id": user_id,
                },
            )

        raw_password = PasswordTransportService.resolve(password_payload)
        hashed_password = await sync_to_async(make_password, thread_sensitive=False)(raw_password)

        item = await cls.repository_class.update_item(
            model_class=cls.model_class,
            item_id=user_id,
            data={
                "password": hashed_password,
            },
            fields=cls.detail_fields,
            operator_id=cls.get_operator_id(operator),
        )

        if item is None:
            raise IamResourceNotFoundError(
                details={
                    "model": cls.model_class.__name__,
                    "id": user_id,
                },
            )

        revoked_at = timezone.now()
        await UserSessionRepository.revoke_user_sessions_and_tokens(
            user_id=user_id,
            revoked_at=revoked_at,
        )

        return {
            "id": user_id,
            "password_reset": True,
            "sessions_revoked": True,
            "revoked_at": revoked_at.isoformat(),
        }

    @classmethod
    def get_password_payload(cls, *, data: dict[str, Any]) -> str:
        raw_password = data.get("new_password")

        if raw_password in (None, ""):
            raw_password = data.get("password")

        if raw_password in (None, ""):
            raise IamManagementRequestInvalidError(
                "Password cannot be empty.",
                details={
                    "field": "new_password",
                },
            )

        return str(raw_password)

    @classmethod
    async def validate_create_business_rules(cls, *, data: dict[str, Any], operator: Any) -> None:
        await cls.validate_user_org_relation(
            user_type=data.get("user_type"),
            company_id=data.get("company_id"),
            subsidiary_id=data.get("subsidiary_id"),
            department_id=data.get("department_id"),
        )

    @classmethod
    async def validate_update_business_rules(cls, *, item: Any, data: dict[str, Any], operator: Any) -> None:
        user_type = getattr(item, "user_type", None)
        company_id = data.get("company_id", getattr(item, "company_id", None))
        subsidiary_id = data.get("subsidiary_id", getattr(item, "subsidiary_id", None))
        department_id = data.get("department_id", getattr(item, "department_id", None))

        await cls.validate_user_org_relation(
            user_type=user_type,
            company_id=company_id,
            subsidiary_id=subsidiary_id,
            department_id=department_id,
        )

    @classmethod
    async def validate_user_org_relation(cls, *, user_type: str | None, company_id: int | None, subsidiary_id: int | None, department_id: int | None) -> None:
        if user_type == USER_TYPE_PERSONAL:
            if company_id is not None or subsidiary_id is not None or department_id is not None:
                raise IamInvalidRelationError(
                    "Personal user must not bind to organization.",
                    details={
                        "user_type": user_type,
                        "company_id": company_id,
                        "subsidiary_id": subsidiary_id,
                        "department_id": department_id,
                    },
                )
            return

        if user_type != USER_TYPE_ENTERPRISE:
            raise IamInvalidRelationError("User type is invalid.",
                details={
                    "user_type": user_type,
                },
            )

        if company_id is None:
            raise IamInvalidRelationError(
                "Enterprise user must bind to company.",
                details={
                    "user_type": user_type,
                },
            )

        company = await cls.repository_class.get_by_id(
            model_class=IamCompany,
            item_id=company_id,
        )

        if company is None:
            raise IamInvalidRelationError(
                "Company does not exist.",
                details={
                    "company_id": company_id,
                },
            )

        if subsidiary_id is not None:
            subsidiary = await cls.repository_class.get_by_id(
                model_class=IamSubsidiary,
                item_id=subsidiary_id,
            )

            if subsidiary is None:
                raise IamInvalidRelationError(
                    "Subsidiary does not exist.",
                    details={
                        "subsidiary_id": subsidiary_id,
                    },
                )

            if subsidiary.company_id != company_id:
                raise IamInvalidRelationError(
                    "Subsidiary does not belong to company.",
                    details={
                        "company_id": company_id,
                        "subsidiary_id": subsidiary_id,
                    },
                )

        if department_id is not None:
            department = await cls.repository_class.get_by_id(
                model_class=IamDepartment,
                item_id=department_id,
            )

            if department is None:
                raise IamInvalidRelationError(
                    "Department does not exist.",
                    details={
                        "department_id": department_id,
                    },
                )

            if department.company_id != company_id:
                raise IamInvalidRelationError(
                    "Department does not belong to company.",
                    details={
                        "company_id": company_id,
                        "department_id": department_id,
                    },
                )

            department_subsidiary_id = getattr(department, "subsidiary_id", None)
            if subsidiary_id is not None and department_subsidiary_id is not None and department_subsidiary_id != subsidiary_id:
                raise IamInvalidRelationError(
                    "Department does not belong to subsidiary.",
                    details={
                        "subsidiary_id": subsidiary_id,
                        "department_id": department_id,
                        "department_subsidiary_id": department_subsidiary_id,
                    },
                )

    @classmethod
    def ensure_can_write_privileged_flags(cls, *, data: dict[str, Any], operator: Any) -> None:
        if cls.operator_is_superuser(operator):
            return

        privileged_fields = [
            field
            for field in (
                "is_staff",
                "is_superuser",
            )
            if field in data
        ]

        if not privileged_fields:
            return

        raise IamManagementAccessDeniedError(
            "Only superuser can modify privileged user flags.",
            details={
                "fields": privileged_fields,
            },
        )

    @staticmethod
    def operator_is_superuser(operator: Any) -> bool:
        return getattr(operator, "is_superuser", 0) in (
            True,
            1,
            "1",
        )

    @classmethod
    def prepare_create_data_for_operator(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        create_data = dict(data)

        if cls.operator_is_superuser(operator):
            return create_data

        if create_data.get("user_type") == USER_TYPE_PERSONAL:
            raise IamManagementAccessDeniedError(
                "Only platform superuser can create personal user.",
                details={
                    "user_type": USER_TYPE_PERSONAL,
                },
            )

        if create_data.get("user_type") == USER_TYPE_ENTERPRISE:
            create_data["company_id"] = cls.get_operator_company_id_or_raise(operator)

        return create_data

    @classmethod
    def prepare_update_data_for_operator(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        update_data = dict(data)

        if cls.operator_is_superuser(operator):
            return update_data

        if "company_id" not in update_data:
            return update_data

        company_id = cls.get_operator_company_id_or_raise(operator)
        requested_company_id = cls.normalize_company_id(update_data["company_id"])

        if requested_company_id != company_id:
            raise IamManagementAccessDeniedError(
                "Cannot move user to another company.",
                details={
                    "operator_company_id": company_id,
                    "request_company_id": requested_company_id,
                },
            )

        return update_data


class UserRoleManagementService(IamManagementService):
    model_class = IamUserRole
    validator_class = UserRoleValidator

    list_fields = detail_fields = (
        "id",
        "user_id",
        "role_id",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
    )
    filter_fields = (
        "id",
        "user_id",
        "role_id",
    )
    keyword_fields = ()
    order_fields = (
        "id",
        "user_id",
        "role_id",
        "created_at",
        "updated_at",
    )
    unique_fields = ()
    tenant_scope_field = "user__company_id"

    @classmethod
    async def validate_create_business_rules(cls, *, data: dict[str, Any], operator: Any) -> None:
        user_id = data.get("user_id")
        role_id = data.get("role_id")

        user = await cls.repository_class.get_by_id(
            model_class=IamUser,
            item_id=user_id,
        )
        if user is None:
            raise IamInvalidRelationError(
                "User does not exist.",
                details={
                    "user_id": user_id,
                },
            )

        role = await cls.repository_class.get_by_id(
            model_class=IamRole,
            item_id=role_id,
        )
        if role is None:
            raise IamInvalidRelationError(
                "Role does not exist.",
                details={
                    "role_id": role_id,
                },
            )

        await cls.ensure_model_item_company_access(
            model_class=IamUser,
            item_id=user_id,
            scope_field="company_id",
            operator=operator,
            label="user",
        )
        await cls.ensure_model_item_company_access(
            model_class=IamRole,
            item_id=role_id,
            scope_field="company_id",
            operator=operator,
            label="role",
        )

        await cls.validate_user_role_scope(
            user=user,
            role=role,
        )

    @classmethod
    async def validate_unique_fields(cls, *, data: dict[str, Any], exclude_id: int | None) -> None:
        user_id = data.get("user_id")
        role_id = data.get("role_id")

        if user_id in (None, "") or role_id in (None, ""):
            return

        exists = await cls.repository_class.exists_by_filters(
            model_class=cls.model_class,
            filters={
                "user_id": user_id,
                "role_id": role_id,
            },
            exclude_id=exclude_id,
        )

        if exists:
            raise IamResourceAlreadyExistsError(
                details={
                    "model": cls.model_class.__name__,
                    "fields": [
                        "user_id",
                        "role_id",
                    ],
                    "user_id": user_id,
                    "role_id": role_id,
                },
            )

    @classmethod
    async def validate_user_role_scope(cls, *, user: Any, role: Any) -> None:
        user_type = getattr(user, "user_type", None)
        user_company_id = getattr(user, "company_id", None)
        role_scope = getattr(role, "role_scope", None)
        role_company_id = getattr(role, "company_id", None)

        if user_type == USER_TYPE_PERSONAL:
            if role_scope != ROLE_SCOPE_PERSONAL or role_company_id is not None:
                raise IamInvalidRelationError(
                    "Personal user can only bind personal role.",
                    details={
                        "user_id": getattr(user, "id", None),
                        "user_type": user_type,
                        "role_id": getattr(role, "id", None),
                        "role_scope": role_scope,
                        "role_company_id": role_company_id,
                    },
                )
            return

        if user_type == USER_TYPE_ENTERPRISE:
            if role_scope != ROLE_SCOPE_ENTERPRISE:
                raise IamInvalidRelationError(
                    "Enterprise user can only bind enterprise role.",
                    details={
                        "user_id": getattr(user, "id", None),
                        "user_type": user_type,
                        "role_id": getattr(role, "id", None),
                        "role_scope": role_scope,
                    },
                )

            if user_company_id is None or role_company_id != user_company_id:
                raise IamInvalidRelationError(
                    "Enterprise role must belong to user company.",
                    details={
                        "user_id": getattr(user, "id", None),
                        "user_company_id": user_company_id,
                        "role_id": getattr(role, "id", None),
                        "role_company_id": role_company_id,
                    },
                )
            return

        raise IamInvalidRelationError(
            "User type is invalid.",
            details={
                "user_id": getattr(user, "id", None),
                "user_type": user_type,
            },
        )


class RolePermissionManagementService(IamManagementService):
    model_class = IamRolePermission
    validator_class = RolePermissionValidator

    list_fields = detail_fields = (
        "id",
        "role_id",
        "permission_id",
        "data_scope",
        "granted_by_id",
        "expired_at",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
    )
    filter_fields = (
        "id",
        "role_id",
        "permission_id",
        "data_scope",
        "granted_by_id",
    )
    keyword_fields = ()
    order_fields = (
        "id",
        "role_id",
        "permission_id",
        "data_scope",
        "granted_by_id",
        "expired_at",
        "created_at",
        "updated_at",
    )
    unique_fields = ()
    tenant_scope_field = "role__company_id"

    @classmethod
    async def create_item(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        validated_data = cls.validator_class.validate_create(data)
        validated_data["granted_by_id"] = cls.get_operator_id(operator)

        await cls.validate_create_business_rules(
            data=validated_data,
            operator=operator,
        )
        await cls.validate_unique_fields(
            data=validated_data,
            exclude_id=None,
        )

        return await cls.repository_class.create_item(
            model_class=cls.model_class,
            data=validated_data,
            fields=cls.detail_fields,
            operator_id=cls.get_operator_id(operator),
        )

    @classmethod
    async def validate_create_business_rules(cls, *, data: dict[str, Any], operator: Any) -> None:
        role_id = data.get("role_id")
        permission_id = data.get("permission_id")

        role = await cls.repository_class.get_by_id(
            model_class=IamRole,
            item_id=role_id,
        )
        if role is None:
            raise IamInvalidRelationError(
                "Role does not exist.",
                details={
                    "role_id": role_id,
                },
            )

        permission = await cls.repository_class.get_by_id(
            model_class=IamPermission,
            item_id=permission_id,
        )
        if permission is None:
            raise IamInvalidRelationError(
                "Permission does not exist.",
                details={
                    "permission_id": permission_id,
                },
            )

        await cls.ensure_model_item_company_access(
            model_class=IamRole,
            item_id=role_id,
            scope_field="company_id",
            operator=operator,
            label="role",
        )

    @classmethod
    async def validate_unique_fields(cls, *, data: dict[str, Any], exclude_id: int | None) -> None:
        role_id = data.get("role_id")
        permission_id = data.get("permission_id")

        if role_id in (None, "") or permission_id in (None, ""):
            return

        exists = await cls.repository_class.exists_by_filters(
            model_class=cls.model_class,
            filters={
                "role_id": role_id,
                "permission_id": permission_id,
            },
            exclude_id=exclude_id,
        )

        if exists:
            raise IamResourceAlreadyExistsError(
                details={
                    "model": cls.model_class.__name__,
                    "fields": [
                        "role_id",
                        "permission_id",
                    ],
                    "role_id": role_id,
                    "permission_id": permission_id,
                },
            )


class DirectPermissionGrantManagementService(IamManagementService):
    """
    直接授权关系管理基类。

    适用表：
    1. iam_user_permission
    2. iam_department_permission
    3. iam_subsidiary_permission
    """

    subject_model_class: ClassVar[Any] = None
    subject_id_field: ClassVar[str] = ""
    subject_label: ClassVar[str] = ""

    list_fields = detail_fields = (
        "id",
        "permission_id",
        "effect",
        "data_scope",
        "granted_by_id",
        "expired_at",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
    )
    keyword_fields = ()
    unique_fields = ()

    @classmethod
    async def create_item(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        validated_data = cls.validator_class.validate_create(data)
        validated_data["granted_by_id"] = cls.get_operator_id(operator)

        await cls.validate_create_business_rules(
            data=validated_data,
            operator=operator,
        )
        await cls.validate_unique_fields(
            data=validated_data,
            exclude_id=None,
        )

        return await cls.repository_class.create_item(
            model_class=cls.model_class,
            data=validated_data,
            fields=cls.detail_fields,
            operator_id=cls.get_operator_id(operator),
        )

    @classmethod
    async def validate_create_business_rules(cls, *, data: dict[str, Any], operator: Any) -> None:
        subject_id = data.get(cls.subject_id_field)
        permission_id = data.get("permission_id")

        subject = await cls.repository_class.get_by_id(
            model_class=cls.subject_model_class,
            item_id=subject_id,
        )

        if subject is None:
            raise IamInvalidRelationError(
                f"{cls.subject_label} does not exist.",
                details={
                    cls.subject_id_field: subject_id,
                },
            )

        permission = await cls.repository_class.get_by_id(
            model_class=IamPermission,
            item_id=permission_id,
        )

        if permission is None:
            raise IamInvalidRelationError(
                "Permission does not exist.",
                details={
                    "permission_id": permission_id,
                },
            )

        await cls.validate_subject_business_rules(
            subject=subject,
            data=data,
            operator=operator,
        )

    @classmethod
    async def validate_subject_business_rules(cls, *, subject: Any, data: dict[str, Any], operator: Any) -> None:
        return None

    @classmethod
    async def validate_unique_fields(cls, *, data: dict[str, Any], exclude_id: int | None) -> None:
        subject_id = data.get(cls.subject_id_field)
        permission_id = data.get("permission_id")

        if subject_id in (None, "") or permission_id in (None, ""):
            return

        exists = await cls.repository_class.exists_by_filters(
            model_class=cls.model_class,
            filters={
                cls.subject_id_field: subject_id,
                "permission_id": permission_id,
            },
            exclude_id=exclude_id,
        )

        if exists:
            raise IamResourceAlreadyExistsError(
                details={
                    "model": cls.model_class.__name__,
                    "fields": [
                        cls.subject_id_field,
                        "permission_id",
                    ],
                    cls.subject_id_field: subject_id,
                    "permission_id": permission_id,
                },
            )


class UserPermissionManagementService(DirectPermissionGrantManagementService):
    model_class = IamUserPermission
    validator_class = UserPermissionValidator
    subject_model_class = IamUser
    subject_id_field = "user_id"
    subject_label = "User"

    list_fields = detail_fields = (
        "id",
        "user_id",
        "permission_id",
        "effect",
        "data_scope",
        "granted_by_id",
        "expired_at",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
    )
    filter_fields = (
        "id",
        "user_id",
        "permission_id",
        "effect",
        "data_scope",
        "granted_by_id",
    )
    order_fields = (
        "id",
        "user_id",
        "permission_id",
        "effect",
        "data_scope",
        "granted_by_id",
        "expired_at",
        "created_at",
        "updated_at",
    )
    tenant_scope_field = "user__company_id"

    @classmethod
    async def validate_subject_business_rules(cls, *, subject: Any, data: dict[str, Any], operator: Any) -> None:
        await cls.ensure_model_item_company_access(
            model_class=IamUser,
            item_id=getattr(subject, "id", None),
            scope_field="company_id",
            operator=operator,
            label="user",
        )


class DepartmentPermissionManagementService(DirectPermissionGrantManagementService):
    model_class = IamDepartmentPermission
    validator_class = DepartmentPermissionValidator
    subject_model_class = IamDepartment
    subject_id_field = "department_id"
    subject_label = "Department"

    list_fields = detail_fields = (
        "id",
        "department_id",
        "permission_id",
        "effect",
        "data_scope",
        "granted_by_id",
        "expired_at",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
    )
    filter_fields = (
        "id",
        "department_id",
        "permission_id",
        "effect",
        "data_scope",
        "granted_by_id",
    )
    order_fields = (
        "id",
        "department_id",
        "permission_id",
        "effect",
        "data_scope",
        "granted_by_id",
        "expired_at",
        "created_at",
        "updated_at",
    )
    tenant_scope_field = "department__company_id"

    @classmethod
    async def validate_subject_business_rules(cls, *, subject: Any, data: dict[str, Any], operator: Any) -> None:
        await cls.ensure_model_item_company_access(
            model_class=IamDepartment,
            item_id=getattr(subject, "id", None),
            scope_field="company_id",
            operator=operator,
            label="department",
        )


class SubsidiaryPermissionManagementService(DirectPermissionGrantManagementService):
    model_class = IamSubsidiaryPermission
    validator_class = SubsidiaryPermissionValidator
    subject_model_class = IamSubsidiary
    subject_id_field = "subsidiary_id"
    subject_label = "Subsidiary"

    list_fields = detail_fields = (
        "id",
        "subsidiary_id",
        "permission_id",
        "effect",
        "data_scope",
        "granted_by_id",
        "expired_at",
        "created_by",
        "updated_by",
        "created_at",
        "updated_at",
    )
    filter_fields = (
        "id",
        "subsidiary_id",
        "permission_id",
        "effect",
        "data_scope",
        "granted_by_id",
    )
    order_fields = (
        "id",
        "subsidiary_id",
        "permission_id",
        "effect",
        "data_scope",
        "granted_by_id",
        "expired_at",
        "created_at",
        "updated_at",
    )
    tenant_scope_field = "subsidiary__company_id"

    @classmethod
    async def validate_subject_business_rules(cls, *, subject: Any, data: dict[str, Any], operator: Any) -> None:
        await cls.ensure_model_item_company_access(
            model_class=IamSubsidiary,
            item_id=getattr(subject, "id", None),
            scope_field="company_id",
            operator=operator,
            label="subsidiary",
        )
