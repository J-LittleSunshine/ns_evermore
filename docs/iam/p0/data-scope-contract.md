# Data Scope Contract (P0-04)

## 1. Purpose

This contract standardizes IAM data-scope outputs while preserving backward compatibility with legacy values.

## 2. Canonical Scope Values

- `SELF`
- `DEPARTMENT`
- `DEPARTMENT_AND_CHILDREN`
- `ORGANIZATION`
- `ALL`

Current implementation also keeps `SUBSIDIARY` for existing enterprise granularity.

## 3. Compatibility Mapping

- `DEPARTMENT_TREE` -> `DEPARTMENT_AND_CHILDREN`
- `COMPANY` -> `ORGANIZATION`

## 4. API Output Contract

`POST /iam/auth/data-scopes` keeps existing `scope` and adds canonical `normalized_scope`.

Example item:

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

## 5. Consumer Requirement

Business services must consume IAM filter plans and normalized scopes instead of inferring access scope from local enums.

