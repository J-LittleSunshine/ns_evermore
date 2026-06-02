# L1 Foundation: API and Permission Contract

## 1. Permission Code Format

Format:

- `{module}:{resource}:{action}`

Examples:

- `iam:user:update`
- `knowledge:chunk:read`
- `erp:invoice:approve`

## 2. Action Governance

Action values should follow IAM action taxonomy.

Reference implementation:

- `ResourceAclService.ALLOWED_ACTION_CODES` in `src/ns_backend/iam/services/resource_acl.py`

## 3. API Capability Groups

Resource registration:

- `POST /iam/resource/register`
- `POST /iam/resource/action/register`
- `POST /iam/resource/list`

ACL management:

- `POST /iam/acl/grant`
- `POST /iam/acl/revoke`
- `POST /iam/acl/list`

Policy management:

- `POST /iam/policy/create`
- `POST /iam/policy/update`
- `POST /iam/policy/publish`
- `POST /iam/policy/disable`
- `POST /iam/policy/rule/add`
- `POST /iam/policy/rule/remove`
- `POST /iam/policy/rule/list`

Authorization:

- `POST /iam/authorize/check`
- `POST /iam/authorize/batch-check`

Decision audit query:

- `POST /iam/audit/decision/list`

## 4. Authorize Response Contract

`/iam/authorize/check` response fields:

- `allowed: bool`
- `effect: allow|deny`
- `reason: str`
- `matched_source: acl|policy|rbac|superuser|none`
- `matched_policy_id: int|null`
- `matched_rule_id: int|null`
- `filters: object`

## 5. IAM View Permission Contract

IAM routes use `required_permissions` as stable route contract.

Current behavior:

- Permission decision path is unified through `AuthorizeService`.
- If authorization service fails, request handling is fail-close.

