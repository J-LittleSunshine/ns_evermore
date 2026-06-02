# L3 Integration: Knowledge and Agent

## 1. Knowledge Integration (Retriever-First Guard)

Mandatory entry:

- `KnowledgeRetrieverIamFacade.recall_with_iam(...)`

Source:

- `src/ns_backend/iam/integration/facade.py`

Behavior:

- IAM filter is evaluated before retriever invocation.
- Unauthorized candidates are excluded.
- If no candidate is authorized, retriever is not called.

Fail-close conditions:

- invalid decision payload shape
- candidate cannot satisfy returned IAM filters

## 2. Agent Integration (Tool-First Guard)

Mandatory entry:

- `AgentToolIamFacade.execute_tool_with_iam(...)`

Source:

- `src/ns_backend/iam/integration/facade.py`

Behavior:

- IAM authorization is evaluated before tool execution.
- denied or unmapped tools raise `PERMISSION_DENIED`.
- tool callback is not executed when denied.

## 3. Mapping Management

Tool-action mapping source:

- `AgentToolAuthorizationGuard.TOOL_ACTION_MAP`

Runtime extension:

- `register_tool_action(...)`
- mapping registration auto-provisions IAM `resource/action/permission` rows

Each mapping defines:

- `resource_type`
- `action_code`
- `permission_code` (optional)

## 4. Integration Examples

- `src/ns_backend/iam/integration/examples.py`

