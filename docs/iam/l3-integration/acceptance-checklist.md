# L3 Integration: Acceptance Checklist

## 1. Global Gate Checklist

1. Subject/Resource/Action/Effect model is available end-to-end.
2. deny precedence is consistent across ACL, Policy, and RBAC.
3. IAM `filters` is consumed by business query layer.
4. Knowledge authorization filtering runs before retriever recall.
5. Agent tool authorization runs before tool execution.
6. Decision audit can trace denied requests to policy-rule level.
7. New module onboarding requires resource/action registration and policy config only.

## 2. Ready for Integration Checklist

Use this before business framework integration starts:

- [x] Resource registration APIs are available.
- [x] ACL APIs are available.
- [x] Policy APIs are available.
- [x] Unified authorize APIs are available.
- [x] Decision audit query API is available.
- [x] Knowledge and Agent integration facades are available.

## 3. Final Acceptance Checklist

Use this after business framework integration is complete:

- [ ] At least one real Knowledge chain is connected and non-bypass verified.
- [ ] At least one real Agent tool dispatcher is connected and non-bypass verified.
- [ ] IAM filters are enforced in real business data access.
- [ ] Decision audit coverage and traceability are validated in production-like traffic.
- [ ] Performance baseline target is measured and archived.

