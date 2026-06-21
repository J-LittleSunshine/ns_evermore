# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ns_backend.iam.integration.agent_guard import AgentToolAuthorizationGuard
from ns_backend.iam.integration.facade import AgentToolIamFacade, KnowledgeRetrieverIamFacade
from ns_backend.iam.integration.knowledge_filter import KnowledgeAuthorizationFilter

if TYPE_CHECKING:
    pass

KNOWLEDGE_RESOURCE_TYPE = "knowledge.chunk"
KNOWLEDGE_ACTION_CODE = "read"
KNOWLEDGE_PERMISSION_CODE = "knowledge:chunk:read"
AGENT_CHANNEL_CONTEXT = "agent"


def _build_agent_context() -> dict[str, str]:
    """Build a fresh agent execution context payload."""
    return {
        "channel": AGENT_CHANNEL_CONTEXT
    }


async def filter_knowledge_candidates_before_retriever(
        *,
        user: Any,
        candidates: list[dict[str, Any]],
        trace_id: str | None = None,
) -> list[dict[str, Any]]:
    """Filter candidate chunks/documents before retriever recall."""
    filter_result = await KnowledgeAuthorizationFilter.filter_candidates(
        user=user,
        candidates=candidates,
        resource_type=KNOWLEDGE_RESOURCE_TYPE,
        action_code=KNOWLEDGE_ACTION_CODE,
        resource_id_field="chunk_id",
        permission_code=KNOWLEDGE_PERMISSION_CODE,
        trace_id=trace_id,
    )
    return list(filter_result.get("allowed_items", []))


async def run_knowledge_retriever_with_iam(
        *,
        user: Any,
        candidates: list[dict[str, Any]],
        retriever_callable,
        retriever_kwargs: dict[str, Any] | None = None,
        trace_id: str | None = None,
) -> dict[str, Any]:
    """Run retriever with IAM filtering applied before execution."""
    return await KnowledgeRetrieverIamFacade.recall_with_iam(
        user=user,
        candidates=candidates,
        retriever_callable=retriever_callable,
        resource_type=KNOWLEDGE_RESOURCE_TYPE,
        action_code=KNOWLEDGE_ACTION_CODE,
        resource_id_field="chunk_id",
        permission_code=KNOWLEDGE_PERMISSION_CODE,
        retriever_kwargs=retriever_kwargs,
        trace_id=trace_id,
    )


async def ensure_agent_tool_executable(
        *,
        user: Any,
        tool_name: str,
        resource_id: str,
        trace_id: str | None = None,
) -> dict[str, Any]:
    """Authorize one agent tool call before invocation."""
    return await AgentToolAuthorizationGuard.ensure_tool_allowed(
        user=user,
        tool_name=tool_name,
        resource_id=resource_id,
        context=_build_agent_context(),
        trace_id=trace_id,
    )


async def run_agent_tool_with_iam(
        *,
        user: Any,
        tool_name: str,
        resource_id: str,
        tool_callable,
        tool_args: list[Any] | tuple[Any, ...] | None = None,
        tool_kwargs: dict[str, Any] | None = None,
        trace_id: str | None = None,
) -> dict[str, Any]:
    """Authorize and execute one agent tool callback via IAM facade."""
    return await AgentToolIamFacade.execute_tool_with_iam(
        user=user,
        tool_name=tool_name,
        resource_id=resource_id,
        tool_callable=tool_callable,
        context=_build_agent_context(),
        tool_args=tool_args,
        tool_kwargs=tool_kwargs,
        trace_id=trace_id,
    )
