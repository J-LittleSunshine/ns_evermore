# L3 Integration: Module Onboarding

## 1. Goal

Allow enterprise self-built applications to integrate IAM without modifying IAM core flow.

## 2. Minimum Integration Steps

1. Register resource type and action codes.
2. Define permission codes using IAM format.
3. Configure RBAC/ACL/Policy according to business model.
4. Enforce IAM check at application entry point.
5. Consume returned IAM `filters` in data queries.
6. Keep trace id propagation for audit correlation.

## 3. Recommended Integration Pattern

Preferred for external applications:

- call IAM APIs over HTTP (`/iam/authorize/check` and `/iam/authorize/batch-check`)

Optional for same-repo modules:

- call `AuthorizeService` and integration facades directly

Standardized same-repo entrypoint:

- inherit `AuthenticatedRequestViewSet` from `src/ns_backend/backend/common/viewset.py`
- configure `verify_service`, `authorize_service`, `authorize_resource_type`, and `required_permissions` in module viewsets

## 4. External Application Contract

Per decision request, provide:

- `resource_type`
- `resource_id`
- `action_code`
- `permission_code` (recommended)
- `context` (optional)

## 5. Non-Bypass Rule

Business applications should expose one authorization gateway in their own framework.

Do not allow direct retriever/tool/data-access execution that bypasses IAM checks.

