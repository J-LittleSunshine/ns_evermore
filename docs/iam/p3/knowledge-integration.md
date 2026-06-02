# IAM P3 Knowledge Integration

## 1. Mandatory Integration Entry

- `src/ns_backend/iam/integration/facade.py`
- Class: `KnowledgeRetrieverIamFacade`
- Convenience function: `run_knowledge_retriever_with_iam(...)`

## 2. Integration Contract

Call `KnowledgeRetrieverIamFacade.recall_with_iam(...)` before retriever execution.

Input:

- candidate list
- retriever callable
- resource id field name (default `resource_id`)
- IAM resource/action (`knowledge.chunk` + `read` by default)
- candidate fields used by IAM `filters` (direct fields or `metadata` fields)

Output:

- `allowed_items`
- `denied_items`
- `decision_items`
- `retriever_called`
- `retriever_result`

## 3. Fail-Close Rules

- Authorization filtering always happens before retriever invocation.
- If all candidates are denied, retriever is not called and `retriever_called=False`.
- If candidate payload cannot satisfy IAM filters, candidate is denied (fail-close).
- If batch decision shape is invalid (count/type mismatch), request fails closed (`BusinessError`).

## 4. Callable Example

```python
from ns_backend.iam.integration import run_knowledge_retriever_with_iam


async def guarded_recall(current_user, retriever):
    result = await run_knowledge_retriever_with_iam(
        user=current_user,
        candidates=[
            {"chunk_id": "chunk_001", "content": "..."},
            {"chunk_id": "chunk_002", "content": "..."},
        ],
        retriever_callable=retriever.recall,
        trace_id="trace-knowledge-001",
    )

    return result["retriever_result"]
```

## 5. Enforcement Rule

No unauthorized chunk/document should enter final retrieval context.

