# IAM P0 Smoke Checklist

## 1. Scope

This checklist is the minimum smoke gate before merging P0 changes.

## 2. Core Cases

1. Login succeeds with valid username/password payload.
2. Login fails with wrong password and returns auth error code.
3. Refresh succeeds with a valid refresh token.
4. Accessing `/iam/auth/profile` without token is denied.
5. Accessing `/iam/auth/profile` with token but without `iam:auth:profile` is denied.
6. Accessing `/iam/auth/profile` with granted permission succeeds.
7. `/iam/auth/logout` without token is denied.
8. `/iam/session/list` without `iam:session:list` is denied.
9. `/iam/session/list` with `iam:session:list` succeeds.
10. `/iam/session/revoke` with valid `session_id` succeeds.
11. `/iam/company/list` enforces `iam:company:list`.
12. `/iam/department/list` enforces `iam:department:list`.
13. `/iam/grant/user-permission/grant` succeeds with permission.
14. `/iam/grant/user-permission/revoke` succeeds with permission.
15. Data scope output includes both `scope` and `normalized_scope`.
16. `DEPARTMENT_TREE` is normalized to `DEPARTMENT_AND_CHILDREN`.
17. `COMPANY` is normalized to `ORGANIZATION`.
18. Permission sync fails when ACTION code format is invalid.
19. Permission sync fails when ACTION is not in whitelist.
20. Failed permission checks write audit `decision_reason`.
21. Failed permission checks write audit `matched_permission_code`.
22. Failed permission checks write audit `decision_source`.
23. Resource registration API can create `knowledge.document`.
24. Resource action registration can create `read/write/share` for one resource.
25. ACL grant and ACL revoke APIs are idempotent.
26. ACL deny overrides ACL allow for same subject-resource-action.
27. `authorize/check` returns complete decision contract fields.
28. `authorize/batch-check` returns per-item decisions.
29. Policy create/update/publish/disable lifecycle works.
30. Policy rule add/remove/list works with priority ordering.
31. Policy deny is effective in authorize decisions.
32. Decision audit API can query policy/rule matched results.

## 3. Exit Criteria

All checklist items must pass in the target environment and no critical regression is observed in IAM API responses.

