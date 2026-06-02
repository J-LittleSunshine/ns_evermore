# IAM P3 Agent Tool Guard

## 1. Mandatory Integration Entry

- `src/ns_backend/iam/integration/facade.py`
- Class: `AgentToolIamFacade`
- Convenience function: `run_agent_tool_with_iam(...)`

## 2. Tool Guard Contract

Before executing a tool, call `AgentToolIamFacade.execute_tool_with_iam(...)`.

Guard behavior:

- IAM decision is evaluated before tool callable execution.
- Denied or unmapped tools raise `BusinessError(code=PERMISSION_DENIED)`.
- Tool callable is never executed when authorization fails.

## 3. Callable Example

```python
from ns_backend.iam.integration import run_agent_tool_with_iam


async def guarded_tool_call(current_user, knowledge_search_tool):
	result = await run_agent_tool_with_iam(
		user=current_user,
		tool_name="knowledge.search",
		resource_id="workspace_001",
		tool_callable=knowledge_search_tool.run,
		tool_kwargs={"query": "roadmap"},
		trace_id="trace-agent-001",
	)
	return result["tool_result"]
```

## 4. Mapping Management

- Built-in map: `TOOL_ACTION_MAP`
- Runtime extension: `register_tool_action(...)`

Each tool mapping provides:

- `resource_type`
- `action_code`
- `permission_code` (optional)

