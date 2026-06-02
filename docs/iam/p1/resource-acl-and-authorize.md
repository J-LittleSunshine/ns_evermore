# IAM P1 Resource ACL and Authorize APIs

## 1. Resource Registry APIs

- `POST /iam/resource/register`
- `POST /iam/resource/action/register`
- `POST /iam/resource/list`

### Request examples

`/iam/resource/register`

```json
{
  "resource_type": "knowledge.document",
  "resource_name": "Knowledge Document",
  "module_code": "knowledge",
  "status": 1
}
```

`/iam/resource/action/register`

```json
{
  "resource_type": "knowledge.document",
  "action_code": "read",
  "action_name": "Read document",
  "status": 1
}
```

## 2. Resource ACL APIs

- `POST /iam/acl/grant`
- `POST /iam/acl/revoke`
- `POST /iam/acl/list`

### `subject_type` values

- `USER`
- `ROLE`
- `DEPARTMENT`
- `ORGANIZATION`
- `SUBSIDIARY`

### ACL grant example

```json
{
  "subject_type": "USER",
  "subject_id": 1001,
  "resource_type": "knowledge.document",
  "resource_id": "doc_123",
  "action_code": "read",
  "effect": "ALLOW",
  "data_scope": "DEPARTMENT_TREE",
  "expired_at": null
}
```

## 3. Unified Authorize APIs

- `POST /iam/authorize/check`
- `POST /iam/authorize/batch-check`

## 4. View-Layer Unified Access Mode (Default)

`IamRequestViewSet` keeps `required_permissions` as the route contract, but the decision path is unified through `AuthorizeService`.

- No runtime toggle is required for IAM views.
- If unified authorization cannot return a valid decision, request handling is fail-close (`PERMISSION_DENIED`) and logs an explicit error.
- Decision reason/source from `AuthorizeService` is written into request audit context.

### Decision order

1. superuser
2. ACL deny
3. Policy deny (placeholder, P2)
4. ACL allow
5. RBAC allow
6. otherwise deny

### `authorize/check` response fields

- `allowed`
- `effect`
- `reason`
- `matched_source`
- `matched_policy_id`
- `matched_rule_id`
- `filters`

