# -*- coding: utf-8 -*-
from __future__ import annotations

import inspect
from typing import (
    Any,
    Callable,
    TYPE_CHECKING,
)

from ns_backend.iam.errors import IamRuntimeRequestInvalidError
from ns_backend.iam.integration.agent_guard import AgentToolAuthorizationGuard
from ns_backend.iam.integration.knowledge_filter import KnowledgeAuthorizationFilter

if TYPE_CHECKING:
    pass


def normalize_kwargs(*, value: dict[str, Any] | None, field_name: str) -> dict[str, Any]:
    kwargs = {} if value is None else value
    if not isinstance(kwargs, dict):
        raise IamRuntimeRequestInvalidError(
            f"{field_name} must be an object.",
            details={
                "field": field_name,
            },
        )

    return kwargs


async def invoke_callable(*, target: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
    result = target(*args, **kwargs)
    if inspect.isawaitable(result):
        return await result

    return result


class KnowledgeRetrieverIamFacade:
    @staticmethod
    async def invoke_retriever(*, retriever_callable: Callable[..., Any], allowed_items: list[dict[str, Any]], retriever_kwargs: dict[str, Any] | None) -> Any:
        kwargs = normalize_kwargs(
            value=retriever_kwargs,
            field_name="retriever_kwargs",
        )

        return await invoke_callable(
            target=retriever_callable,
            args=(allowed_items,),
            kwargs=kwargs,
        )

    @classmethod
    async def recall_with_iam(
            cls,
            *,
            user: Any,
            candidates: list[dict[str, Any]],
            retriever_callable: Callable[..., Any],
            resource_type: str = KnowledgeAuthorizationFilter.DEFAULT_RESOURCE_TYPE,
            action_code: str = KnowledgeAuthorizationFilter.DEFAULT_ACTION_CODE,
            resource_id_field: str = KnowledgeAuthorizationFilter.DEFAULT_RESOURCE_ID_FIELD,
            permission_code: str | None = None,
            field_map: dict[str, Any] | None = None,
            retriever_kwargs: dict[str, Any] | None = None,
            trace_id: str | None = None,
    ) -> dict[str, Any]:
        if not callable(retriever_callable):
            raise IamRuntimeRequestInvalidError(
                "retriever_callable is required.",
                details={
                    "field": "retriever_callable",
                },
            )

        filter_result = await KnowledgeAuthorizationFilter.filter_candidates(
            user=user,
            candidates=candidates,
            resource_type=resource_type,
            action_code=action_code,
            resource_id_field=resource_id_field,
            permission_code=permission_code,
            field_map=field_map,
            trace_id=trace_id,
        )

        allowed_items = list(filter_result.get("allowed_items", []))
        denied_items = list(filter_result.get("denied_items", []))
        decision_items = list(filter_result.get("decision_items", []))

        if not allowed_items:
            return {
                "allowed_items": allowed_items,
                "denied_items": denied_items,
                "decision_items": decision_items,
                "authorized_count": 0,
                "denied_count": len(denied_items),
                "retriever_called": False,
                "retriever_result": [],
                "retrieval_filter": filter_result.get("retrieval_filter"),
                "trace_id": trace_id,
            }

        retriever_result = await cls.invoke_retriever(
            retriever_callable=retriever_callable,
            allowed_items=allowed_items,
            retriever_kwargs=retriever_kwargs,
        )

        return {
            "allowed_items": allowed_items,
            "denied_items": denied_items,
            "decision_items": decision_items,
            "authorized_count": len(allowed_items),
            "denied_count": len(denied_items),
            "retriever_called": True,
            "retriever_result": retriever_result,
            "retrieval_filter": filter_result.get("retrieval_filter"),
            "trace_id": trace_id,
        }


class AgentToolIamFacade:
    @staticmethod
    def normalize_tool_args(tool_args: list[Any] | tuple[Any, ...] | None) -> tuple[Any, ...]:
        if tool_args is None:
            return ()

        if isinstance(tool_args, tuple):
            return tool_args

        if isinstance(tool_args, list):
            return tuple(tool_args)

        raise IamRuntimeRequestInvalidError(
            "tool_args must be a list or tuple.",
            details={
                "field": "tool_args",
            },
        )

    @staticmethod
    async def invoke_tool(*, tool_callable: Callable[..., Any], tool_args: list[Any] | tuple[Any, ...] | None, tool_kwargs: dict[str, Any] | None) -> Any:
        normalized_args = AgentToolIamFacade.normalize_tool_args(tool_args)
        kwargs = normalize_kwargs(
            value=tool_kwargs,
            field_name="tool_kwargs",
        )

        return await invoke_callable(
            target=tool_callable,
            args=normalized_args,
            kwargs=kwargs,
        )

    @classmethod
    async def execute_tool_with_iam(
            cls,
            *,
            user: Any,
            tool_name: str,
            resource_id: str,
            tool_callable: Callable[..., Any],
            context: dict[str, Any] | None = None,
            tool_args: list[Any] | tuple[Any, ...] | None = None,
            tool_kwargs: dict[str, Any] | None = None,
            trace_id: str | None = None,
    ) -> dict[str, Any]:
        if not callable(tool_callable):
            raise IamRuntimeRequestInvalidError(
                "tool_callable is required.",
                details={
                    "field": "tool_callable",
                },
            )

        decision = await AgentToolAuthorizationGuard.ensure_tool_allowed(
            user=user,
            tool_name=tool_name,
            resource_id=resource_id,
            context=context,
            trace_id=trace_id,
        )

        tool_result = await cls.invoke_tool(
            tool_callable=tool_callable,
            tool_args=tool_args,
            tool_kwargs=tool_kwargs,
        )

        return {
            "decision": decision,
            "tool_result": tool_result,
        }
