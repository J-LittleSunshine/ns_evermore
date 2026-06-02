# L2 Capability: Resource ACL and Unified Authorize

## 1. Resource Registry

Purpose:

- Register module-independent resource types and action codes.

Core APIs:

- `POST /iam/resource/register`
- `POST /iam/resource/action/register`
- `POST /iam/resource/list`

## 2. Resource ACL

Purpose:

- Manage instance-level authorization rules.

Supported subjects:

- USER
- ROLE
- DEPARTMENT
- ORGANIZATION
- SUBSIDIARY

Core APIs:

- `POST /iam/acl/grant`
- `POST /iam/acl/revoke`
- `POST /iam/acl/list`

## 3. Unified Authorize Service

Core APIs:

- `POST /iam/authorize/check`
- `POST /iam/authorize/batch-check`

Current decision order:

1. superuser allow
2. ACL deny
3. Policy deny
4. ACL allow
5. Policy allow
6. RBAC allow
7. default deny

Rule guarantee:

- deny > allow

## 4. IAM View Layer Behavior

In IAM routes, `required_permissions` remains the route contract.

Decision path:

- route permission checks are evaluated by `AuthorizeService`
- no silent fallback to legacy RBAC path on authorize failure
- authorization failure is fail-close

## 5. Key Source Files

- `src/ns_backend/iam/services/resource_registry.py`
- `src/ns_backend/iam/services/resource_acl.py`
- `src/ns_backend/iam/services/authorize.py`
- `src/ns_backend/iam/__init__.py`
- `src/ns_backend/iam/views/__init__.py`

