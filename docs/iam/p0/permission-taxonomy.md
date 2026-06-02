# IAM Permission Taxonomy (P0-01)

## 1. Goal

This document defines the baseline format for IAM permission codes and action naming.

## 2. Permission Code Format

- Format: `{module}:{resource}:{action}`
- `module`: lowercase domain code, such as `iam`, `knowledge`, `crm`
- `resource`: lowercase resource code (single or hierarchical), such as `user`, `grant:user_role`
- `action`: lowercase action code from whitelist

Examples:

- `iam:user:update`
- `iam:grant:user_role:bind`
- `knowledge:document:read`

## 3. Action Whitelist (ACTION type only)

Current allowed action codes:

- `add`
- `approve`
- `batch_check`
- `bind`
- `check`
- `create`
- `current_user`
- `data_scopes`
- `delete`
- `detail`
- `disable`
- `execute`
- `grant`
- `list`
- `login`
- `logout`
- `manage`
- `menus`
- `permissions`
- `profile`
- `publish`
- `read`
- `refresh`
- `register`
- `remove`
- `reset_password`
- `revoke`
- `share`
- `sync`
- `unbind`
- `update`
- `update_staff`
- `update_superuser`
- `write`

Validation behavior:

- ACTION permissions with invalid format fail with `PERMISSION_CODE_FORMAT_INVALID`.
- ACTION permissions with unsupported action fail with `PERMISSION_ACTION_INVALID`.

## 4. Builtin Cross-Module Action Examples

Builtin provider includes disabled examples for taxonomy alignment:

- `example:platform_resource:read`
- `example:platform_resource:write`
- `example:platform_resource:delete`
- `example:platform_resource:manage`
- `example:platform_resource:execute`
- `example:platform_resource:approve`
- `example:platform_resource:share`

These examples are governance references and are created with `status=0`.

