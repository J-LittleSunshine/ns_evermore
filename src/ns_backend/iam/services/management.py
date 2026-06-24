# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import (
    Any,
    ClassVar,
    TYPE_CHECKING,
)

from ns_backend.iam.errors import (
    IamInvalidRelationError,
    IamManagementRequestInvalidError,
    IamResourceAlreadyExistsError,
    IamResourceNotFoundError,
)
from ns_backend.iam.models import (
    IamCompany,
    IamDepartment,
    IamSubsidiary,
)
from ns_backend.iam.repositories import IamManagementRepository
from ns_backend.iam.validators import (
    CompanyValidator,
    DepartmentValidator,
    IamManagementValidator,
    SubsidiaryValidator,
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

        filters = cls.build_filters(data=data)
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
    async def detail_item(cls, *, data: dict[str, Any], operator: Any) -> dict[str, Any]:
        item_id = cls.get_required_id(data=data)

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
        validated_data = cls.validator_class.validate_create(data)

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
        item_id = cls.get_required_id(data=data)
        validated_data = cls.validator_class.validate_update(data)

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
