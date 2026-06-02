# IAM API Permission Matrix (P0-02)

## 1. Boundary Rules

- Anonymous allowed only for login and refresh endpoints.
- All other IAM endpoints require authentication and explicit `required_permissions`.

## 2. Route Matrix

| Path | Method | View Action | Auth Boundary | Required Permission |
| --- | --- | --- | --- | --- |
| `/iam/company/list` | POST | `list_item` | Authenticated | `iam:company:list` |
| `/iam/company/detail` | POST | `detail_item` | Authenticated | `iam:company:detail` |
| `/iam/company/create` | POST | `create_item` | Authenticated | `iam:company:create` |
| `/iam/company/update` | POST | `update_item` | Authenticated | `iam:company:update` |
| `/iam/company/delete` | POST | `delete_item` | Authenticated | `iam:company:delete` |
| `/iam/subsidiary/list` | POST | `list_item` | Authenticated | `iam:subsidiary:list` |
| `/iam/subsidiary/detail` | POST | `detail_item` | Authenticated | `iam:subsidiary:detail` |
| `/iam/subsidiary/create` | POST | `create_item` | Authenticated | `iam:subsidiary:create` |
| `/iam/subsidiary/update` | POST | `update_item` | Authenticated | `iam:subsidiary:update` |
| `/iam/subsidiary/delete` | POST | `delete_item` | Authenticated | `iam:subsidiary:delete` |
| `/iam/department/list` | POST | `list_item` | Authenticated | `iam:department:list` |
| `/iam/department/detail` | POST | `detail_item` | Authenticated | `iam:department:detail` |
| `/iam/department/create` | POST | `create_item` | Authenticated | `iam:department:create` |
| `/iam/department/update` | POST | `update_item` | Authenticated | `iam:department:update` |
| `/iam/department/delete` | POST | `delete_item` | Authenticated | `iam:department:delete` |
| `/iam/permission/list` | POST | `list_item` | Authenticated | `iam:permission:list` |
| `/iam/permission/detail` | POST | `detail_item` | Authenticated | `iam:permission:detail` |
| `/iam/permission/create` | POST | `create_item` | Authenticated | `iam:permission:create` |
| `/iam/permission/update` | POST | `update_item` | Authenticated | `iam:permission:update` |
| `/iam/permission/delete` | POST | `delete_item` | Authenticated | `iam:permission:delete` |
| `/iam/role/list` | POST | `list_item` | Authenticated | `iam:role:list` |
| `/iam/role/detail` | POST | `detail_item` | Authenticated | `iam:role:detail` |
| `/iam/role/create` | POST | `create_item` | Authenticated | `iam:role:create` |
| `/iam/role/update` | POST | `update_item` | Authenticated | `iam:role:update` |
| `/iam/role/delete` | POST | `delete_item` | Authenticated | `iam:role:delete` |
| `/iam/user/list` | POST | `list_item` | Authenticated | `iam:user:list` |
| `/iam/user/detail` | POST | `detail_item` | Authenticated | `iam:user:detail` |
| `/iam/user/create` | POST | `create_item` | Authenticated | `iam:user:create` |
| `/iam/user/update` | POST | `update_item` | Authenticated | `iam:user:update` |
| `/iam/user/delete` | POST | `delete_item` | Authenticated | `iam:user:delete` |
| `/iam/user/reset-password` | POST | `reset_password` | Authenticated | `iam:user:reset_password` |
| `/iam/auth/login` | POST | `login` | Anonymous | None |
| `/iam/auth/refresh` | POST | `refresh` | Anonymous | None |
| `/iam/auth/refresh-token` | POST | `refresh_token` | Anonymous | None |
| `/iam/auth/logout` | POST | `logout` | Authenticated | `iam:auth:logout` |
| `/iam/auth/profile` | POST | `profile` | Authenticated | `iam:auth:profile` |
| `/iam/auth/current-user` | POST | `current_user` | Authenticated | `iam:auth:current_user` |
| `/iam/auth/permissions` | POST | `permissions` | Authenticated | `iam:auth:permissions` |
| `/iam/auth/menus` | POST | `menus` | Authenticated | `iam:auth:menus` |
| `/iam/auth/data-scopes` | POST | `data_scopes` | Authenticated | `iam:auth:data_scopes` |
| `/iam/grant/user-role/bind` | POST | `bind_user_role` | Authenticated | `iam:grant:user_role:bind` |
| `/iam/grant/user-role/unbind` | POST | `unbind_user_role` | Authenticated | `iam:grant:user_role:unbind` |
| `/iam/grant/role-permission/grant` | POST | `grant_role_permission` | Authenticated | `iam:grant:role_permission:grant` |
| `/iam/grant/role-permission/revoke` | POST | `revoke_role_permission` | Authenticated | `iam:grant:role_permission:revoke` |
| `/iam/grant/user-permission/grant` | POST | `grant_user_permission` | Authenticated | `iam:grant:user_permission:grant` |
| `/iam/grant/user-permission/revoke` | POST | `revoke_user_permission` | Authenticated | `iam:grant:user_permission:revoke` |
| `/iam/grant/department-permission/grant` | POST | `grant_department_permission` | Authenticated | `iam:grant:department_permission:grant` |
| `/iam/grant/department-permission/revoke` | POST | `revoke_department_permission` | Authenticated | `iam:grant:department_permission:revoke` |
| `/iam/grant/subsidiary-permission/grant` | POST | `grant_subsidiary_permission` | Authenticated | `iam:grant:subsidiary_permission:grant` |
| `/iam/grant/subsidiary-permission/revoke` | POST | `revoke_subsidiary_permission` | Authenticated | `iam:grant:subsidiary_permission:revoke` |
| `/iam/session/list` | POST | `list_sessions` | Authenticated | `iam:session:list` |
| `/iam/session/revoke` | POST | `revoke_session` | Authenticated | `iam:session:revoke` |
| `/iam/resource/register` | POST | `register_resource` | Authenticated | `iam:resource:register` |
| `/iam/resource/action/register` | POST | `register_resource_action` | Authenticated | `iam:resource:action:register` |
| `/iam/resource/list` | POST | `list_resources` | Authenticated | `iam:resource:list` |
| `/iam/acl/grant` | POST | `grant_acl` | Authenticated | `iam:acl:grant` |
| `/iam/acl/revoke` | POST | `revoke_acl` | Authenticated | `iam:acl:revoke` |
| `/iam/acl/list` | POST | `list_acl` | Authenticated | `iam:acl:list` |
| `/iam/authorize/check` | POST | `check` | Authenticated | `iam:authorize:check` |
| `/iam/authorize/batch-check` | POST | `batch_check` | Authenticated | `iam:authorize:batch_check` |
| `/iam/policy/create` | POST | `create_policy` | Authenticated | `iam:policy:create` |
| `/iam/policy/update` | POST | `update_policy` | Authenticated | `iam:policy:update` |
| `/iam/policy/publish` | POST | `publish_policy` | Authenticated | `iam:policy:publish` |
| `/iam/policy/disable` | POST | `disable_policy` | Authenticated | `iam:policy:disable` |
| `/iam/policy/rule/add` | POST | `add_rule` | Authenticated | `iam:policy:rule:add` |
| `/iam/policy/rule/remove` | POST | `remove_rule` | Authenticated | `iam:policy:rule:remove` |
| `/iam/policy/rule/list` | POST | `list_rules` | Authenticated | `iam:policy:rule:list` |
| `/iam/audit/decision/list` | POST | `list_decision_audits` | Authenticated | `iam:audit:decision:list` |

