# -*- coding: utf-8 -*-
from __future__ import annotations

import inspect
from typing import TYPE_CHECKING, Any, Callable

from ns_backend.backend.exceptions import BusinessError
from ns_backend.iam.integration.agent_guard import AgentToolAuthorizationGuard
from ns_backend.iam.integration.knowledge_filter import KnowledgeAuthorizationFilter
from ns_common.error_codes import NsErrorCode

if TYPE_CHECKING:
    pass


def _normalize_kwargs(*, value: dict[str, Any] | None, field_name: str) -> dict[str, Any]:
    """Normalize optional keyword-argument payload for callable invocation."""
    kwargs = {} if value is None else value
    if not isinstance(kwargs, dict):
        raise BusinessError(f"{field_name} must be an object", NsErrorCode.INVALID_VALUE)
    return kwargs


async def _invoke_callable(*, target: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]) -> Any:
    """Invoke one callable and await the result when needed."""
    result = target(*args, **kwargs)
    if inspect.isawaitable(result):
        return await result
    return result


class KnowledgeRetrieverIamFacade:
    """Apply IAM filtering before invoking retriever callbacks."""

    @staticmethod
    async def _invoke_retriever(
        *,
        retriever_callable: Callable[..., Any],
        allowed_items: list[dict[str, Any]],
        retriever_kwargs: dict[str, Any] | None,
    ) -> Any:
        """Invoke retriever with IAM-allowed items only."""
        kwargs = _normalize_kwargs(value=retriever_kwargs, field_name="retriever_kwargs")
        return await _invoke_callable(target=retriever_callable, args=(allowed_items,), kwargs=kwargs)

    @classmethod
    async def recall_with_iam(
        cls,
        *,
        user: Any,
        candidates: list[dict[str, Any]],
        retriever_callable: Callable[..., Any],
        resource_type: str = KnowledgeAuthorizationFilter.DEFAULT_RESOURCE_TYPE,
        action_code: str = KnowledgeAuthorizationFilter.DEFAULT_ACTION_CODE,
        resource_id_field: str = "resource_id",
        permission_code: str | None = None,
        retriever_kwargs: dict[str, Any] | None = None,
        trace_id: str | None = None,
    ) -> dict[str, Any]:
        """Filter candidate items by IAM and run retriever on allowed candidates only."""
        if not callable(retriever_callable):
            raise BusinessError("retriever_callable is required", NsErrorCode.INVALID_VALUE)

        filter_result = await KnowledgeAuthorizationFilter.filter_candidates(
            user=user,
            candidates=candidates,
            resource_type=resource_type,
            action_code=action_code,
            resource_id_field=resource_id_field,
            permission_code=permission_code,
            trace_id=trace_id,
        )

        allowed_items = list(filter_result.get("allowed_items", []))
        denied_items = list(filter_result.get("denied_items", []))
        decision_items = list(filter_result.get("decision_items", []))

        if not allowed_items:
            # Fail-close: no authorized candidates means retriever is not called.
            return {
                "allowed_items": allowed_items,
                "denied_items": denied_items,
                "decision_items": decision_items,
                "authorized_count": 0,
                "denied_count": len(denied_items),
                "retriever_called": False,
                "retriever_result": [],
            }

        retriever_result = await cls._invoke_retriever(
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
        }


class AgentToolIamFacade:
    """Apply IAM authorization before invoking agent tool callbacks."""

    @staticmethod
    def _normalize_tool_args(tool_args: list[Any] | tuple[Any, ...] | None) -> tuple[Any, ...]:
        """Normalize optional positional arguments passed to tool callbacks."""
        if tool_args is None:
            return ()
        if isinstance(tool_args, tuple):
            return tool_args
        if isinstance(tool_args, list):
            return tuple(tool_args)
        raise BusinessError("tool_args must be a list or tuple", NsErrorCode.INVALID_VALUE)

    @staticmethod
    async def _invoke_tool(
        *,
        tool_callable: Callable[..., Any],
        tool_args: list[Any] | tuple[Any, ...] | None,
        tool_kwargs: dict[str, Any] | None,
    ) -> Any:
        """Invoke one tool callback after IAM authorization succeeds."""
        normalized_args = AgentToolIamFacade._normalize_tool_args(tool_args)
        kwargs = _normalize_kwargs(value=tool_kwargs, field_name="tool_kwargs")
        return await _invoke_callable(target=tool_callable, args=normalized_args, kwargs=kwargs)

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
        """Authorize tool action first, then execute the tool callback."""
        if not callable(tool_callable):
            raise BusinessError("tool_callable is required", NsErrorCode.INVALID_VALUE)

        decision = await AgentToolAuthorizationGuard.ensure_tool_allowed(
            user=user,
            tool_name=tool_name,
            resource_id=resource_id,
            context=context,
            trace_id=trace_id,
        )

        tool_result = await cls._invoke_tool(
            tool_callable=tool_callable,
            tool_args=tool_args,
            tool_kwargs=tool_kwargs,
        )
        return {
            "decision": decision,
            "tool_result": tool_result,
        }

