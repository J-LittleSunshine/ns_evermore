# IAM P2 Policy Engine and Decision Audit

## 1. Added Data Models

- `iam_policy`
- `iam_policy_rule`
- `iam_audit_log`

All three models are included in:

- `sql/create/iam/sqlite.sql`
- `sql/create/iam/mysql.sql`
- `sql/create/iam/postgresql.sql`

## 2. Policy Evaluation Order

Current `AuthorizeService` decision flow:

1. superuser allow
2. ACL deny
3. Policy deny
4. ACL allow
5. Policy allow
6. RBAC allow
7. default deny

Policy rule ordering inside policy engine:

- higher `rule.priority` first
- then higher `policy.priority`
- same priority: `DENY` before `ALLOW`

## 3. Policy APIs

- `POST /iam/policy/create`
- `POST /iam/policy/update`
- `POST /iam/policy/publish`
- `POST /iam/policy/disable`
- `POST /iam/policy/rule/add`
- `POST /iam/policy/rule/remove`
- `POST /iam/policy/rule/list`

## 4. Decision Audit API

- `POST /iam/audit/decision/list`

Each decision row keeps:

- subject/resource/action
- result and reason
- matched policy/rule ids
- trace id

## 5. Decision Audit Strict Mode Toggle

- Setting key: `IAM_DECISION_AUDIT_STRICT_MODE`
- Environment keys: `NS_IAM_DECISION_AUDIT_STRICT_MODE` or `IAM_DECISION_AUDIT_STRICT_MODE`
- Backend config key: `backend.iam_decision_audit_strict_mode`
- Default: `false` (best-effort audit write, only logs on failure)

When strict mode is enabled:

- Decision audit write failures raise `AUDIT_CREATE_FAILED`.
- This is intended for later Gate strict enforcement after application integration.

