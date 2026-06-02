# L2 Capability: Data Scope Contract

## 1. Canonical Scope Values

- SELF
- DEPARTMENT
- DEPARTMENT_AND_CHILDREN
- ORGANIZATION
- ALL

Current implementation also keeps `SUBSIDIARY` for existing enterprise granularity.

## 2. Compatibility Mapping

- DEPARTMENT_TREE -> DEPARTMENT_AND_CHILDREN
- COMPANY -> ORGANIZATION

## 3. API Contract

`POST /iam/auth/data-scopes` keeps raw `scope` and returns canonical `normalized_scope`.

Example:

```json
{
  "permission_code": "iam:department:list",
  "allowed": true,
  "scope": "DEPARTMENT_TREE",
  "normalized_scope": "DEPARTMENT_AND_CHILDREN",
  "company_id": 1,
  "subsidiary_id": 10,
  "department_id": 100,
  "department_ids": [100, 101, 102],
  "user_id": 2001,
  "is_platform_scope": false
}
```

## 4. Business Consumer Rule

Business modules must consume IAM `filters` output from authorize decisions.

Do not infer data scope from local enums or local role assumptions.

