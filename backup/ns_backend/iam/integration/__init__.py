# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from ns_backend.iam.integration.agent_guard import AgentToolAuthorizationGuard
from ns_backend.iam.integration.examples import (
    ensure_agent_tool_executable,
    filter_knowledge_candidates_before_retriever,
    run_agent_tool_with_iam,
    run_knowledge_retriever_with_iam,
)
from ns_backend.iam.integration.facade import AgentToolIamFacade, KnowledgeRetrieverIamFacade
from ns_backend.iam.integration.knowledge_filter import KnowledgeAuthorizationFilter

if TYPE_CHECKING:
    pass

__all__ = [
    "AgentToolAuthorizationGuard",
    "AgentToolIamFacade",
    "KnowledgeAuthorizationFilter",
    "KnowledgeRetrieverIamFacade",
    "ensure_agent_tool_executable",
    "filter_knowledge_candidates_before_retriever",
    "run_agent_tool_with_iam",
    "run_knowledge_retriever_with_iam",
]
