# L2 Capability: Policy Engine and Decision Audit

## 1. Policy Data Model

Core tables:

- `iam_policy`
- `iam_policy_rule`

Schema sources:

- `sql/create/iam/sqlite.sql`
- `sql/create/iam/mysql.sql`
- `sql/create/iam/postgresql.sql`
- `src/ns_backend/iam/models.py`

## 2. Policy Evaluation Rule

Policy rule ordering:

- higher `rule.priority` first
- then higher `policy.priority`
- same priority: DENY before ALLOW

Policy result is included in authorize decision with:

- `matched_policy_id`
- `matched_rule_id`

## 3. Decision Audit

Decision audit table:

- `iam_audit_log`

Query API:

- `POST /iam/audit/decision/list`

Decision audit records include at least:

- subject/resource/action
- result
- reason
- matched ACL id/source
- matched policy/rule id
- trace id

Current write payload also keeps compact chain trace in `reason`, e.g. ACL/Policy/RBAC hit order.

## 4. Strict Decision Audit Mode

Setting:

- `IAM_DECISION_AUDIT_STRICT_MODE`

Environment overrides:

- `NS_IAM_DECISION_AUDIT_STRICT_MODE`
- `IAM_DECISION_AUDIT_STRICT_MODE`

Backend config:

- `backend.iam_decision_audit_strict_mode`

Current default:

- `false` (best-effort write)

When enabled:

- decision audit write failures raise `AUDIT_CREATE_FAILED`

